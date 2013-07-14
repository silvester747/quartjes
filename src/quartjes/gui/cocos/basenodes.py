"""
Basic nodes used in different parts of the Cocos GUI.
"""

import cocos
from cocos.actions import FadeOut
import pyglet
from pyglet.gl import glPushMatrix, glPopMatrix

class LabelBatch(cocos.cocosnode.CocosNode):
    """
    Special CocosNode to contain a number of text objects
    """

    use_batch_rendering = True

    def __init__(self, position=(0,0)):
        """
        Construct a label batch.
        """
        super(LabelBatch, self).__init__()
        self.position = position
        self.group = None
        self.elements = []

        if self.use_batch_rendering:
            self.batch = pyglet.graphics.Batch()
        else:
            self.batch = None

    def add_text(self, text='', position=(0,0), **kwargs):
        """
        Add a text label to the batch.
        Accepts additional keyword arguments to pass on to a pyglet label.
        """
        kwargs['text']=text
        element = pyglet.text.Label(group=self.group, batch=self.batch,
                                    x=position[0], y=position[1], **kwargs)
        self.elements.append(element)

    def draw(self):
        """
        This is where the magic happens.
        Draw all labels in a single batch.
        """
        glPushMatrix()
        self.transform()
        if self.batch:
            self.batch.draw()
        else:
            for e in self.elements:
                e.draw()
        glPopMatrix()


class UpdatableNode(cocos.cocosnode.CocosNode):
    """
    Cocos node with easy updatable content.
    """
    
    def __init__(self, inner_node, position=(0,0)):
        super(UpdatableNode, self).__init__()
    
        self.position = position    
        self._inner_node = inner_node
        self.add(inner_node, 0)
        self._next_z_level = 1
    
    def update(self, new_node):
        """
        Update the drink shown.
        """
        #self._inner_node.do(FadeOut(1))
        self._inner_node.kill()
        self._inner_node = new_node
        self.add(new_node, z=self._next_z_level)
        self._next_z_level += 1
        #self._inner_node.do(FadeIn(1))
    
    def hide(self):
        self._inner_node.do(FadeOut(1))

