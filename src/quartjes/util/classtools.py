
__author__="Rob van der Most"
__date__ ="$Jun 6, 2011 7:14:58 PM$"

'''
Assorted class utilities and tools

Created on May 5, 2011

@author: Rob van der Most
'''

import uuid
from pprint import pformat

class AttrDisplay(object):
    """
    Provides an inheritable print overload method that displays
    instances with their class names and a name=value pair for
    each attribute stored on the instance itself (but not attrs
    inherited from its classes). Can be mixed into any class,
    and will work on any instance.
    """
    def __str__(self):
        return '%s: \n %s' % (self.__class__.__name__, pformat(vars(self)))

class QuartjesBaseClass(AttrDisplay):
    """
    Base class for all objects in quartjes that are serialized. Deriving from
    this class does not automatically make your objects serializable, but at
    least a unique id is present.
    """

    def __init__(self, id=None):
        """
        Default constructor. Accepts an id to store. If no id is given, a new
        unique id is created.
        """
        if id == None:
            self.id = uuid.uuid4()
        else:
            self.id = id

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not other:
            return False
        return vars(self) == vars(other)

    def __ne__(self, other):
        if not other:
            return True
        return vars(self) != vars(other)

def trace(method):
    def on_call(*args, **kwargs):
        mylevel = trace.level
        trace.level = trace.level + 1
        print("%sMethod %s called with args=%s and kwargs=%s" % ("." * mylevel, method.__name__, args, kwargs))
        result = method(*args, **kwargs)
        print("%sMethod %s returned: %s" % ("." * mylevel, method.__name__, result))
        trace.level = trace.level - 1
        return result
    return on_call
trace.level = 0