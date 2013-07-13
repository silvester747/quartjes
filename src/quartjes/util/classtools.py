
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

    def __init__(self, id_=None):
        """
        Default constructor. Accepts an id to store. If no id is given, a new
        unique id is created.
        """
        if id_ == None:
            self.id = uuid.uuid4()
        else:
            self.id = id_

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

from functools import wraps

def cached_class(klass):
    """Decorator to cache class instances by constructor arguments.
    
    We "tuple-ize" the keyword arguments dictionary since
    dicts are mutable; keywords themselves are strings and
    so are always hashable, but if any arguments (keyword
    or positional) are non-hashable, that set of arguments
    is not cached.
    """
    cache = {}
    
    @wraps(klass, assigned=('__name__', '__module__'), updated=())
    class _decorated(klass):
        # The wraps decorator can't do this because __doc__
        # isn't writable once the class is created
        __doc__ = klass.__doc__
        def __new__(cls, *args, **kwds):
            key = (cls,) + args + tuple(kwds.iteritems())
            try:
                inst = cache.get(key, None)
            except TypeError:
                # Can't cache this set of arguments
                inst = key = None
            if inst is None:
                # Technically this is cheating, but it works,
                # and takes care of initializing the instance
                # (so we can override __init__ below safely);
                # calling up to klass.__new__ would be the
                # "official" way to create the instance, but
                # that raises DeprecationWarning if there are
                # args or kwds and klass does not override
                # __new__ (which most classes don't), because
                # object.__new__ takes no parameters (and in
                # Python 3 the warning will become an error)
                inst = klass(*args, **kwds)
                # This makes isinstance and issubclass work
                # properly
                inst.__class__ = cls
                if key is not None:
                    cache[key] = inst
            return inst
        def __init__(self, *args, **kwds):
            # This will be called every time __new__ is
            # called, so we skip initializing here and do
            # it only when the instance is created above
            pass
    
    return _decorated
