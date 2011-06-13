__author__="Rob van der Most"
__date__ ="$May 27, 2011 8:53:12 PM$"

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor, threads, defer
from twisted.protocols.basic import NetstringReceiver
from twisted.internet import threads
import uuid
from quartjes.connector.messages import ServerRequestMessage, ServerResponseMessage
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

    def send_message_as_xml(self, msg):
        """
        Send the XML message to the other end of this connection.
        """
        #print("Sending message: %s" % msg)
        self.sendString(create_message_string(msg))


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
        client.send_message_as_xml(motd)

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

        if isinstance(msg, ServerRequestMessage):
            result = self.perform_action(msg)
        else:
            raise MessageHandleError(MessageHandleError.RESULT_UNEXPECTED_MESSAGE, msg)

        return MessageResult(result=result, original_message=msg)

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

    def send_result(self, result, client):
        #print("Send result: %s" % result)
        msg = ServerResponseMessage(result_code=0, result=result.result, response_to=result.original_message.id)
        client.send_message_as_xml(msg)

    def send_error(self, result, client):
        error = result.value
        #print("Error occurred: %s" % result)
        id = None
        if error.original_message != None:
            id = error.original_message.id
        msg = ServerResponseMessage(result_code=error.error_code, response_to=id)
        client.send_message_as_xml(msg)


class QuartjesClientFactory(ReconnectingClientFactory):
    """
    Client factory for quartjes client. Implements the reconnecting client factory
    to make sure it reconnects in case of errors.
    """
    protocol = QuartjesProtocol

    def __init__(self):
        self.waiting_messages = {}
        self.current_client = None

    def client_connected(self, client):
        print("Client connected")
        self.current_client = client

    def client_disconnected(self, client):
        print("Client disconnected")
        self.current_client = None

    def handle_incoming_message(self, string, client):
        #print("Incoming: %s" % string)
        d = threads.deferToThread(parse_message_string, string)
        d.addCallback(self.handle_message_contents, client)

    def handle_message_contents(self, msg, client):
        if isinstance(msg, ServerResponseMessage):
            d = self.waiting_messages.get(msg.response_to)
            if d != None:
                d.callback(msg)
        elif isinstance(msg, ServerMotdMessage):
            print("Connected: %s" % msg.motd)
            self.resetDelay()

    def send_message_blocking_from_thread(self, message):
        return threads.blockingCallFromThread(reactor, self.send_message_and_wait, message)

    def send_message_and_wait(self, message):
        d = defer.Deferred()
        self.waiting_messages[message.id] = d
        self.current_client.send_message_as_xml(message)
        return d

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

    def __init__(self, error_code=RESULT_UNKNOWN_ERROR, original_message=None):
        self.error_code = error_code
        self.original_message = original_message

