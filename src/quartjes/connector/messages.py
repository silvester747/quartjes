__author__="Rob van der Most"
__date__ ="$Jun 3, 2011 8:52:26 PM$"


class Message(object):
    """
    Base class all messages are derived from.
    """

class ServerRequestMessage(Message):
    """
    Message type used to send requests from clients to the server.
    """

    def __init__(self, id=None, serviceName=None, action=None, params=None):
        self.id = id
        self.serviceName = serviceName
        self.action = action
        self.params = params

    def createDocument(self, doc):
        """
        Add the contents of this message to a DOM document
        """
        
        root = appendElement(doc, doc, "serverRequest")
        appendElement(doc, root, "id", self.id)
        appendElement(doc, root, "serviceName", self.serviceName)
        appendElement(doc, root, "action", self.action)



    def parseDocument(doc):
        """
        Parse an xml DOM document for this message type and return a new instance
        """

        node = doc.firstChild
        if node == None or not node.localName == "id":
            raise MessageHandleError(RESULT_XML_INVALID)
        id = node.firstChild.nodeValue

        node = node.nextSibling
        if node == None or not node.localName == "service":
            raise MessageHandleError(RESULT_XML_INVALID)
        serviceName = node.firstChild.nodeValue

        node = node.nextSibling
        if node == None or not node.localName == "action":
            raise MessageHandleError(RESULT_XML_INVALID)
        action = node.firstChild.nodeValue

        node = node.nextSibling
        params = {}
        if node != None and node.localName == "parameterList":
            params = self.parseParameters(node)

        return ServerRequest(id, serviceName, action, params)


def parseMessageString(string):
    """
    Parse a string for an xml message an return an instance of the contained
    message type.
    """

    doc = minidom.parseString(string)

    if doc.documentElement == "serverRequest":
        return ServerRequestMessage.parseDocument(doc)
    else:
        raise MessageHandleError(RESULT_UNKNOWN_MESSAGE)

def parseParameters(node):
    params = {}


    return params

def parseObject(node):
    pass

def addElement(doc, parent, name, text=None):
    """
    Add a new element with the given name to the XML document as a child of the given parent.
    If text is not None, a text node is added as a child of the new node.
    The new node is returned.
    """
    node = doc.createElement(name)
    parent.appendChild(node)

    if (text != None):
        textNode = doc.createTextNode(text)
        node.appendChild(textNode)

    return node

def addParameterList(doc, parent, name, params):
    """
    Add a list of parameters as an XML parameterList.
    """
    pass

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



if __name__ == "__main__":
    print "Hello World"
