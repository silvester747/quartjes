"""
Methods for serializing Quartjes messages and objects to XML for transmitting
over the network or maybe even storing in files or other locations.

Several types of objects are supported for serialization:
* objects implementing a __serialize__ class variable and a constructor allowing
  zero arguments
* objects with a __dict__ variable and a constructor allowing zero arguments
* several builtin types like str, int, float, uuid
* tuples, lists and dictionaries of supported types
* custom types that are registered with this module
"""
__author__="Rob van der Most"
__date__ ="$Jun 8, 2011 7:32:02 PM$"

# In other modules using ElementTree always import the version from this file.
# That makes it easy to switch between py and c version.
import xml.etree.cElementTree as et
import uuid

def serialize(obj, parent=None, tag_name="unknown", cache=None):
    """
    If a parent node is supplied the data is serialized as a sub element of the parent
    node. tagName is used as the name of the top level tag.
    """
    if cache == None:
        cache = {}

    return add_value_element(obj, parent, tag_name, cache=cache)

def deserialize(node, cache=None):
    """
    Deserialize the contents of the given node and return the instance.
    """
    if cache == None:
        cache = {}

    return parse_value_element(node, cache=cache)


def serialize_dict(value, parent=None, tag_name="dict", cache=None):
    """
    Construct an XML representation of the given dictionary.
    Returns the created element.
    """
    #print("serializeDict %s" % value)
    dict_node = add_element(tag_name, parent=parent, type="dict")

    for (key, value) in value.items():

        item_node = add_element("item", parent=dict_node)
        add_element("key", text=key, parent=item_node)
        add_value_element(value, parent=item_node, tag_name="value", cache=cache)

    return dict_node

def deserialize_dict(node, cache=None):
    """
    Parse the contents of the given node as a dictionary and return the
    contents.
    """
    params = {}

    param_elements = node.findall("item")

    for param in param_elements:

        key = param.findtext("key")
        value = parse_value_element(param.find("value"), cache=cache)

        if key != None:
            params[key] = value

    return params

def serialize_list_or_tuple(values, parent=None, tag_name="list", cache=None):
    """
    Serialize the contents of a list to xml.
    Returns the top element of the list.
    """

    type = "list"
    if isinstance(values, tuple):
        type = "tuple"

    node = add_element(tag_name, parent=parent, type=type)
    for value in values:
        add_value_element(value, parent=node, tag_name="value", cache=cache)

    return node

def deserialize_list_or_tuple(node, cache=None):
    """
    Parse an XML list node. Returns the original list.
    """
    value = []
    for item in node:
        value.append(parse_value_element(item, cache=cache))

    type = node.get("type")
    if type == "tuple":
        return tuple(value)
    else:
        return value

def serialize_instance(obj=None, parent=None, tag_name="object", cache=None):
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

    if not hasattr(obj, "id"):
        obj.id = uuid.uuid4()

    obj_node.set("class", class_name)
    obj_node.set("id", obj.id.urn)

    if cache != None and obj.id in cache:
        obj_node.set("stub", "yes")
    else:
        attributes = None
        if hasattr(obj, "__serialize__"):
            attributes = obj.__serialize__
        else:
            attributes = obj.__dict__

        if cache != None:
            cache[obj.id] = obj
        for attr_name in attributes:
            if attr_name == "id":
                continue
                
            add_value_element(getattr(obj, attr_name, None), parent=obj_node, tag_name=attr_name, cache=cache)

    return obj_node

def deserialize_instance(node, cache=None):
    """
    Read an object instance serialized to XML and return the instance.
    """
    
    id = uuid.UUID(node.get("id"))
    class_name = node.get("class")

    if id == None or class_name == None:
        return None

    obj = None
    stub = node.get("stub")
    if stub == "yes":
        assert cache != None
        obj = cache.get(id)

    if obj == None:
        klass = get_class_by_name(class_name)
        obj = klass()
        obj.id = id

        if cache != None:
            cache[id] = obj

        for element in node:
            value = parse_value_element(element, cache=cache)
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

def add_value_element(value, parent=None, tag_name="value", cache=None):
    """
    Add a value inside an element. Use the correct way to serialize built-in
    types, library types or serializable types. The element is added to the
    parent. If no tagName is given, the default tag for the type of value is
    used.
    Returns the newly created element.
    """
    #print("addValueElement %s" % value)

    if hasattr(value, "__serialize__"):

        return serialize_instance(value, parent, tag_name, cache=cache)

    elif isinstance(value, dict):

        return serialize_dict(parent=parent, value=value, tag_name=tag_name, cache=cache)
        
    elif isinstance(value, list) or isinstance(value, tuple):

        return serialize_list_or_tuple(parent=parent, values=value, tag_name=tag_name, cache=cache)
        
    elif value.__class__ in value_serializers_by_klass:
        (string, type) = get_serialized_value(value)

        return add_element(tag_name, string, parent, type)

    elif hasattr(value, "__dict__"):

        return serialize_instance(value, parent, tag_name, cache=cache)

    else:

        return add_element(tag_name, None, parent, "NoneType")

def parse_value_element(node, cache=None):
    """
    Parse an element and based on the type call the correct deserializer.
    """
    type = node.get("type")

    if type == None or type == "NoneType":
        return None

    if type == "instance":
        return deserialize_instance(node, cache=cache)

    if type == "dict":
        return deserialize_dict(node, cache=cache)

    if type == "list" or type == "tuple":
        return deserialize_list_or_tuple(node, cache=cache)

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

