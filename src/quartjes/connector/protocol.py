__author__="Rob van der Most"
__date__ ="$May 27, 2011 8:53:12 PM$"

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor, threads, defer
from twisted.protocols.basic import NetstringReceiver
from twisted.internet import threads
import uuid
from quartjes.connector.messages import ActionRequestMessage, ResponseMessage
from quartjes.connector.messages import ServerMotdMessage, create_message_string, parse_message_string

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
        self.factory.client_connected(self)

    def stringReceived(self, string):
        """
        Fired by twisted when a complete netstring is received.
        """
        self.factory.handle_incoming_message(string, self)

    def connectionLost(self, reason):
        """
        Fired by twisted when the connection is lost.
        """
        self.factory.client_disconnected(self)

    def send_message(self, serial_message):
        """
        Send the XML message to the other end of this connection.
        """
        #print("Sending message: %s" % msg)
        self.sendString(serial_message)


class QuartjesServerFactory(ServerFactory):
    """
    Protocol factory to handle incoming connections for the Quartjes server.
    """

    protocol = QuartjesProtocol

    def __init__(self):
        self.clients = {}
        self.services = {}

    def client_connected(self, client):
        self.clients[client.id] = client
        motd = ServerMotdMessage(client_id=client.id)
        client.send_message(create_message_string(motd))

    def client_disconnected(self, client):
        del self.clients[client.id]

    def register_service(self, service):
        self.services[service.name] = service

    def unregister_service(self, service):
        self.services.remove(service.name)

    def handle_incoming_message(self, string, client):
        #print("Incoming: %s" % string)
        d = threads.deferToThread(self.parse_message, string, client)
        d.addCallbacks(callback=self.send_result, errback=self.send_error, callbackArgs=(client,), errbackArgs=(client,))

    def parse_message(self, string, client):
        #print("Parsing message: %s" % string)
        msg = parse_message_string(string)
        result = None

        if isinstance(msg, ActionRequestMessage):
            result = self.perform_action(msg)
        else:
            raise MessageHandleError(MessageHandleError.RESULT_UNEXPECTED_MESSAGE, msg)

        response_msg = ResponseMessage(result_code=0, result=result, response_to=msg.id)

        return create_message_string(response_msg)

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

    def send_result(self, response, client):
        #print("Send result: %s" % result)
        client.send_message(response)

    def send_error(self, result, client):
        error = result.value
        #print("Error occurred: %s" % result)
        id = None
        if error.original_message != None:
            id = error.original_message.id
        msg = ResponseMessage(result_code=error.error_code, response_to=id, result=error.error_details)
        client.send_message(create_message_string(msg))


class QuartjesClientFactory(ReconnectingClientFactory):
    """
    Client factory for quartjes client. Implements the reconnecting client factory
    to make sure it reconnects in case of errors.
    """
    protocol = QuartjesProtocol

    def __init__(self):
        self.waiting_messages = {}
        self.current_client = None
        self.topic_callbacks = {}

    def client_connected(self, client):
        """
        Handle a newly established connection to the server.
        """
        print("Client connected")
        self.current_client = client

    def client_disconnected(self, client):
        """
        Handle a lost connection.
        """
        print("Client disconnected")
        self.current_client = None

    def handle_incoming_message(self, string, client):
        """
        Handle incoming messages. Defers parsing the message to another thread, so the
        reactor is not blocked.
        """
        #print("Incoming: %s" % string)
        d = threads.deferToThread(parse_message_string, string)
        d.addCallback(self.handle_message_contents, client)

    def handle_message_contents(self, msg, client):
        """
        After parsing a message handle it in the reactor loop.
        """
        if isinstance(msg, ResponseMessage):
            d = self.waiting_messages.get(msg.response_to)
            if d != None:
                d.callback(msg)
        elif isinstance(msg, ServerMotdMessage):
            print("Connected: %s" % msg.motd)
            self.resetDelay()
        elif isinstance(msg, TopicUpdateMessage):
            callback = self.topic_callbacks.get((msg.service_name, msg.topic))
            if callback != None:
                threads.deferToThread(callback, **msg.params)
            

    def send_message_blocking_from_thread(self, message):
        """
        Call from another thread to send a message to the server and wait for the result.
        Accepts a serializable message.
        Based on the response either the result is returned or an exception is raised.
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
        d = defer.Deferred()
        self.waiting_messages[message_id] = d
        self.current_client.send_message(serial_message)
        return d

    def send_action_request_from_thread(self, service_name, action, params):
        """
        Call from another thread to request an action to be performed at the server
        and wait for the result.
        """
        msg = ActionRequestMessage(service_name=service_name, action=action, params=params)
        return self.send_message_blocking_from_thread(msg)

    def subscribe_from_thread(self, service_name, topic, callback):
        """
        Call from another thread to subscribe to a topic of a specific service.
        The given callback is called each time an update for the topic is received.
        Returns None, but an exception can be raised.
        """
        msg = SubscribeMessage(service_name=service_name, topic=topic)
        self.send_message_blocking_from_thread(msg)

        # if subscribe failed an exception should be raised by now
        self.topic_callbacks[(service_name, topic)] = callback

        return None


class MessageResult(object):
    
    def __init__(self, result=None, original_message=None):
        self.result = result
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

