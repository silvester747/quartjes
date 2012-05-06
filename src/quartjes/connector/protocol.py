"""
Implementation of the Quartjes protocol in Twisted.

Contents of this file are not to be used directly. Use either the ServerConnector
in quartjes.connector.server or the ClientConnector in quartjes.connector.client.

The protocol implementation in Twisted is asynchronous. The methods in this file
translate between the asynchronous calls in the reactor thread and synchronous
or blocking calls from other threads. Methods designed to run in the reactor
thread are prefixed with "r_". Do not call these method from any other thread.
"""

__author__ = "Rob van der Most"

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
    """

    protocol = QuartjesProtocol

    def __init__(self):
        """
        Initialize the factory.
        """
        self.connections = {}
        self.services = {}

    def register_service(self, service, name):
        """
        Register a service with the factory.
        After registering the service, it can be remotely accessed through the given name.
        """
        assert service._remote_service, "Services should be decorated correctly."
        
        prepare_remote_service(service)
        self.services[name] = service

    def unregister_service(self, name):
        """
        Unregister a service from the factory.
        """
        self.services.remove(name)

    def _r_on_connection_established(self, protocol):
        """
        Handle an incoming connection.
        """
        self.connections[protocol.id] = protocol
        motd = ServerMotdMessage(client_id=protocol.id)
        protocol.send_message(create_message_string(motd))

    def _r_on_connection_lost(self, protocol):
        """
        Handle a lost connection.
        """
        del self.connections[protocol.id]

    def _r_on_incoming_message(self, string, protocol):
        """
        Handle incoming messages. Most of the work is offloaded to a separate
        thread.
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
        """
        if isinstance(result.original_message, SubscribeMessage):
            self._r_subscribe_to_event(result.original_message.service_name,
                result.original_message.event_name, protocol)
        
        return result.response

    def _method_call(self, msg):
        """
        Handle an MethodCall message by calling the requested method on the
        requested service.
        """
        #print("Performing service: %s, method_name: %s" % (msg.service_name, msg.method_name))
        service = self.services.get(msg.service_name)
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
        """
        service = self.services.get(service_name)
        if service == None:
            return
        
        subscribe_to_remote_event(service, service_name, event_name, protocol, self)

    def _r_send_result(self, response, protocol):
        """
        Send the result back to the client.
        Response is expected to be a string ready to send.
        """
        #print("Send result: %s" % result)
        protocol.send_message(response)

    def _r_send_error(self, result, protocol):
        """
        Send an exception to the client.
        This is the only method that creates XML inside the reactor thread. This
        might cause problems if the error contains a lot of data, but for now we
        do not expect this to be the case.
        """
        error = result.value
        if not isinstance(error, MessageHandleError):
            raise error
        print("Error occurred: %s" % result)
        id = None
        if error.original_message != None:
            id = error.original_message.id
        msg = ResponseMessage(result_code=error.error_code, response_to=id, result=error.error_details)
        protocol.send_message(create_message_string(msg))

    def send_event(self, service_name, event_name, listener, *pargs, **kwargs):
        """
        Notify a client of an event.
        """
        msg = EventMessage(service_name, event_name, pargs, kwargs)
        string = create_message_string(msg)
        reactor.callFromThread(listener.send_message, string)
        

class QuartjesClientFactory(ReconnectingClientFactory):
    """
    Client factory for quartjes client. Implements the reconnecting client factory
    to make sure it reconnects in case of errors.
    """
    protocol = QuartjesProtocol
    default_timeout = 5

    def __init__(self, timeout=default_timeout):
        """
        Initialize the client factory.
        """
        self.waiting_messages = {}
        self.waiting_for_connection = []
        self.current_protocol = None
        self.event_callbacks = {}
        self.timeout = timeout

    def _r_on_connection_established(self, protocol):
        """
        Handle a newly established connection to the server.
        """
        print("Client connected")
        self.current_protocol = protocol

        for d in self.waiting_for_connection:
            d.callback(True)
        self.waiting_for_connection = []

    def _r_on_connection_lost(self, protocol):
        """
        Handle a lost connection.
        All callbacks waiting for a message response are notified that a
        connection error has occurred.
        """
        print("Client disconnected")
        self.current_protocol = None

        for cb in self.waiting_messages.values():
            cb.errback(ConnectionError("Connection lost."))
        self.waiting_messages.clear()

    def _r_on_incoming_message(self, string, protocol):
        """
        Handle incoming messages. Defers parsing the message to another thread, so the
        reactor is not blocked.
        """
        #print("Incoming: %s" % string)
        d = threads.deferToThread(parse_message_string, string)
        d.addCallback(self._r_handle_message_contents, protocol)

    def _r_handle_message_contents(self, msg, protocol):
        """
        After parsing a message handle it in the reactor loop.
        """
        if isinstance(msg, ResponseMessage):
            d = self.waiting_messages.pop(msg.response_to, None)
            if d != None:
                d.callback(msg)
        elif isinstance(msg, ServerMotdMessage):
            print("Connected: %s" % msg.motd)
            self._r_successful_connection()
        elif isinstance(msg, EventMessage):
            callback = self.event_callbacks.get((msg.service_name, msg.event_name))
            if callback != None:
                threads.deferToThread(callback, *msg.pargs, **msg.kwargs)
            
    def _r_successful_connection(self):
        self.resetDelay()
        for (service_name, event_name) in self.event_callbacks.keys():
            msg = SubscribeMessage(service_name=service_name, event_name=event_name)
            serial_message = create_message_string(msg)
            self.current_protocol.send_message(serial_message)

    def send_message_blocking(self, message):
        """
        Call from another thread to send a message to the server and wait for the result.
        Accepts a serializable message.
        Based on the response either the result is returned or an exception is raised.

        Can throw either a MessageHandleError or a ConnectionError
        """
        serial_message = create_message_string(message)
        result_msg = threads.blockingCallFromThread(reactor, self._r_send_message_and_wait, message.id, serial_message)
        if result_msg.result_code > 0:
            raise MessageHandleError(error_code=result_msg.result_code, error_details = result_msg.result)
        return result_msg.result

    def _r_send_message_and_wait(self, message_id, serial_message):
        """
        Send a message to the server and return a Deferred which is called back
        when a response has been received.
        Accepts a string containing an already serialized message.
        """
        if self.current_protocol == None:
            raise ConnectionError("Not connected.")
        d = defer.Deferred()
        self.waiting_messages[message_id] = d
        self.current_protocol.send_message(serial_message)
        return d

    def send_method_call(self, service_name, method_name, *pargs, **kwargs):
        """
        Call from another thread to request an method_name to be performed at the server
        and wait for the result.

        Can throw either a MessageHandleError or a ConnectionError
        """
        msg = MethodCallMessage(service_name=service_name, method_name=method_name, pargs=pargs, kwargs=kwargs)
        return self.send_message_blocking(msg)

    def subscribe(self, service_name, event_name, callback):
        """
        Call from another thread to subscribe to a event_name of a specific service.
        The given callback is called each time an update for the event_name is received.
        Returns None, but an exception can be raised.

        Can throw either a MessageHandleError or a ConnectionError
        """
        msg = SubscribeMessage(service_name=service_name, event_name=event_name)
        self.send_message_blocking(msg)

        # if subscribe failed an exception should be raised by now
        self.event_callbacks[(service_name, event_name)] = callback

        return None

    def wait_for_connection(self, timeout=None):
        """
        Wait for the connection to be established.
        Provide a timeout value to control the time waited for a connection. If no
        timeout value is provided, the default value is used.

        If a timeout occurs the TimeoutError is raised.
        """
        return threads.blockingCallFromThread(reactor, self._r_wait_for_connection, timeout)

    def _r_wait_for_connection(self, timeout=None):
        """
        Wait for the connection to be established.

        Internal version. Only to be called from the reactor thread.
        """
        if self.is_connected():
            return True

        d = self._r_create_timeout_deferred(timeout)
        self.waiting_for_connection.append(d)

        return d

    def _r_create_timeout_deferred(self, timeout=None):
        """
        Construct a deferred which will return an exception if the callback is
        not triggered within the timeout.
        """
        if not timeout:
            timeout = self.timeout
            
        d = defer.Deferred()
        timeout_call = reactor.callLater(timeout, d.errback, TimeoutError())

        def cb(result, timeout_call):
            timeout_call.cancel()
            return result

        d.addCallback(cb, timeout_call)
        return d

    def is_connected(self):
        return self.current_protocol != None


class MessageResult(object):
    """
    Intermediate result of an incoming message in the server protocol.
    Contains both the original message and optionally the result to sent back
    to the client.
    """
    def __init__(self, response=None, original_message=None):
        self.response = response
        self.original_message = original_message

