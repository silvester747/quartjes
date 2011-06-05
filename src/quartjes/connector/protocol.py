__author__="Rob van der Most"
__date__ ="$May 27, 2011 8:53:12 PM$"

from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import NetstringReceiver
from twisted.internet import threads
import uuid
from quartjes.connector.messages import MessageHandleError, ServerRequestMessage

class QuartjesServerProtocol(NetstringReceiver):
    """
    Protocol implementation for the Quartjes server. For now we are using a basic
    Netstring receiver to listen for xml messages encoded as netstrings.
    """

    def __init(self):
        self.id = uuid.uuid4()

    def connectionMade(self):
        print("Incoming connection")
        self.transport.write("Hello there!")
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
        self.clients.remove(client.id)

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


class EndPoint(object):
    pass

class ServerEndPoint(EndPoint):
    pass

class ClientEndPoint(EndPoint):
    def __init__(self, id=None):
        self.id = id

class Service(object):
    """
    Base class to be implemented by services using the protocol.
    """

    def __init__(self, name="Unnamed"):
        self.name = name

    def call(self, action, params):
        pass
    