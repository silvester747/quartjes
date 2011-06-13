__author__="Rob van der Most"
__date__ ="$May 27, 2011 8:53:12 PM$"

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor, threads, defer
from twisted.protocols.basic import NetstringReceiver
from twisted.internet import threads
import uuid
from quartjes.connector.messages import ServerRequestMessage, ServerResponseMessage
from quartjes.connector.messages import ServerMotdMessage, createMessageString, parseMessageString

class QuartjesProtocol(NetstringReceiver):
    """
    Protocol implementation for the Quartjes application. For now we are using a basic
    Netstring receiver to listen for xml messages encoded as netstrings.
    """

    def __init__(self):
        self.id = uuid.uuid4()

    def connectionMade(self):
        self.factory.clientConnected(self)

    def stringReceived(self, string):
        self.factory.handleIncomingMessage(string, self)

    def connectionLost(self, reason):
        self.factory.clientDisconnected(self)

    def sendMessageAsXml(self, msg):
        #print("Sending message: %s" % msg)
        self.sendString(createMessageString(msg))


class QuartjesServerFactory(ServerFactory):
    """
    Protocol factory to handle incoming connections for the Quartjes server.
    """

    protocol = QuartjesProtocol

    def __init__(self):
        self.clients = {}
        self.services = {}

    def clientConnected(self, client):
        self.clients[client.id] = client
        motd = ServerMotdMessage(clientId=client.id)
        client.sendMessageAsXml(motd)

    def clientDisconnected(self, client):
        del self.clients[client.id]

    def registerService(self, service):
        self.services[service.name] = service

    def unregisterService(self, service):
        self.services.remove(service.name)

    def handleIncomingMessage(self, string, client):
        #print("Incoming: %s" % string)
        d = threads.deferToThread(self.parseMessage, string, client)
        d.addCallbacks(callback=self.sendResult, errback=self.sendError, callbackArgs=(client,), errbackArgs=(client,))

    def parseMessage(self, string, client):
        #print("Parsing message: %s" % string)
        msg = parseMessageString(string)
        result = None

        if isinstance(msg, ServerRequestMessage):
            result = self.performAction(msg)
        else:
            raise MessageHandleError(MessageHandleError.RESULT_UNEXPECTED_MESSAGE, msg)

        return MessageResult(result=result, originalMessage=msg)

    def performAction(self, msg):
        #print("Performing service: %s, action: %s" % (msg.serviceName, msg.action))
        service = self.services.get(msg.serviceName)
        if service == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_SERVICE, msg)

        return service.call(msg.action, msg.params)

    def sendResult(self, result, client):
        #print("Send result: %s" % result)
        msg = ServerResponseMessage(resultCode=0, result=result.result, responseTo=result.originalMessage.id)
        client.sendMessageAsXml(msg)

    def sendError(self, result, client):
        error = result.value
        #print("Error occurred: %s" % result)
        id = None
        if error.originalMessage != None:
            id = error.originalMessage.id
        msg = ServerResponseMessage(resultCode=error.errorCode, responseTo=id)
        client.sendMessageAsXml(msg)


class QuartjesClientFactory(ReconnectingClientFactory):
    """
    Client factory for quartjes client. Implements the reconnecting client factory
    to make sure it reconnects in case of errors.
    """
    protocol = QuartjesProtocol

    def __init__(self):
        self.waitingMessages = {}
        self.currentClient = None

    def clientConnected(self, client):
        print("Client connected")
        self.currentClient = client

    def clientDisconnected(self, client):
        print("Client disconnected")
        self.currentClient = None

    def handleIncomingMessage(self, string, client):
        #print("Incoming: %s" % string)
        d = threads.deferToThread(parseMessageString, string)
        d.addCallback(self.handleMessageContents, client)

    def handleMessageContents(self, msg, client):
        if isinstance(msg, ServerResponseMessage):
            d = self.waitingMessages.get(msg.responseTo)
            if d != None:
                d.callback(msg)
        elif isinstance(msg, ServerMotdMessage):
            print("Connected: %s" % msg.motd)
            self.resetDelay()


    def sendMessageBlockingFromThread(self, message):
        return threads.blockingCallFromThread(reactor, self.sendMessageAndWait, message)

    def sendMessageAndWait(self, message):
        d = defer.Deferred()
        self.waitingMessages[message.id] = d
        self.currentClient.sendMessageAsXml(message)
        return d

class Service(object):
    """
    Base class to be implemented by services using the protocol.
    In derived implementations create actions as function definitions with format:
    action_<action name>. The parameters are passed as dictionary. You can accept
    the dictionary or let Python fill the arguments by keyword.
    """

    def __init__(self, name="Unnamed"):
        self.name = name

    def call(self, action, params):
        meth = getattr(self, "action_%s" % action, None)
        if meth == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_ACTION)

        return meth(**params)

class TestService(Service):
    
    def __init__(self):
        Service.__init__(self, "test")
    
    def action_test(self, text):
        return text

class MessageResult(object):
    
    def __init__(self, result=None, originalMessage=None):
        self.result = result
        self.originalMessage = originalMessage

class MessageHandleError(Exception):

    RESULT_OK = 0
    RESULT_XML_PARSE_FAILED = 1
    RESULT_XML_INVALID = 2
    RESULT_UNKNOWN_MESSAGE = 3
    RESULT_UNEXPECTED_MESSAGE = 4
    RESULT_UNKNOWN_SERVICE = 5
    RESULT_UNKNOWN_ACTION = 6
    RESULT_UNKNOWN_ERROR = 99

    def __init__(self, errorCode=RESULT_UNKNOWN_ERROR, originalMessage=None):
        self.errorCode = errorCode
        self.originalMessage = originalMessage

