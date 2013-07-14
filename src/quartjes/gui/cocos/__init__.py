"""
GUI using Cocos2D
"""

import cocos
import pyglet
import re

# Do some version checks
pyglet_version = re.match(r"(\d+)\.(\d+)", pyglet.version)
if not pyglet_version:
    raise ImportError("Cannot determine Pyglet version!")
else:
    pyglet_major = int(pyglet_version.group(1))
    pyglet_minor = int(pyglet_version.group(2))
    
    if pyglet_major < 1 or (pyglet_major == 1 and pyglet_minor < 2):
        raise ImportError("Require Pyglet 1.2alpha or greater")
del pyglet_version

cocos_version = re.match(r"(\d+)\.(\d+)\.(\d+)", cocos.version)
if not cocos_version:
    raise ImportError("Cannot determine Cocos2d version!")
else:
    cocos_major = int(cocos_version.group(1))
    cocos_minor = int(cocos_version.group(2))
    cocos_build = int(cocos_version.group(3))
    
    if cocos_major == 0:
        if cocos_minor < 5:
            raise ImportError("Require Cocos2d 0.5.5 or greater")
        elif cocos_minor == 5 and cocos_build < 5:
            raise ImportError("Require Cocos2d 0.5.5 or greater")
del cocos_version

del cocos
del pyglet
del re