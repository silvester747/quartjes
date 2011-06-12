"""
Methods for serializing Quartjes messages and objects to XML for transmitting
over the network or maybe even storing in files or other locations.

Several types of objects are supported for serialization:
* objects implementing a __serialize__ class variable and a constructor allowing
  zero arguments
* several builtin types like str, int, float, uuid
* lists and dictionaries of supported types
* custom types that are registered with this module
"""
__author__="Rob van der Most"
__date__ ="$Jun 8, 2011 7:32:02 PM$"

import xml.etree.ElementTree as et
import uuid

def serialize(obj, parent=None, tagName="unknown"):
    """
    If a parent node is supplied the data is serialized as a sub element of the parent
    node. tagName is used as the name of the top level tag.
    """

    return addValueElement(obj, parent, tagName)

def deserialize(node):
    """
    """

    return parseValueElement(node)


def serializeDict(value, parent=None, tagName="dict"):
    """
    Construct an XML representation of the given dictionary.
    Returns the created element.
    """
    #print("serializeDict %s" % value)
    dictNode = addElement(tagName, parent=parent, type="dict")

    for (key, value) in value.items():

        itemNode = addElement("item", parent=dictNode)
        addElement("key", text=key, parent=itemNode)
        addValueElement(value, parent=itemNode, tagName="value")

    return dictNode

def deserializeDict(node):
    """
    Parse the contents of the given node as a dictionary and return the
    contents.
    """
    params = {}

    paramElements = node.findall("item")

    for param in paramElements:

        key = param.findtext("key")
        value = parseValueElement(param.find("value"))

        if key != None:
            params[key] = value

    return params

def serializeList(values, parent=None, tagName="list"):
    """
    Serialize the contents of a list to xml.
    Returns the top element of the list.
    """
    #print("serializeList %s" % value)

    node = addElement(tagName, parent=parent, type="list")

    for value in values:

        addValueElement(value, parent=node, tagName="value")

    return node

def deserializeList(node):
    """
    Parse an XML list node. Returns the original list.
    """
    value = []

    for item in node:

        value.append(parseValueElement(item))
    
    return value

def serializeInstance(obj=None, parent=None, tagName="object"):
    """
    Create an XML representation of an object instance. All variables are stored in a
    parameter list. Returns the root element of the object.
    root can be None, in that case the object will have no parent.
    obj can be None, in that case a None value is stored.
    tagName can be used to override the default <object> tag.
    """
    #print("serializeInstance %s" % obj)

    objNode = addElement(tagName, parent=parent, type="instance")

    className = "%s.%s" % (obj.__class__.__module__, obj.__class__.__name__)

    objNode.set("class", className)
    objNode.set("id", obj.id.urn)

    for attrName in obj.__serialize__:
        addValueElement(getattr(obj, attrName, None), parent=objNode, tagName=attrName)

    return objNode

def deserializeInstance(node):
    """
    Read an object instance serialized to XML and return the instance.
    """
    
    id = uuid.UUID(node.get("id"))
    className = node.get("class")

    if id == None or className == None:
        return None

    klass = getClassByName(className)
    obj = klass()
    obj.id = id

    for element in node:
        value = parseValueElement(element)
        setattr(obj, element.tag, value)

    return obj

def getClassByName(className):
    """
    Get a class using the fully qualified name.
    """
    parts = className.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def addElement(tagName, text=None, parent=None, type=None):
    """
    Add a new element with the given name to the XML document as a child of the given parent.
    If text is not None, a text node is added as a child of the new node.
    The new node is returned.
    """

    node = None
    if parent == None:
        node = et.Element(tagName)
    else:
        node = et.SubElement(parent, tagName)

    if text != None:
        node.text = text

    if type != None:
        node.set("type", type)

    return node

def addValueElement(value, parent=None, tagName="value"):
    """
    Add a value inside an element. Use the correct way to serialize built-in
    types, library types or serializable types. The element is added to the
    parent. If no tagName is given, the default tag for the type of value is
    used.
    Returns the newly created element.
    """
    #print("addValueElement %s" % value)

    if hasattr(value, "__serialize__"):

        return serializeInstance(value, parent, tagName)

    elif isinstance(value, dict):

        return serializeDict(parent=parent, value=value, tagName=tagName)
        
    elif isinstance(value, list):

        return serializeList(parent=parent, values=value, tagName=tagName)
        
    else:
        (string, type) = getSerializedValue(value)

        return addElement(tagName, string, parent, type)

def parseValueElement(node):
    """
    Parse an element and based on the type call the correct deserializer.
    """
    type = node.get("type")

    if type == None or type == "NoneType":
        return None

    if type == "instance":
        return deserializeInstance(node)

    if type == "dict":
        return deserializeDict(node)

    if type == "list":
        return deserializeList(node)

    if not type in valueSerializersByKlassName:
        return None

    ser = valueSerializersByKlassName[type]
    return ser.deserialize(node.text)


valueSerializersByKlass = {}
valueSerializersByKlassName = {}

def getSerializedValue(value):
    """
    Serialize the given value using a value serializer.
    Returns a tuple of: serialized value, type name
    If no serializer is present, the value is serialized as None.
    """
    
    if value == None:
        return (None, "NoneType")
    
    if not value.__class__ in valueSerializersByKlass:
        return (None, "NoneType")
    
    ser = valueSerializersByKlass[value.__class__]
    return (ser.serialize(value), ser.klassName)


def addValueSerializer(ser):
    """
    Add a value serializer to the list of available serializers.
    """
    valueSerializersByKlass[ser.klass] = ser
    valueSerializersByKlassName[ser.klassName] = ser

class ValueSerializer(object):
    """
    Object for serializing a type of object containing only a single value. The
    value should be serialized into a single string that is stored in a single
    element.
    Create your custom version of this class to add unsupported data types.
    """

    def __init__(self, klass, serializeMethod, deserializeMethod):
        self.klass = klass
        self.serializeMethod = serializeMethod
        self.deserializeMethod = deserializeMethod
        self.klassName = "%s.%s" % (klass.__module__, klass.__name__)

    def serialize(self, value):
        """
        Serialize the value into string format and return it.
        """
        return self.serializeMethod(value)

    def deserialize(self, string):
        """
        Deserialize the given string and return the value.
        """
        return self.deserializeMethod(string)

_intSerializer = ValueSerializer(int, str, int)
_stringSerializer = ValueSerializer(str, lambda x: x, lambda x: x)
_floatSerializer = ValueSerializer(float, str, float)
_uuidSerializer = ValueSerializer(uuid.UUID, lambda x: x.urn, uuid.UUID)

addValueSerializer(_intSerializer)
addValueSerializer(_stringSerializer)
addValueSerializer(_floatSerializer)
addValueSerializer(_uuidSerializer)


if __name__ == "__main__":

    from quartjes.drink import Drink

    value = uuid.uuid4()
    #print(value)
    string = _uuidSerializer.serialize(value)
    #print(string)
    value2 = _uuidSerializer.deserialize(string)
    #print(value2)
    assert value == value2

    #print(getSerializedValue(2))
    #print(getSerializedValue(2.1))
    #print(getSerializedValue("test"))
    #print(getSerializedValue(value))

    xml = addValueElement(value)
    #print(et.tostring(xml))

    params = {"what":"that", "howmany":3, "price":2.10, "drink":Drink("Cola")}
    xml = serializeDict(parent=None, value=params)
    #print(et.tostring(xml))

    params2 = deserializeDict(xml)
    #print(params2)
    #print(params2["drink"])
    assert params == params2

    xml = serialize(params, None, "message")
    #print(et.tostring(xml))
    params3 = deserialize(xml)
    assert params == params3
    
