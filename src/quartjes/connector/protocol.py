__author__="Rob van der Most"
__date__ ="$May 27, 2011 8:53:12 PM$"

from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import NetstringReceiver
from twisted.internet import threads
import uuid
from quartjes.connector.messages import ServerRequestMessage
from quartjes.connector.messages import ServerMotdMessage, createMessageString

class QuartjesServerProtocol(NetstringReceiver):
    """
    Protocol implementation for the Quartjes server. For now we are using a basic
    Netstring receiver to listen for xml messages encoded as netstrings.
    """

    def __init__(self):
        self.id = uuid.uuid4()

    def connectionMade(self):
        print("Incoming connection")
        motd = ServerMotdMessage(clientId=self.id)
        self.transport.write(createMessageString(motd))
        self.factory.clientConnected(self)

    def stringReceived(self, string):
        print("Received %s" % string)
        self.factory.handleIncomingMessage(self, string)

    def connectionLost(self, reason):
        print("Connection lost: %s" % reason)
        self.factory.clientDisconnected(self)


class QuartjesServerFactory(ServerFactory):
    """
    Protocol factory to handle incoming connections for the Quartjes server.
    """

    protocol = QuartjesServerProtocol

    def __init__(self):
        self.clients = {}
        self.services = {}

    def clientConnected(self, client):
        self.clients[client.id] = client

    def clientDisconnected(self, client):
        del self.clients[client.id]

    def registerService(self, service):
        self.services[service.name] = service

    def unregisterService(self, service):
        self.services.remove(service.name)

    def handleIncomingMessage(self, client, message):
        d = threads.deferToThread(self.parseMessage, message, client)
        d.addCallbacks(callback=self.sendResult, errback=self.sendError, callbackArgs=(client,), errbackArgs=(client,))

    def parseMessage(self, string, client):

        msg = messages.parseMessageString(string)

        if isinstance(msg, ServerRequestMessage):
            return self.performAction(msg)
        else:
            raise MessageHandleError(MessageHandleError.RESULT_UNEXPECTED_MESSAGE)

    def performAction(self, msg):

        service = self.services[msg.serviceName]
        if service == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_SERVICE)

        return service.call(msg.action, msg.params)

    def sendResult(self, result, client):
        pass

    def sendError(self, result, client):
        pass


class QuartjesClientProtocol(Protocol):
    pass


class QuartjesClientFactory(ReconnectingClientFactory):
    protocol = QuartjesClientProtocol


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
        if meth != None:
           meth(params)
        

class MessageHandleError(Exception):

    RESULT_OK = 0
    RESULT_XML_PARSE_FAILED = 1
    RESULT_XML_INVALID = 2
    RESULT_UNKNOWN_MESSAGE = 3
    RESULT_UNEXPECTED_MESSAGE = 4
    RESULT_UNKNOWN_SERVICE = 5
    RESULT_UNKNOWN_ERROR = 99

    def __init__(self, errorCode=RESULT_UNKNOWN_ERROR):
        self.errorCode = errorCode

