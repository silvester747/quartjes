"""
Implementation of the Quartjes protocol in Twisted.

Contents of this file are not to be used directly. Use either the 
:class:`ServerConnector <quartjes.connector.server.ServerConnector>`
in :mod:`quartjes.connector.server` or the 
:class:`ClientConnector <quartjes.connector.client.ClientConnector>` in 
:mod:`quartjes.connector.client`.

The protocol implementation in Twisted is asynchronous. The methods in this file
translate between the asynchronous calls in the reactor thread and synchronous
or blocking calls from other threads. Methods designed to run in the reactor
thread are prefixed with "r_". Do not call these method from any other thread.
"""

__author__ = "Rob van der Most"
__docformat__ = "restructuredtext en"

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor, threads, defer
from twisted.protocols.basic import NetstringReceiver
import uuid
from quartjes.connector.messages import MethodCallMessage, ResponseMessage, SubscribeMessage
from quartjes.connector.messages import ServerMotdMessage, create_message_string, parse_message_string
from quartjes.connector.messages import EventMessage
from quartjes.connector.exceptions import MessageHandleError, ConnectionError, TimeoutError
from quartjes.connector.services import execute_remote_method_call, prepare_remote_service, subscribe_to_remote_event

class QuartjesProtocol(NetstringReceiver):
    """
    Protocol implementation for the Quartjes application. For now we are using a basic
    Netstring receiver to listen for xml messages encoded as netstrings.
    
    No need to make instances of this class yourself. It is set as the protocol
    in the server and client factories.
    """

    def __init__(self):
        """
        Construct a new protocol handler with a unique id.
        """
        self.id = uuid.uuid4()
        self.MAX_LENGTH = 999999999999

    def connectionMade(self):
        """
        Fired by twisted when the connection is established.
        """
        self.factory._r_on_connection_established(self)

    def stringReceived(self, string):
        """
        Fired by twisted when a complete netstring is received.
        """
        self.factory._r_on_incoming_message(string, self)

    def connectionLost(self, reason):
        """
        Fired by twisted when the connection is lost.
        """
        self.factory._r_on_connection_lost(self)

    def send_message(self, serial_message):
        """
        Send the XML message to the other end of this connection.
        """
        #print("Sending message: %s" % serial_message)
        self.sendString(serial_message)


class QuartjesServerFactory(ServerFactory):
    """
    Protocol factory to handle incoming connections for the Quartjes server.
    
    Methods
    -------
    register_service
    unregister_service
    send_event
    
    Notes
    -----
    
    Handling of incoming messages
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    When a message is received from the client, it is handled in the
    twisted defered way. It contains multiple steps, some within the reactor
    thread and some in a separate thread. It is important to do most of the
    processing outside the reactor thread. As long as processing is inside
    the reactor thread, no other incoming messages can be handled.
    
    Currently the following steps are performed. Communication between steps
    is in the form of a :class:`MessageResult` object.
    
    * :meth:`_parse_message`: Deserialise the message in a separate thread
      and perform any actions that do not need to run inside the reactor
      thread;
    * :meth:`_r_process_message`: Do any processing of the message inside
      the reactor thread;
    * :meth:`_r_send_result`: Send the result back to the client.
    
    If an exception occurs, any following step will be skipped and the error
    message is directly sent back using :meth:`_r_send_error`.
    """

    protocol = QuartjesProtocol
    """
    The protocol class variable is used by twisted to determine the protocol
    to use for this factory.
    """

    def __init__(self):
        """
        Initialize the factory.
        """
        self._connections = {}
        self._services = {}

    def register_service(self, service, name):
        """
        Register a service with the factory.
        After registering the service, it can be remotely accessed through the given name.
        
        Parameters
        ----------
        service : object decorated by :func:`remote_service <quartjes.connector.services.remote_service>`
            Service object to register with the factory. After registering it 
            will be available for remote clients.
        name : string
            Name the service is registered under. Clients must use this name to
            access the service.
        """
        assert service._remote_service, "Services should be decorated correctly."
        
        prepare_remote_service(service)
        self._services[name] = service

    def unregister_service(self, name):
        """
        Unregister a service from the factory. It is no longer accessible by
        remote clients.
        
        Parameters
        ----------
        name : string
            Name the service is currently registered under.
        """
        self._services.remove(name)

    def _r_on_connection_established(self, protocol):
        """
        Handle an incoming connection.
        
        Parameters
        ----------
        protocol
            Twisted protocol object connected to the client.
        """
        self._connections[protocol.id] = protocol
        motd = ServerMotdMessage(client_id=protocol.id)
        protocol.send_message(create_message_string(motd))

    def _r_on_connection_lost(self, protocol):
        """
        Handle a lost connection.
        
        Parameters
        ----------
        protocol
            Twisted protocol object connected to the client.
        """
        del self._connections[protocol.id]

    def _r_on_incoming_message(self, string, protocol):
        """
        Handle incoming messages. Most of the work is offloaded to a separate
        thread.
        
        Parameters
        ----------
        string : string
            Incoming message string to handle.
        protocol
            Twisted protocol object connected to the client.
        """
        #print("Incoming: %s" % string)
        d = threads.deferToThread(self._parse_message, string, protocol)
        d.addCallback(self._r_process_message, protocol)
        d.addCallbacks(callback=self._r_send_result, errback=self._r_send_error, callbackArgs=(protocol,), errbackArgs=(protocol,))

    def _parse_message(self, string, protocol):
        """
        Parse the contents of a message. Also do processing outside the reactor
        thread.

        This method should run in a separate thread to prevent blocking the reactor.

        Both the parsed original message and a possible return message are returned
        in a special MessageResult instance.
        
        Parameters
        ----------
        string : string
            Incoming message string to handle.
        protocol
            Twisted protocol object connected to the client.
            
        Returns
        -------
        result : :class:`MessageResult`
            Result of parsing the message.
        
        Raises
        ------
        MessageHandleError
            If any error occurs while handling the message.
        """
        #print("Parsing message: %s" % string)
        msg = parse_message_string(string)
        result = MessageResult(original_message=msg)

        if isinstance(msg, MethodCallMessage):
            # Handle method call
            res = self._method_call(msg)
            response_msg = ResponseMessage(result_code=0, result=res, response_to=msg.id)
            result.response = create_message_string(response_msg)
        elif isinstance(msg, SubscribeMessage):
            # Handle subscription to event
            response_msg = ResponseMessage(result_code=0, result=None, response_to=msg.id)
            result.response = create_message_string(response_msg)
        else:
            raise MessageHandleError(MessageHandleError.RESULT_UNEXPECTED_MESSAGE, msg)

        return result

    def _r_process_message(self, result, protocol):
        """
        Perform processing required inside the reactor thread. Expects the
        original message to be already parsed. Possibly a return message
        is already present from actions processed outside the reactor.

        Returns the message to be send back to the client.
        
        Parameters
        ----------
        result : :class:`MessageResult`
            Result from previous handling of the message.
        protocol
            Twisted protocol object connected to the client.
            
        Returns
        -------
        response : string
            Serialized message to return to the client.
        
        Raises
        ------
        MessageHandleError
            If any error occurs while handling the message.
        """
        if isinstance(result.original_message, SubscribeMessage):
            self._r_subscribe_to_event(result.original_message.service_name,
                result.original_message.event_name, protocol)
        
        return result.response

    def _method_call(self, msg):
        """
        Handle an MethodCall message by calling the requested method on the
        requested service.
        
        Parameters
        ----------
        msg : :class:`quartjes.connector.messages.MethodCallMessage`
            Message containg the method call to perform.
            
        Returns
        -------
        result
            Whatever the method call returns.
            
        Raises
        ------
        MessageHandleError
            If any error occurs while handling the message.
        """
        #print("Performing service: %s, method_name: %s" % (msg.service_name, msg.method_name))
        service = self._services.get(msg.service_name)
        if service == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_SERVICE, msg)

        try:
            return execute_remote_method_call(service, msg.method_name, *msg.pargs, **msg.kwargs)
            #return service.call(msg.method_name, *msg.pargs, **msg.kwargs)
        except MessageHandleError as error:
            error.original_message = msg
            raise error

    def _r_subscribe_to_event(self, service_name, event_name, protocol):
        """
        Subscribe the client to an event on the specified service.
        
        Parameters
        ----------
        service_name : string
            Name of the service containing the event.
        event_name : string
            Name of the event to subscribe to.
        protocol
            Twisted protocol object connected to the client that should receive
            event notifications.
            
        Raises
        ------
        MessageHandleError
            If any error occurs while handling the message.
        """
        service = self._services.get(service_name)
        if service == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_SERVICE)
        
        subscribe_to_remote_event(service, service_name, event_name, protocol, self)

    def _r_send_result(self, response, protocol):
        """
        Send the result back to the client.
        Response is expected to be a string ready to send.
        
        Parameters
        ----------
        response : string
            Message ready to be sent to the client.
        protocol
            Twisted protocol object connected to the client that should receive
            event notifications.
        """
        #print("Send result: %s" % result)
        protocol.send_message(response)

    def _r_send_error(self, result, protocol):
        """
        Send an exception to the client.
        This is the only method that creates XML inside the reactor thread. This
        might cause problems if the error contains a lot of data, but for now we
        do not expect this to be the case.
        
        Parameters
        ----------
        result
            Result from twisted encapsulating an exception.
        protocol
            Twisted protocol object connected to the client that should receive
            event notifications.
        
        Raises
        ------
        Exception
            If the exception received is not of type 
            :class:`quartjes.connector.exceptions.MessageHandleError` we reraise the
            exception instead of sending it to the client.
        """
        error = result.value
        if not isinstance(error, MessageHandleError):
            raise error
        print("Error occurred: %s" % result)
        msgid = None
        if error.original_message != None:
            msgid = error.original_message.id
        msg = ResponseMessage(result_code=error.error_code, response_to=msgid, result=error.error_details)
        protocol.send_message(create_message_string(msg))

    def send_event(self, service_name, event_name, listener, *pargs, **kwargs):
        """
        Notify a client of an event.
        
        Parameters
        ----------
        service_name : string
            Name of the service firing the event.
        event_name : string
            Name of the event being fired.
        listener
            Twisted protocol object connected to the client that should receive
            event notifications.
        *pargs
            Any additional positional arguments will be sent as positional
            arguments to the client callback.
        **kwargs
            Any additional keyword arguments will be sent as keyword
            arguments to the client callback.
            
        """
        msg = EventMessage(service_name, event_name, pargs, kwargs)
        string = create_message_string(msg)
        reactor.callFromThread(listener.send_message, string) #@UndefinedVariable
        

class QuartjesClientFactory(ReconnectingClientFactory):
    """
    Client factory for quartjes client. Implements the reconnecting client factory
    to make sure it reconnects in case of errors.
    
    Parameters
    ----------
    timeout : int
        Timeout in seconds for messages. If no response is received within this time
        an exception will be returned.
        
    Notes
    -----
    When connected this class keeps a reference to the protocol currently 
    connected to the server. If no connection is present, the reference
    should be None.
    
    Blocking method calls are performed by using the blockingCallFromThread
    functionality in Twisted. The method sending the message returns a
    defered object which is saved in a dictionary with the message id. Once
    a response is received the defered is triggered with the server response.
    That moment the blockingCallFromThread method will unblock and return
    the result.
    
    For timeouts a special defered is created. A call is scheduled in the
    reactor to return a :class:`TimeoutError <quartjes.connector.exceptions.TimeoutError>`
    to the deferred after the timeout has expired. In the defered a callback
    is added that will make sure the timeout call is cancelled when a response
    is received.
    
    Attributes
    ----------
    timeout
    
    Methods
    -------
    is_connected
    send_message_blocking
    send_method_call
    subscribe
    wait_for_connection
    
    """

    protocol = QuartjesProtocol
    """
    The protocol class variable is used by twisted to determine the protocol
    to use for this factory.
    """

    def __init__(self, timeout=5):
        """
        Initialize the client factory.
        """
        self._waiting_messages = {}
        self._waiting_for_connection = []
        self._current_protocol = None
        self._event_callbacks = {}
        self._timeout = timeout

    @property
    def timeout(self):
        """
        Timeout in seconds for messages. If no response is received within this time
        an exception will be returned.
        """
        return self._timeout
    
    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    def _r_on_connection_established(self, protocol):
        """
        Handle a newly established connection to the server. Called by the 
        :class:`QuartjesProtocol`.
        
        If any methods are waiting for a connection, they will be notified.

        Parameters
        ----------
        protocol
            Twisted protocol object connected to the server.
        """
        print("Client connected")
        self._current_protocol = protocol

        for d in self._waiting_for_connection:
            d.callback(True)
        self._waiting_for_connection = []

    def _r_on_connection_lost(self, protocol):
        """
        Handle a lost connection.Called by the :class:`QuartjesProtocol`.
        
        All callbacks waiting for a message response are notified that a
        connection error has occurred.

        Parameters
        ----------
        protocol
            Twisted protocol object connected to the server.
        """
        print("Client disconnected")
        self._current_protocol = None

        for cb in self._waiting_messages.values():
            cb.errback(ConnectionError("Connection lost."))
        self._waiting_messages.clear()

    def _r_on_incoming_message(self, string, protocol):
        """
        Handle incoming messages. Defers parsing the message to another thread, so the
        reactor is not blocked. Called by the :class:`QuartjesProtocol`.

        Parameters
        ----------
        string : string
            Text received from the server.
        protocol
            Twisted protocol object connected to the server.
        """
        #print("Incoming: %s" % string)
        d = threads.deferToThread(parse_message_string, string)
        d.addCallback(self._r_handle_message_contents, protocol)

    def _r_handle_message_contents(self, msg, protocol):
        """
        After parsing a message handle it in the reactor loop.
        
        Parameters
        ----------
        msg : :class:`quartjes.connector.messages.Message`
            Message object to handle.
        protocol
            Twisted protocol object connected to the server.
        """
        if isinstance(msg, ResponseMessage):
            d = self._waiting_messages.pop(msg.response_to, None)
            if d != None:
                d.callback(msg)
        elif isinstance(msg, ServerMotdMessage):
            print("Connected: %s" % msg.motd)
            self._r_successful_connection()
        elif isinstance(msg, EventMessage):
            callback = self._event_callbacks.get((msg.service_name, msg.event_name))
            if callback != None:
                threads.deferToThread(callback, *msg.pargs, **msg.kwargs)
            
    def _r_successful_connection(self):
        """
        Handle a succesful connection. Resets the reconnect backoff and makes
        sure all events that were already subscribed to are active again.
        """
        self.resetDelay()
        for (service_name, event_name) in self._event_callbacks.keys():
            msg = SubscribeMessage(service_name=service_name, event_name=event_name)
            serial_message = create_message_string(msg)
            self._current_protocol.send_message(serial_message)

    def send_message_blocking(self, message):
        """
        Call from another thread to send a message to the server and wait for the result.
        Accepts a serializable message.
        Based on the response either the result is returned or an exception is raised.

        Parameters
        ----------
        message : :class:`quartjes.connector.messages.Message`
            Message object to send to the server.
        
        Returns
        -------
        result
            The response returned by the server.
            
        Raises
        ------
        MessageHandleError
            Something went wrong while handling the message on the server.
        ConnectionError
            There is an issue with the connection to the server.
        TimeoutError
            No response was received within the set timeout.
        """
        serial_message = create_message_string(message)
        try:
            result_msg = threads.blockingCallFromThread(reactor, self._r_send_message_and_wait, message.id, serial_message)
            if result_msg.result_code > 0:
                raise MessageHandleError(error_code=result_msg.result_code, error_details = result_msg.result)
            return result_msg.result
        except TimeoutError:
            self._waiting_messages.pop(message.id, None)
            raise

    def _r_send_message_and_wait(self, message_id, serial_message):
        """
        Send a message to the server and return a Deferred which is called back
        when a response has been received.
        Accepts a string containing an already serialized message.
        
        Parameters
        ----------
        message_id : UUID
            Unique id of the message.
        serial_message : string
            Serialised message to send.
            
        Returns
        -------
        deferred
            Deferred object that is triggered when a response is received or a
            timeout occurs.
        """
        if self._current_protocol == None:
            raise ConnectionError("Not connected.")
        d = self._r_create_timeout_deferred()
        self._waiting_messages[message_id] = d
        self._current_protocol.send_message(serial_message)
        return d

    def send_method_call(self, service_name, method_name, *pargs, **kwargs):
        """
        Call from another thread to request a method call to be performed at the server
        and wait for the result.

        Parameters
        ----------
        service_name : string
            Name of the service containing the method.
        method_name : string
            Name of the method to call.
        *pargs
            Positional arguments to supply to the method.
        **kwargs
            Keyword arguments to supply to the method.
            
        Raises
        ------
        MessageHandleError
            Something went wrong while handling the message on the server.
        ConnectionError
            There is an issue with the connection to the server.
        TimeoutError
            No response was received within the set timeout.
        """
        msg = MethodCallMessage(service_name=service_name, method_name=method_name, pargs=pargs, kwargs=kwargs)
        return self.send_message_blocking(msg)

    def subscribe(self, service_name, event_name, callback):
        """
        Call from another thread to subscribe to an event on a specific service.
        The given callback is called each time an update for the event is received.
        Returns nothing, but an exception can be raised.

        Parameters
        ----------
        service_name : string
            Name of the service containing the event.
        method_name : string
            Name of the event to subscribe to.
        callback
            Method to call when an event notification is received.

        Raises
        ------
        MessageHandleError
            Something went wrong while handling the message on the server.
        ConnectionError
            There is an issue with the connection to the server.
        TimeoutError
            No response was received within the set timeout.
        """
        msg = SubscribeMessage(service_name=service_name, event_name=event_name)
        self.send_message_blocking(msg)

        # if subscribe failed an exception should be raised by now
        self._event_callbacks[(service_name, event_name)] = callback

    def wait_for_connection(self, timeout=None):
        """
        Wait for the connection to be established.
        Provide a timeout value to control the time waited for a connection. If no
        timeout value is provided, the default value is used.

        Parameters
        ----------
        timeout : int
            Time in seconds to wait for a connection to be established. If not
            given, the default will be used.

        Raises
        ------
        TimeoutError
            No connection was established within the timeout.
        """
        return threads.blockingCallFromThread(reactor, self._r_wait_for_connection, timeout)

    def _r_wait_for_connection(self, timeout=None):
        """
        Wait for the connection to be established. First checks if we are already
        connected. Else it will wait for an established connection.

        Internal version. Only to be called from the reactor thread.
        
        Parameters
        ----------
        timeout : int
            Time in seconds to wait for a connection to be established. If not
            given, the default will be used.

        Returns
        -------
        True if already connected, else a Deferred that will be called when a
        connection is established.
        """
        if self.is_connected():
            return True

        d = self._r_create_timeout_deferred(timeout)
        self._waiting_for_connection.append(d)

        return d

    def _r_create_timeout_deferred(self, timeout=None):
        """
        Construct a deferred which will return an exception if the callback is
        not triggered within the timeout.
        
        Parameters
        ----------
        timeout : int
            Time in seconds to wait before generating an error.
            
        Returns
        -------
        A deferred object that will return an error if the timeout expires.
        """
        if not timeout:
            timeout = self._timeout
            
        d = defer.Deferred()
        timeout_call = reactor.callLater(timeout, d.errback, TimeoutError()) #@UndefinedVariable

        def cb(result, timeout_call):
            timeout_call.cancel()
            return result

        d.addCallback(cb, timeout_call)
        return d

    def is_connected(self):
        """
        Is the client connected to the server?
        
        Returns
        -------
        True if currently connected, False if not.
        """
        return self._current_protocol != None


class MessageResult(object):
    """
    Intermediate result of an incoming message in the server protocol.
    Contains both the original message and optionally the result to sent back
    to the client.
    
    Parameters
    ----------
    response : string
        Serialised response to the message.
    original_message: :class:`quartjes.connector.messages.Message`
        Original message this is a result from.
    
    Attributes
    ----------
    response : string
        Serialised response to the message.
    original_message : :class:`Message <quartjes.connector.messages.Message>`
        Original message this is a result from.
    
    """
    def __init__(self, response=None, original_message=None):
        self.response = response
        self.original_message = original_message

