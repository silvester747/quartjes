"""
Definition of messages used to communicate between the Quartjes server and its
clients.
"""

__author__="Rob van der Most"
__date__ ="$Jun 3, 2011 8:52:26 PM$"

import uuid
from quartjes.util.classtools import AttrDisplay
from quartjes.connector.serializer import addElement, createParameterList, parseParameterList
import xml.etree.ElementTree as et

class Message(AttrDisplay):
    """
    Base class all messages are derived from.
    """

class ServerRequestMessage(Message):
    """
    Message type used to send requests from clients to the server.
    """

    tagName = "serverRequest"

    def __init__(self, id=None, serviceName=None, action=None, params=None):
        self.id = id
        self.serviceName = serviceName
        self.action = action
        self.params = params

    def __eq__(self, other):
        return other != None and self.id == other.id and self.serviceName == other.serviceName and self.action == other.action and self.params == other.params

    def __ne__(self, other):
        return other == None or self.id != other.id or self.serviceName != other.serviceName or self.action != other.action or self.params != other.params

    def createXml(self):
        """
        Construct an element tree for this message and return the root of the tree.
        """

        root = addElement("serverRequest", parent=None, text=None)
        addElement("id", parent=root, text=self.id.urn)
        addElement("serviceName", parent=root, text=self.serviceName)
        addElement("action", parent=root, text=self.action)
        
        if self.params != None:
            serializeDict(root, self.params, tagName="params")

        return root

    @staticmethod
    def parseXml(root):
        """
        Parse an xml DOM document for this message type and return a new instance
        """

        assert root.tag == ServerRequestMessage.tagName

        node = root.find("id")
        if node == None:
            raise MessageHandleError(MessageHandleError.RESULT_XML_INVALID)
        id = uuid.UUID(node.text)

        serviceName = root.findtext("serviceName")
        if serviceName == None:
            raise MessageHandleError(MessageHandleError.RESULT_XML_INVALID)

        action = root.findtext("action")
        if action == None:
            raise MessageHandleError(MessageHandleError.RESULT_XML_INVALID)

        node = root.find("parameterList")
        params = None
        if node != None:
            params = deserializeDict(node)

        return ServerRequestMessage(id, serviceName, action, params)

def parseMessageString(string):
    """
    Parse a string for an xml message an return an instance of the contained
    message type.
    """

    root = et.fromstring(string)

    if root.tag == ServerRequestMessage.tagName:
        return ServerRequestMessage.parseXml(root)
    else:
        raise MessageHandleError(RESULT_UNKNOWN_MESSAGE)


def createMessageString(msg):
    root = msg.createXml()
    return et.tostring(root)



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

def selfTest():

    from quartjes.drink import Drink

    params = {"what":"that", "howmany":3, "price":2.10, "drink":Drink("Cola")}

    msg = ServerRequestMessage(uuid.uuid4(), "myservice", "myaction", params)
    assert msg == msg
    assert not msg != msg
    print(msg)

    string = createMessageString(msg)
    print(string)

    msg2 = parseMessageString(string)
    print(msg2)
    assert msg == msg2

if __name__ == "__main__":
    selfTest()
