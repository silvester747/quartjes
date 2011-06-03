__author__="Rob van der Most"
__date__ ="$May 27, 2011 8:53:12 PM$"

from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import NetstringReceiver
from twisted.internet import threads
from twisted.python import failure
from xml.dom import minidom
import uuid
from quartjes.connector.messages import ServerRequest

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

    def clientConnected(self, client):
        self.clients[client.id] = client

    def clientDisconnected(self, client):
        self.clients.remove(client.id)

    def handleIncomingMessage(self, client, message):
        d = threads.deferToThread(self.parseMessage, message, client)
        d.addCallbacks(callback=self.sendResult, errback=self.sendError, callbackArgs=(client,), errbackArgs=(client,))

    def parseMessage(self, string, client):
        doc = minidom.parseString(string)
        if not doc.documentElement == "serverRequest":
            raise MessageHandleError(RESULT_XML_INVALID)

        node = doc.firstChild
        if node == None or not node.localName == "id":
            raise MessageHandleError(RESULT_XML_INVALID)
        id = node.firstChild.nodeValue

        node = node.nextSibling
        if node == None or not node.localName == "module":
            raise MessageHandleError(RESULT_XML_INVALID)
        module = node.firstChild.nodeValue
        
        node = node.nextSibling
        if node == None or not node.localName == "action":
            raise MessageHandleError(RESULT_XML_INVALID)
        action = node.firstChild.nodeValue

        node = node.nextSibling
        params = {}
        if node != None and node.localName == "parameterList":
            params = self.parseParameters(node)

        msg = ServerRequest(id, module, action, params)

        return self.performAction(msg)


    def parseParameters(self, node):
        params = {}


        return params

    def performAction(self, msg):
        pass

    def sendResult(self, result, client):
        pass

    def sendError(self, result, client):
        pass


class QuartjesClientProtocol(Protocol):
    pass


class QuartjesClientFactory(ReconnectingClientFactory):
    protocol = QuartjesClientProtocol


class EndPoint():
    pass

class ServerEndPoint(EndPoint):
    pass

class ClientEndPoint(EndPoint):
    def __init__(self, id=None):
        self.id = id

class MessageHandleError(Exception):
    
    def __init__(self, errorCode=RESULT_UNKNOWN_ERROR):
        self.errorCode = errorCode

RESULT_OK = 0
RESULT_XML_PARSE_FAILED = 1
RESULT_XML_INVALID = 2
RESULT_UNKNOWN_ERROR = 99