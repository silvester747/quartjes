__author__="Rob van der Most"
__date__ ="$May 27, 2011 8:53:12 PM$"

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor, threads, defer
from twisted.protocols.basic import NetstringReceiver
from twisted.internet import threads
import uuid
from quartjes.connector.messages import ServerRequestMessage, ServerResponseMessage
from quartjes.connector.messages import ServerMotdMessage, createMessageString

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
        self.transport.write(createMessageString(msg))


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
        d = threads.deferToThread(self.parseMessage, string, client)
        d.addCallbacks(callback=self.sendResult, errback=self.sendError, callbackArgs=(client,), errbackArgs=(client,))

    def parseMessage(self, string, client):
        msg = messages.parseMessageString(string)
        result = None

        if isinstance(msg, ServerRequestMessage):
            result = self.performAction(msg)
        else:
            raise MessageHandleError(MessageHandleError.RESULT_UNEXPECTED_MESSAGE, msg)

        return MessageResult(result=result, originalMessage=msg)

    def performAction(self, msg):
        service = self.services[msg.serviceName]
        if service == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_SERVICE, msg)

        return service.call(msg.action, msg.params)

    def sendResult(self, result, client):
        msg = ServerResponseMessage(0, result=result, responseTo=result.originalMessage.id)
        client.sendMessageAsXml(msg)

    def sendError(self, result, client):
        id = None
        if result.originalMessage != None:
            id = result.originalMessage.id
        msg = ServerResponseMessage(result.errorCode, responseTo=id)
        client.sendMessageAsXml(msg)


class QuartjesClientFactory(ReconnectingClientFactory):
    """
    Client factory for quartjes client. Implements the reconnecting client factory
    to make sure it reconnects in case of errors.
    """
    protocol = QuartjesProtocol
    waitingMessages = {}
    currentClient = None

    def clientConnected(self, client):
        print("Client connected")
        self.resetDelay()

    def clientDisconnected(self, client):
        print("Client disconnected")

    def handleIncomingMessage(self, string, client):
        print("Incoming: %s" % string)
        d = threads.deferToThread(messages.parseMessageString, string)
        d.addCallback(handleMessageContents, client)

    def handleMessageContents(self, msg, client):
        if isinstance(msg, ServerResponseMessage):
            d = waitingMessages.get(msg.responseTo)
            if d != None:
                if msg.errorCode == 0:
                    d.callback(msg.result)
                else:
                    d.errback(MessageHandleError(msg.errorCode))
        elif isinstance(msg, ServerMotdMessage):
            print("Connected: %s" % msg.motd)


    def sendMessageBlockingFromThread(self, message):
        return threads.blockingCallFromThread(reactor, self.sendMessageAndWait, message)

    def sendMessageAndWait(self, message):
        d = defer.Deferred()
        waitingMessages[message.id] = d
        currentClient.sendMessageAsXml(message)
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
        meth = getattr(self, "action_%s" % action, default=None)
        if meth == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_ACTION)

        meth(params)

class TestService(Service):
    
    def __init__(self):
        Service.__init__("test")
    
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

