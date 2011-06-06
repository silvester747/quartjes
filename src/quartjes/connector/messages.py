__author__="Rob van der Most"
__date__ ="$Jun 3, 2011 8:52:26 PM$"

import uuid
import xml.etree.ElementTree as et
from quartjes.util.classtools import AttrDisplay

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
        return self.id == other.id and self.serviceName == other.serviceName and self.action == other.action and self.params == other.params

    def __ne__(self, other):
        return self.id != other.id or self.serviceName != other.serviceName or self.action != other.action or self.params != other.params

    def createXml(self):
        """
        Construct an element tree for this message and return the root of the tree.
        """

        root = addElement("serverRequest", parent=None, text=None)
        addElement("id", parent=root, text=self.id.urn)
        addElement("serviceName", parent=root, text=self.serviceName)
        addElement("action", parent=root, text=self.action)
        
        if self.params != None:
            createParameterList(root, self.params)

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
            params = parseParameters(node)

        return ServerRequestMessage(id, serviceName, action, params)


class Parameter(AttrDisplay):
    def __init__(self, name="Unnamed", value=None):
        self.name = name
        self.value = value


def createParameterList(root, params):
    """
    Construct an XML paramter list for the given dictionary containing parameters
    """
    paramList = addElement("parameterList", parent=root)

    for (key, value) in params.items():
        fieldName = None
        strValue = None

        param = addElement("parameter", parent=paramList)
        addElement("name", text=key, parent=param)

        if isinstance(value, int):
            fieldName = "intValue"
            strValue = str(value)
        elif isinstance(value, float):
            fieldName = "doubleValue"
            strValue = str(value)
        elif isinstance(value, str):
            fieldName = "stringValue"
            strValue = value
        elif isinstance(value, object):
            serializeObject(param, value)
            continue
        else:
            fieldName = "stringValue"
            strValue = str(value)

        addElement(fieldName, text = strValue, parent=param)
        


def serializeObject(root, obj):
    pass

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

def parseParameters(node):
    params = {}


    return params

def parseObject(node):
    pass

def addElement(name, text=None, parent=None):
    """
    Add a new element with the given name to the XML document as a child of the given parent.
    If text is not None, a text node is added as a child of the new node.
    The new node is returned.
    """

    node = None
    if parent == None:
        node = et.Element(name)
    else:
        node = et.SubElement(parent, name)

    if text != None:
        node.text = text

    return node

def addParameterList(doc, parent, name, params):
    """
    Add a list of parameters as an XML parameterList.
    """
    pass

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

    params = {"what":"that", "howmany":3, "price":2.10}

    msg = ServerRequestMessage(uuid.uuid4(), "myservice", "myaction", params)
    assert msg == msg
    assert not msg != msg
    print(msg)

    string = createMessageString(msg)
    print(string)

    msg2 = parseMessageString(string)
    print(msg2)
    #assert msg == msg2


if __name__ == "__main__":
    selfTest()
