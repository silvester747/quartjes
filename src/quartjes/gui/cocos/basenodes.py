"""
Basic nodes used in different parts of the Cocos GUI.
"""

from abc import ABCMeta, abstractmethod, abstractproperty
import cocos
from cocos.actions import FadeIn, FadeOut
import pyglet
from pyglet.gl import glPushMatrix, glPopMatrix
from threading import Event, Thread


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
        self._group = None
        self._elements = []
        
        self._opacity = None

        if self.use_batch_rendering:
            self._batch = pyglet.graphics.Batch()
        else:
            self._batch = None

    @property
    def opacity(self):
        """
        Opacity of all elements contained. Returns None if not set explicitly.
        Note: if you directly set opacity on any of the contained objects, this will ignore that.
        """
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        for e in self._elements:
            e.color = tuple(e.color[:3]) + (int(value),)

    def add_text(self, text='', position=(0,0), **kwargs):
        """
        Add a text label to the batch.
        Accepts additional keyword arguments to pass on to a pyglet label.
        """
        kwargs['text']=text
        element = pyglet.text.Label(group=self._group, batch=self._batch,
                                    x=position[0], y=position[1], **kwargs)
        self._elements.append(element)

    def draw(self):
        """
        This is where the magic happens.
        Draw all labels in a single batch.
        """
        glPushMatrix()
        self.transform()
        if self._batch:
            self._batch.draw()
        else:
            for e in self._elements:
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
        self._inner_node.do(FadeOut(0.5))
        self._inner_node = new_node
        new_node.opacity = 0
        self.add(new_node, z=self._next_z_level)
        self._next_z_level += 1
        self._inner_node.do(FadeIn(0.5))
    
    def hide(self):
        self._inner_node.do(FadeOut(1))


class NodeConstructor(object):
    """
    Base class for node constructors. Prepares and returns a CocosNode
    for display. Might take time to prepare the node, so check the
    `ready` attribute first.

    Attributes
    ----------
    ready
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractproperty
    def ready(self):
        """
        Is the node ready for construction.
        """

    @abstractmethod
    def get_node(self):
        """
        Get the constructed node.

        Returns
        -------
        node
            The constructed CocosNode.
        """


class ThreadedNodeConstructor(Thread, NodeConstructor):
    """
    Constructs a node that requires more processing than should be
    performed in between render loops. First everything that can be
    constructed outside the renderer is constructed in a separate
    thread. When ready, the actual node can be constructed inside
    the render thread.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        Thread.__init__(self, name=self.__class__.__name__)
        NodeConstructor.__init__(self)
        self.daemon = True

        self.__ready = Event()

        self.start()

    def run(self):
        self._pre_construct()
        self.__ready.set()

    @property
    def ready(self):
        return self.__ready.is_set()

    @abstractmethod
    def _pre_construct(self):
        """
        Perform construction steps in a separate thread outside the render loop.
        """

    @abstractmethod
    def _construct_node(self):
        """
        Construct the CocosNode. Must run inside the render loop after the pre
        construct has finished.
        """

    def get_node(self):
        """
        Get the constructed node.
        Requires the pre construction to be finished. If not it will block until ready.

        Returns
        -------
        node
            The constructed CocosNode.
        """
        self.__ready.wait()
        return self._construct_node()


class SimpleNodeConstructor(NodeConstructor):
    """
    Most basic node constructor. Needs no pre construction, so always ready
    to go. Constructs node type given in class attribute using all arguments
    from the constructor.
    """

    node_type = None

    def __init__(self, *pargs, **kwargs):
        NodeConstructor.__init__(self)
        self.__pargs = pargs
        self.__kwargs = kwargs

    @property
    def ready(self):
        return True

    def get_node(self):
        try:
            return self.node_type(*self.__pargs, **self.__kwargs)
        except:
            print('Failed to instantiate next node')
            print('\tNode type: %s' % SimpleNodeConstructor.node_type)
            print('\tPargs:     %s' % self.__pargs)
            print('\tKwargs:    %s' % self.__kwargs)
            print('Stack trace:')
            import traceback
            traceback.print_exc()
