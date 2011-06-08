"""
Methods for serializing Quartjes messages and objects to XML for transmitting
over the network or maybe even storing in files or other locations.

Objects to be serialized must implement:
* a constructor accepting zero arguments
* a class variable __serialize__ containing the names of variables to include
"""
__author__="Rob van der Most"
__date__ ="$Jun 8, 2011 7:32:02 PM$"

import xml.etree.ElementTree as et
import uuid

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
        elif hasattr(value, "__serialize__"):
            objValue = addElement("objectValue", parent=param)
            serializeObject(value, root=objValue)
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

    if node.tag != "object":
        node = node.find("object")

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



if __name__ == "__main__":

    from quartjes.drink import Drink

    d = Drink("Cola")
    xml = serializeObject(d)
    print(et.tostring(xml))
    d2 = parseObject(xml)
    print(d)
    print(d2)
