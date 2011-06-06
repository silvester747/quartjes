
__author__="Rob van der Most"
__date__ ="$Jun 6, 2011 7:14:58 PM$"

'''
Assorted class utilities and tools

Created on May 5, 2011

@author: Rob van der Most
'''

class AttrDisplay(object):
    """
    Provides an inheritable print overload method that displays
    instances with their class names and a name=value pair for
    each attribute stored on the instance itself (but not attrs
    inherited from its classes). Can be mixed into any class,
    and will work on any instance.
    """

    def gatherAttrs(self):
        attrs = []
        for key in sorted(self.__dict__):
            attrs.append('%s=%s' % (key, getattr(self, key)))
        return ', '.join(attrs)

    def __str__(self):
        return '[%s: %s]' % (self.__class__.__name__, self.gatherAttrs())
