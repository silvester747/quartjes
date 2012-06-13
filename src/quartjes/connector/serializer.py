"""
Methods for serializing Quartjes messages and objects to XML for transmitting
over the network or maybe even storing in files or other locations.

Several types of objects are supported for serialization:

* objects implementing a __serialize__ class variable and a constructor allowing
  zero arguments
* objects with a __dict__ variable (e.g. python classes) and a constructor 
  allowing zero arguments
* several builtin types like str, int, float, uuid
* tuples, lists and dictionaries of supported types
* custom types that are registered with this module

Some object types are not supported and will be ignored (this will not break
existing methods on classes, just happens when you assign such a method to
a instance variable):

* various types of functions and methods
* file handles

For class instances with an id attribute containing a UUID, that id is used
as identifier of the serialized object. If no id attribute is present, one
is added to the instance.

Usage
-----
In most cases only :func:`serialize` and :func:`deserialize` need to be used.

Cache
-----
Troughout this module a parameter cache is used for most functions. This cache
parameter should contain a dictionary where the key is the unique id of the
object and the value is the object. If an object is present in the cache it
is considered already serialized or deserialized. In case of serializing this
will result in only a reference being added. In case of deserializing the 
object is directly referenced if the stream contains only a reference and
if the stream contains the full object it is fully deserialized.
"""

__author__ = "Rob van der Most"
__docformat__ = "restructuredtext en"

# In other modules using ElementTree always import the version from this file.
# That makes it easy to switch between py and c version.
import xml.etree.cElementTree as et
import uuid
import types

ignored_types = (types.FunctionType, types.BuiltinFunctionType, types.BuiltinMethodType,
                 types.FileType, types.GeneratorType, types.LambdaType, types.MemberDescriptorType,
                 types.MethodType, types.ModuleType, types.TypeType, types.UnboundMethodType)
"""
For these internal types, serialization is not supported. They will be ignored
when encountered.
"""

def serialize(obj, parent=None, tag_name="unknown", cache=None):
    """
    Serialize an object.
    
    Parameters
    ----------
    obj
        The object to serialize.
    parent : ElementTree Node
        If present: Node to use as a parent of this object.
    tag_name : string
        Name of the tag to enclose the object in.
    cache : dict
        Dictionary to use as cache.
    
    Returns
    -------
    node : ElementTree Node
        Root node containing the serialized object.
    """
    if cache == None:
        cache = {}

    return add_value_element(obj, parent, tag_name, cache=cache)

def deserialize(node, cache=None):
    """
    Deserialize the contents of the given node and return the instance.
    
    Parameters
    ----------
    node : ElementTree Node
        Root node of the object to deserialize.
    cache : dict
        Dictionary to use as cache.

    Returns
    -------
    obj
        Deserialized object.
    """
    if cache == None:
        cache = {}

    return parse_value_element(node, cache=cache)


def serialize_dict(value, parent=None, tag_name="dict", cache=None):
    """
    Construct an XML representation of the given dictionary.

    Parameters
    ----------
    value : dict
        The dictionary to serialize.
    parent : ElementTree Node
        If present: Node to use as a parent of this object.
    tag_name : string
        Name of the tag to enclose the object in.
    cache : dict
        Dictionary to use as cache.
    
    Returns
    -------
    node : ElementTree Node
        Root node containing the serialized dictionary.
    """
    #print("serializeDict %s" % value)
    dict_node = add_element(tag_name, parent=parent, type_name="dict")

    for (key, value) in value.items():

        item_node = add_element("item", parent=dict_node)
        add_element("key", text=key, parent=item_node)
        add_value_element(value, parent=item_node, tag_name="value", cache=cache)

    return dict_node

def deserialize_dict(node, cache=None):
    """
    Parse the contents of the given node as a dictionary and return the
    contents.
    
    Parameters
    ----------
    node : ElementTree Node
        Root node of the object to deserialize.
    cache : dict
        Dictionary to use as cache.

    Returns
    -------
    obj : dict
        Deserialized dictionary.
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

    Parameters
    ----------
    values : list or tuple
        The list or tuple to serialize.
    parent : ElementTree Node
        If present: Node to use as a parent of this object.
    tag_name : string
        Name of the tag to enclose the object in.
    cache : dict
        Dictionary to use as cache.
    
    Returns
    -------
    node : ElementTree Node
        Root node containing the serialized list or tuple.
    """

    type_name = "list"
    if isinstance(values, tuple):
        type_name = "tuple"

    node = add_element(tag_name, parent=parent, type_name=type_name)
    for value in values:
        add_value_element(value, parent=node, tag_name="value", cache=cache)

    return node

def deserialize_list_or_tuple(node, cache=None):
    """
    Parse an XML list node. Returns the original list.
    
    Parameters
    ----------
    node : ElementTree Node
        Root node of the object to deserialize.
    cache : dict
        Dictionary to use as cache.

    Returns
    -------
    obj : list or tuple
        Deserialized list or tuple.
    """
    value = []
    for item in node:
        value.append(parse_value_element(item, cache=cache))

    type_name = node.get("type")
    if type_name == "tuple":
        return tuple(value)
    else:
        return value

def serialize_instance(obj=None, parent=None, tag_name="object", cache=None):
    """
    Create an XML representation of an object instance. All variables are stored in a
    parameter list. 

    Parameters
    ----------
    obj
        The object instance to serialize.
    parent : ElementTree Node
        If present: Node to use as a parent of this object.
    tag_name : string
        Name of the tag to enclose the object in.
    cache : dict
        Dictionary to use as cache.
    
    Returns
    -------
    node : ElementTree Node
        Root node containing the serialized object.
    """
    #print("serializeInstance %s" % obj)

    obj_node = add_element(tag_name, parent=parent, type_name="instance")

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
    
    Parameters
    ----------
    node : ElementTree Node
        Root node of the object to deserialize.
    cache : dict
        Dictionary to use as cache.

    Returns
    -------
    obj
        Deserialized object instance.
    """
    
    obj_id = uuid.UUID(node.get("id"))
    class_name = node.get("class")

    if obj_id == None or class_name == None:
        return None

    obj = None
    stub = node.get("stub")
    if stub == "yes":
        assert cache != None, "When stubs are present, cache is required."
        obj = cache.get(obj_id)

    if obj == None:
        klass = get_class_by_name(class_name)
        obj = klass()
        obj.id = obj_id

        if cache != None:
            cache[obj_id] = obj

        for element in node:
            value = parse_value_element(element, cache=cache)
            setattr(obj, element.tag, value)

    return obj

def get_class_by_name(class_name):
    """
    Get a class using the fully qualified name.
    
    Parameters
    ----------
    class_name : string
        Fully qualified name of the class.
        
    Returns
    -------
    klass
        Class object matching the name.
    """
    parts = class_name.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def add_element(tag_name, text=None, parent=None, type_name=None):
    """
    Add a new element with the given name to the XML document as a child of the given parent.
    
    Parameters
    ----------
    tag_name : string
        Name of the tag to add.
    text : string
        Text node to add to the element. None if no text node should be created.
    parent : ElementTree Node
        Node to add the new element in.
    type_name : string
        Type to include in the type attribute of the new element. None to skip.
    
    Returns
    -------
    node : ElementTree Node
        The newly created node.
    """

    node = None
    if parent == None:
        node = et.Element(tag_name)
    else:
        node = et.SubElement(parent, tag_name)

    if text != None:
        node.text = text

    if type_name != None:
        node.set("type", type_name)

    return node

def add_value_element(value, parent=None, tag_name="value", cache=None):
    """
    Add a value inside an element. Use the correct way to serialize built-in
    types, library types or serializable types. 
    
    Parameters
    ----------
    value
        Value to add inside the element.
    parent : ElementTree Node
        Node to add the element to. Can be None.
    tag_name : string
        Name of the tag the value is encapsulated in.
    cache : dict
        Dictionary to use as cache.
    
    Returns
    -------
    node : ElementTree Node
        The newly created node.
    """
    
    if isinstance(value, ignored_types):
        print("Warning: value type cannot be serialized: %s. Ignoring value." % value.__class__)
        return None
    

    if hasattr(value, "__serialize__"):

        return serialize_instance(value, parent, tag_name, cache=cache)

    elif isinstance(value, dict):

        return serialize_dict(parent=parent, value=value, tag_name=tag_name, cache=cache)
        
    elif isinstance(value, list) or isinstance(value, tuple):

        return serialize_list_or_tuple(parent=parent, values=value, tag_name=tag_name, cache=cache)
        
    elif value.__class__ in value_serializers_by_klass:
        (string, type_name) = get_serialized_value(value)

        return add_element(tag_name, string, parent, type_name)

    elif hasattr(value, "__dict__"):

        return serialize_instance(value, parent, tag_name, cache=cache)

    else:

        return add_element(tag_name, None, parent, None)

def parse_value_element(node, cache=None):
    """
    Parse an element and based on the type call the correct deserializer.
    
    Parameters
    ----------
    node : ElementTree Node
        Node from which the value should be extracted.
        
    Returns
    -------
    obj
        The object contain within the node.
    """
    type_name = node.get("type")

    if type_name == None or type_name == "NoneType":
        return None

    if type_name == "instance":
        return deserialize_instance(node, cache=cache)

    if type_name == "dict":
        return deserialize_dict(node, cache=cache)

    if type_name == "list" or type_name == "tuple":
        return deserialize_list_or_tuple(node, cache=cache)

    if not type_name in value_serializers_by_klass_name:
        return None

    ser = value_serializers_by_klass_name[type_name]
    return ser.deserialize(node.text)


value_serializers_by_klass = {}
"""
Dictionary of registered value serializers by class. Key is the corresponding class object.
"""

value_serializers_by_klass_name = {}
"""
Dictionary of registered value serializers by class name.
"""

def get_serialized_value(value):
    """
    Serialize the given value using a value serializer.
    If no serializer is present, the value is serialized as None.
    
    Parameters
    ----------
    value
        Value to serialize.
    
    Returns
    -------
    serial_value : string
        The serialized value.
    type_name : string
        Name of the serialized type.
    """
    
    if value == None:
        return (None, None)
    
    if not value.__class__ in value_serializers_by_klass:
        return (None, None)
    
    ser = value_serializers_by_klass[value.__class__]
    return (ser.serialize(value), ser.klass_name)


def add_value_serializer(ser):
    """
    Add a value serializer to the list of available serializers.
    
    Parameters
    ----------
    ser : :class:`ValueSerializer`
        Value serializer to add.
    """
    value_serializers_by_klass[ser.klass] = ser
    value_serializers_by_klass_name[ser.klass_name] = ser

class ValueSerializer(object):
    """
    Object for serializing a type of object containing only a single value. The
    value should be serialized into a single string that is stored in a single
    element.
    
    Instantiate your custom version of this class to add unsupported data types.
    
    Parameters
    ----------
    klass : type
        Class object this serializer will handle.
    serialize_method : callable object
        Method or other callable object that accepts a value to serialize and
        returns the serialized string.
    deserialize_method : callable object
        Method or other callable object that accepts a string and returns the
        contained value.
    klass_name : string
        Name of the value class. If omitted the name is extracted from the 
        klass parameter.
    
    """

    def __init__(self, klass, serialize_method, deserialize_method, klass_name=None):
        self._klass = klass
        self._serialize_method = serialize_method
        self._deserialize_method = deserialize_method

        if klass_name:
            self._klass_name = klass_name
        else:
            if klass.__module__ == "__builtin__":
                self._klass_name = klass.__name__
            else:
                self._klass_name = "%s.%s" % (klass.__module__, klass.__name__)

    @property
    def klass(self):
        """
        Class type this serializer handles.
        """
        return self._klass
    
    @property
    def klass_name(self):
        """
        Name of the class this serializer handles.
        """
        return self._klass_name

    def serialize(self, value):
        """
        Serialize the value into string format.
        
        Parameters
        ----------
        value
            Object to serialize.
            
        Returns
        -------
        string
            Serialized object.
        """
        return self._serialize_method(value)

    def deserialize(self, string):
        """
        Deserialize the given string.
        
        Parameters
        ----------
        string : string
            Serialized object.
            
        Returns
        -------
        value
            Value present in the serialized string.
        """
        return self._deserialize_method(string)

# Already included value serializers. Mostly for builtin python data types.
_int_serializer = ValueSerializer(int, str, int)
_string_serializer = ValueSerializer(str, lambda x: x, lambda x: x)
_float_serializer = ValueSerializer(float, str, float)
_uuid_serializer = ValueSerializer(uuid.UUID, lambda x: x.urn, uuid.UUID, klass_name="uuid")
_bool_serializer = ValueSerializer(bool, str, lambda x: x == "True")

add_value_serializer(_int_serializer)
add_value_serializer(_string_serializer)
add_value_serializer(_float_serializer)
add_value_serializer(_uuid_serializer)
add_value_serializer(_bool_serializer)

