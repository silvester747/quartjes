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

def serialize(obj, parent=None, tag_name="unknown"):
    """
    If a parent node is supplied the data is serialized as a sub element of the parent
    node. tagName is used as the name of the top level tag.
    """

    return add_value_element(obj, parent, tag_name)

def deserialize(node):
    """
    Deserialize the contents of the given node and return the instance.
    """

    return parse_value_element(node)


def serialize_dict(value, parent=None, tag_name="dict"):
    """
    Construct an XML representation of the given dictionary.
    Returns the created element.
    """
    #print("serializeDict %s" % value)
    dict_node = add_element(tag_name, parent=parent, type="dict")

    for (key, value) in value.items():

        item_node = add_element("item", parent=dict_node)
        add_element("key", text=key, parent=item_node)
        add_value_element(value, parent=item_node, tag_name="value")

    return dict_node

def deserialize_dict(node):
    """
    Parse the contents of the given node as a dictionary and return the
    contents.
    """
    params = {}

    param_elements = node.findall("item")

    for param in param_elements:

        key = param.findtext("key")
        value = parse_value_element(param.find("value"))

        if key != None:
            params[key] = value

    return params

def serialize_list(values, parent=None, tag_name="list"):
    """
    Serialize the contents of a list to xml.
    Returns the top element of the list.
    """
    #print("serializeList %s" % value)

    node = add_element(tag_name, parent=parent, type="list")

    for value in values:

        add_value_element(value, parent=node, tag_name="value")

    return node

def deserialize_list(node):
    """
    Parse an XML list node. Returns the original list.
    """
    value = []

    for item in node:

        value.append(parse_value_element(item))
    
    return value

def serialize_instance(obj=None, parent=None, tag_name="object"):
    """
    Create an XML representation of an object instance. All variables are stored in a
    parameter list. Returns the root element of the object.
    root can be None, in that case the object will have no parent.
    obj can be None, in that case a None value is stored.
    tagName can be used to override the default <object> tag.
    """
    #print("serializeInstance %s" % obj)

    obj_node = add_element(tag_name, parent=parent, type="instance")

    class_name = "%s.%s" % (obj.__class__.__module__, obj.__class__.__name__)

    obj_node.set("class", class_name)
    obj_node.set("id", obj.id.urn)

    for attr_name in obj.__serialize__:
        add_value_element(getattr(obj, attr_name, None), parent=obj_node, tag_name=attr_name)

    return obj_node

def deserialize_instance(node):
    """
    Read an object instance serialized to XML and return the instance.
    """
    
    id = uuid.UUID(node.get("id"))
    class_name = node.get("class")

    if id == None or class_name == None:
        return None

    klass = get_class_by_name(class_name)
    obj = klass()
    obj.id = id

    for element in node:
        value = parse_value_element(element)
        setattr(obj, element.tag, value)

    return obj

def get_class_by_name(class_name):
    """
    Get a class using the fully qualified name.
    """
    parts = class_name.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def add_element(tag_name, text=None, parent=None, type=None):
    """
    Add a new element with the given name to the XML document as a child of the given parent.
    If text is not None, a text node is added as a child of the new node.
    The new node is returned.
    """

    node = None
    if parent == None:
        node = et.Element(tag_name)
    else:
        node = et.SubElement(parent, tag_name)

    if text != None:
        node.text = text

    if type != None:
        node.set("type", type)

    return node

def add_value_element(value, parent=None, tag_name="value"):
    """
    Add a value inside an element. Use the correct way to serialize built-in
    types, library types or serializable types. The element is added to the
    parent. If no tagName is given, the default tag for the type of value is
    used.
    Returns the newly created element.
    """
    #print("addValueElement %s" % value)

    if hasattr(value, "__serialize__"):

        return serialize_instance(value, parent, tag_name)

    elif isinstance(value, dict):

        return serialize_dict(parent=parent, value=value, tag_name=tag_name)
        
    elif isinstance(value, list):

        return serialize_list(parent=parent, values=value, tag_name=tag_name)
        
    else:
        (string, type) = get_serialized_value(value)

        return add_element(tag_name, string, parent, type)

def parse_value_element(node):
    """
    Parse an element and based on the type call the correct deserializer.
    """
    type = node.get("type")

    if type == None or type == "NoneType":
        return None

    if type == "instance":
        return deserialize_instance(node)

    if type == "dict":
        return deserialize_dict(node)

    if type == "list":
        return deserialize_list(node)

    if not type in value_serializers_by_klass_name:
        return None

    ser = value_serializers_by_klass_name[type]
    return ser.deserialize(node.text)


value_serializers_by_klass = {}
value_serializers_by_klass_name = {}

def get_serialized_value(value):
    """
    Serialize the given value using a value serializer.
    Returns a tuple of: serialized value, type name
    If no serializer is present, the value is serialized as None.
    """
    
    if value == None:
        return (None, "NoneType")
    
    if not value.__class__ in value_serializers_by_klass:
        return (None, "NoneType")
    
    ser = value_serializers_by_klass[value.__class__]
    return (ser.serialize(value), ser.klass_name)


def add_value_serializer(ser):
    """
    Add a value serializer to the list of available serializers.
    """
    value_serializers_by_klass[ser.klass] = ser
    value_serializers_by_klass_name[ser.klass_name] = ser

class ValueSerializer(object):
    """
    Object for serializing a type of object containing only a single value. The
    value should be serialized into a single string that is stored in a single
    element.
    Create your custom version of this class to add unsupported data types.
    """

    def __init__(self, klass, serialize_method, deserialize_method):
        self.klass = klass
        self.serialize_method = serialize_method
        self.deserialize_method = deserialize_method
        self.klass_name = "%s.%s" % (klass.__module__, klass.__name__)

    def serialize(self, value):
        """
        Serialize the value into string format and return it.
        """
        return self.serialize_method(value)

    def deserialize(self, string):
        """
        Deserialize the given string and return the value.
        """
        return self.deserialize_method(string)

_int_serializer = ValueSerializer(int, str, int)
_string_serializer = ValueSerializer(str, lambda x: x, lambda x: x)
_float_serializer = ValueSerializer(float, str, float)
_uuid_serializer = ValueSerializer(uuid.UUID, lambda x: x.urn, uuid.UUID)

add_value_serializer(_int_serializer)
add_value_serializer(_string_serializer)
add_value_serializer(_float_serializer)
add_value_serializer(_uuid_serializer)


if __name__ == "__main__":

    from quartjes.drink import Drink

    value = uuid.uuid4()
    #print(value)
    string = _uuid_serializer.serialize(value)
    #print(string)
    value2 = _uuid_serializer.deserialize(string)
    #print(value2)
    assert value == value2

    #print(getSerializedValue(2))
    #print(getSerializedValue(2.1))
    #print(getSerializedValue("test"))
    #print(getSerializedValue(value))

    xml = add_value_element(value)
    #print(et.tostring(xml))

    params = {"what":"that", "howmany":3, "price":2.10, "drink":Drink("Cola")}
    xml = serialize_dict(parent=None, value=params)
    #print(et.tostring(xml))

    params2 = deserialize_dict(xml)
    #print(params2)
    #print(params2["drink"])
    assert params == params2

    xml = serialize(params, None, "message")
    #print(et.tostring(xml))
    params3 = deserialize(xml)
    assert params == params3
    
