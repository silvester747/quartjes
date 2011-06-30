__author__="Rob van der Most"
__date__ ="$May 27, 2011 8:53:12 PM$"

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor, threads, defer
from twisted.protocols.basic import NetstringReceiver
from twisted.internet import threads
import uuid
from quartjes.connector.messages import ActionRequestMessage, ResponseMessage, SubscribeMessage
from quartjes.connector.messages import ServerMotdMessage, create_message_string, parse_message_string
from quartjes.connector.messages import TopicUpdateMessage

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

    def connectionMade(self):
        """
        Fired by twisted when the connection is established.
        """
        self.factory.connection_established(self)

    def stringReceived(self, string):
        """
        Fired by twisted when a complete netstring is received.
        """
        self.factory.handle_incoming_message(string, self)

    def connectionLost(self, reason):
        """
        Fired by twisted when the connection is lost.
        """
        self.factory.connection_lost(self)

    def send_message(self, serial_message):
        """
        Send the XML message to the other end of this connection.
        """
        print("Sending message: %s" % serial_message)
        self.sendString(serial_message)


class QuartjesServerFactory(ServerFactory):
    """
    Protocol factory to handle incoming connections for the Quartjes server.
    """

    protocol = QuartjesProtocol

    def __init__(self):
        self.connections = {}
        self.services = {}
        self.topic_listeners = {}
        self.topics_per_connection = {}

    def connection_established(self, protocol):
        self.connections[protocol.id] = protocol
        self.topics_per_connection[protocol.id] = []
        motd = ServerMotdMessage(client_id=protocol.id)
        protocol.send_message(create_message_string(motd))

    def connection_lost(self, protocol):
        del self.connections[protocol.id]

        topics = self.topics_per_connection[protocol.id]
        for topic in topics:
            self.topic_listeners[topic].remove(protocol)

    def register_service(self, service):
        self.services[service.name] = service
        service.factory = self

    def unregister_service(self, service):
        self.services.remove(service.name)
        service.factory = None

    def handle_incoming_message(self, string, protocol):
        #print("Incoming: %s" % string)
        d = threads.deferToThread(self.parse_message_in_thread, string, protocol)
        d.addCallback(self.process_message_in_reactor, protocol)
        d.addCallbacks(callback=self.send_result, errback=self.send_error, callbackArgs=(protocol,), errbackArgs=(protocol,))

    def parse_message_in_thread(self, string, protocol):
        #print("Parsing message: %s" % string)
        msg = parse_message_string(string)
        result = MessageResult(original_message=msg)

        if isinstance(msg, ActionRequestMessage):
            res = self.perform_action(msg)
            response_msg = ResponseMessage(result_code=0, result=res, response_to=msg.id)
            result.response = create_message_string(response_msg)
        elif isinstance(msg, SubscribeMessage):
            response_msg = ResponseMessage(result_code=0, result=None, response_to=msg.id)
            result.response = create_message_string(response_msg)
        else:
            raise MessageHandleError(MessageHandleError.RESULT_UNEXPECTED_MESSAGE, msg)

        return result

    def process_message_in_reactor(self, result, protocol):

        if isinstance(result.original_message, SubscribeMessage):
            self.subscribe_to_topic(result.original_message.service_name,
                result.original_message.topic, protocol)
        
        return result.response

    def perform_action(self, msg):
        #print("Performing service: %s, action: %s" % (msg.service_name, msg.action))
        service = self.services.get(msg.service_name)
        if service == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_SERVICE, msg)

        try:
            return service.call(msg.action, msg.params)
        except MessageHandleError as error:
            error.original_message = msg
            raise error

    def subscribe_to_topic(self, service_name, topic, protocol):
        listeners = self.topic_listeners.get((service_name, topic))
        if listeners == None:
            listeners = [protocol]
            self.topic_listeners[(service_name, topic)] = listeners
        else:
            listeners.append(protocol)
        self.topics_per_connection[protocol.id].append((service_name, topic))

    def send_result(self, response, protocol):
        #print("Send result: %s" % result)
        protocol.send_message(response)

    def send_error(self, result, protocol):
        error = result.value
        if not isinstance(error, MessageHandleError):
            raise error
        #print("Error occurred: %s" % result)
        id = None
        if error.original_message != None:
            id = error.original_message.id
        msg = ResponseMessage(result_code=error.error_code, response_to=id, result=error.error_details)
        protocol.send_message(create_message_string(msg))

    def send_topic_update_from_thread(self, service_name, topic, **kwargs):
        listeners = self.topic_listeners.get((service_name, topic))
        if listeners == None:
            return

        msg = TopicUpdateMessage(service_name, topic, kwargs)
        string = create_message_string(msg)
        reactor.callFromThread(self.multicast_message, listeners, string)

    def multicast_message(self, protocols, string):
        for protocol in protocols:
            protocol.send_message(string)



class QuartjesClientFactory(ReconnectingClientFactory):
    """
    Client factory for quartjes client. Implements the reconnecting client factory
    to make sure it reconnects in case of errors.
    """
    protocol = QuartjesProtocol

    def __init__(self):
        self.waiting_messages = {}
        self.current_protocol = None
        self.topic_callbacks = {}

    def connection_established(self, protocol):
        """
        Handle a newly established connection to the server.
        """
        print("Client connected")
        self.current_protocol = protocol


    def connection_lost(self, protocol):
        """
        Handle a lost connection.
        """
        print("Client disconnected")
        self.current_protocol = None

        for cb in self.waiting_messages.values():
            cb.errback(ConnectionError("Connection lost."))
        self.waiting_messages.clear()

    def handle_incoming_message(self, string, protocol):
        """
        Handle incoming messages. Defers parsing the message to another thread, so the
        reactor is not blocked.
        """
        #print("Incoming: %s" % string)
        d = threads.deferToThread(parse_message_string, string)
        d.addCallback(self.handle_message_contents, protocol)

    def handle_message_contents(self, msg, protocol):
        """
        After parsing a message handle it in the reactor loop.
        """
        if isinstance(msg, ResponseMessage):
            d = self.waiting_messages.pop(msg.response_to, None)
            if d != None:
                d.callback(msg)
        elif isinstance(msg, ServerMotdMessage):
            print("Connected: %s" % msg.motd)
            self.successful_connection()
        elif isinstance(msg, TopicUpdateMessage):
            callback = self.topic_callbacks.get((msg.service_name, msg.topic))
            if callback != None:
                threads.deferToThread(callback, **msg.params)
            
    def successful_connection(self):
        self.resetDelay()
        for (service_name, topic) in self.topic_callbacks.keys():
            msg = SubscribeMessage(service_name=service_name, topic=topic)
            serial_message = create_message_string(msg)
            self.current_protocol.send_message(serial_message)

    def send_message_blocking_from_thread(self, message):
        """
        Call from another thread to send a message to the server and wait for the result.
        Accepts a serializable message.
        Based on the response either the result is returned or an exception is raised.

        Can throw either a MessageHandleError or a ConnectionError
        """
        serial_message = create_message_string(message)
        result_msg = threads.blockingCallFromThread(reactor, self.send_message_and_wait, message.id, serial_message)
        if result_msg.result_code > 0:
            raise MessageHandleError(error_code=result_msg.result_code, error_details = result_msg.result)
        return result_msg.result

    def send_message_and_wait(self, message_id, serial_message):
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

    def send_action_request_from_thread(self, service_name, action, params):
        """
        Call from another thread to request an action to be performed at the server
        and wait for the result.

        Can throw either a MessageHandleError or a ConnectionError
        """
        msg = ActionRequestMessage(service_name=service_name, action=action, params=params)
        return self.send_message_blocking_from_thread(msg)

    def subscribe_from_thread(self, service_name, topic, callback):
        """
        Call from another thread to subscribe to a topic of a specific service.
        The given callback is called each time an update for the topic is received.
        Returns None, but an exception can be raised.

        Can throw either a MessageHandleError or a ConnectionError
        """
        msg = SubscribeMessage(service_name=service_name, topic=topic)
        self.send_message_blocking_from_thread(msg)

        # if subscribe failed an exception should be raised by now
        self.topic_callbacks[(service_name, topic)] = callback

        return None

    def is_connected(self):
        return self.current_protocol != None


class MessageResult(object):
    
    def __init__(self, response=None, original_message=None):
        self.response = response
        self.original_message = original_message

class MessageHandleError(Exception):

    RESULT_OK = 0
    RESULT_XML_PARSE_FAILED = 1
    RESULT_XML_INVALID = 2
    RESULT_UNKNOWN_MESSAGE = 3
    RESULT_UNEXPECTED_MESSAGE = 4
    RESULT_UNKNOWN_SERVICE = 5
    RESULT_UNKNOWN_ACTION = 6
    RESULT_INVALID_PARAMS = 7
    RESULT_UNKNOWN_ERROR = 99

    def __init__(self, error_code=RESULT_UNKNOWN_ERROR, original_message=None, error_details=None):
        self.error_code = error_code
        self.original_message = original_message
        self.error_details = error_details

    def __str__(self):
        return "MessageHandleError: (%d) %s" % (self.error_code, self.error_details)

class ConnectionError(Exception):

    def __init__(self, message=None):
        self.message = message