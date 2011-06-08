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
            params = parseParameterList(node)

        return ServerRequestMessage(id, serviceName, action, params)


def createParameterList(root, params):
    """
    Construct an XML parameter list for the given dictionary containing parameters.
    Always starts adding a tag <parameterList> to the given parent.
    Returns the <parameterList> tag.
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
        elif getattr(object, "__serialize__", None) != None:
            serializeObject(param, value)
            continue
        else:
            fieldName = "stringValue"
            strValue = str(value)

        addElement(fieldName, text = strValue, parent=param)

    return paramList


def serializeObject(obj=None, root=None, tagName="object"):
    """
    Create an XML representation of an object. All variables are stored in a
    parameter list. Returns the root element of the object.
    root can be None, in that case the object will have no parent.
    obj can be None, in that case a None value is stored.
    tagName can be used to override the default <object> tag.
    """

    objNode = addElement(tagName, parent=root)

    if obj == None:
        return objNode

    objName = "%s.%s" % (obj.__class__.__module__, obj.__class__.__name__)

    addElement("id", parent=objNode, text=obj.id.urn)
    addElement("type", parent=objNode, text=objName)

    attrs = {}

    for attrName in obj.__serialize__:
        attrs[attrName] = getattr(obj, attrName, None)

    createParameterList(objNode, attrs)

    return objNode



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

def parseParameterList(node):
    """
    Parse a <parameterList> tag and return the contents as a dictionary.
    Accepts a parameterList element or searches the given node for a
    parameterList tag.
    """
    params = {}

    if node.tag != "parameterList":
        node = node.find("parameterList")

    paramElements = node.findall("parameter")

    for param in paramElements:

        key = None
        value = None

        for e in param:
            if e.tag == "name":
                key = e.text
            elif e.tag == "stringValue":
                value = e.text
            elif e.tag == "objectValue":
                value = parseObject(e)
            elif e.tag == "intValue":
                value = int(e.text)
            elif e.tag == "doubleValue":
                value = float(e.text)

        if key != None:
            params[key] = value


    return params

def parseObject(node):
    """
    Read an object serialized to XML and return the object.
    """

    id = uuid.UUID(node.findtext("id"))
    className = node.findtext("type")

    if id == None or className == None:
        return None

    params = parseParameterList(node)

    klass = getClassByName(className)
    obj = klass()
    obj.id = id

    for (key, value) in params.items():
        setattr(obj, key, value)

    return obj

def getClassByName(className):
    parts = className.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


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

    params = {"what":"that", "howmany":3, "price":2.10}

    msg = ServerRequestMessage(uuid.uuid4(), "myservice", "myaction", params)
    assert msg == msg
    assert not msg != msg
    print(msg)

    string = createMessageString(msg)
    print(string)

    msg2 = parseMessageString(string)
    print(msg2)
    assert msg == msg2

    d = Drink("Cola")
    xml = serializeObject(d)
    print(et.tostring(xml))
    d2 = parseObject(xml)
    print(d)
    print(d2)

if __name__ == "__main__":
    selfTest()
