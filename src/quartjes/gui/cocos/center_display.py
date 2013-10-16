"""
Main display area of the screen.
"""

from cocos.actions import CallFunc, Delay, MoveTo
import cocos.layer
import time
from threading import Timer

from quartjes.gui.cocos.basenodes import LabelBatch, UpdatableNode, SimpleNodeConstructor
from quartjes.gui.cocos.basenodes import ThreadedNodeConstructor
import quartjes.gui.cocos.history_graph as history_graph
import quartjes.gui.cocos.mix_drawer as mix_drawer
from quartjes.models.drink import Mix

debug_mode = True


class CenterDisplayController(object):
    """
    Control the content displayed on the center layer.
    
    Parameters
    ----------
    explanation_interval : int
        Time after which an explanation should be shown.
    """
    def __init__(self, explanation_interval=300):
        
        self._explanation_interval = explanation_interval
        
        # Time to back off if the display is locked while explanation should be shown
        self._explanation_locked_backoff = 10
        
        # Timer for showing the explanation
        self._explanation_timer = None
        
        # Currently displayed drink
        self._current_drink = None
        
        # Layer used for display
        self._layer = None
        
        # If the display is locked, time the lock expires
        self._lock_expires = 0
    
    def stop(self):
        """
        Stop the controller.
        """
        if self._explanation_timer:
            self._explanation_timer.cancel()
    
    @property
    def locked(self):
        """
        Is the display currently locked by a node with minimum display time?
        """
        return time.time() < self._lock_expires
    
    def _set_lock(self, lock_time):
        """
        Lock the screen on the current node for `lock_time` seconds.
        """
        self._lock_expires = time.time() + lock_time
        
        if debug_mode:
            print("Lock set for %f seconds" % lock_time)
    
    def drink_focussed(self, drink):
        """
        Handle new drink in focus.
        """
        if not self.locked and self._layer:
            if not drink and self._current_drink:
                self._layer.clear()
                self._current_drink = None
                if debug_mode:
                    print("drink_focussed: Drink cleared")
            elif drink:
                in_place = False
                if self._current_drink:
                    in_place = self._current_drink.id == drink.id
                self._layer.show_drink(drink, in_place)
                self._current_drink = drink
                if debug_mode:
                    print("drink_focussed: Display drink %s" % repr(drink))
        elif debug_mode:
            print("drink_focussed: Display locked or not active")

    def show_explanation(self, display_time=10.0):
        """
        Show the explanation.
        """
        if not self.locked and self._layer:
            self._layer.show_explanation()
            self._set_lock(display_time)
            self._current_drink = None
            self._explanation_timer = Timer(self._explanation_interval, self.show_explanation)
            self._explanation_timer.start()
            print('show_explanation: Explanation activated')
        elif self._layer:
            if debug_mode:
                print('show_explanation: Display locked, start backoff timer')
            self._explanation_timer = Timer(self._explanation_locked_backoff, self.show_explanation)
            self._explanation_timer.start()
        else:
            if debug_mode:
                print('show_explanation: Display not active')
            
    def get_layer(self):
        """
        Get the layer for display.
        """
        if not self._layer:
            self._layer = CenterLayer()
            if debug_mode:
                print('get_layer: Layer activated')
            self.show_explanation()
        return self._layer


class CenterLayer(cocos.layer.base_layers.Layer):
    """
    Center part of the screen, handling display of the main content.
    
    Current content:
    - Display the drink or mix currently centered on the bottom ticker;
    - Display instructions on demand;
    
    Added nodes are expected to anchor at the bottom-center. Their sizes should
    respect the passed content sizes.
    
    Parameters
    ----------
    top_margin : int
        Margin on top of the screen.
    bottom_margin : int
        Margin at the bottom of the screen.
    left_margin : int
        Margin at the left side of the screen.
    right_margin : int
        Margin at the right side of the screen.
    move_time : float
        Time in seconds to move an object in and out of the screen.
    """

    def __init__(self, 
                 top_margin=100,
                 bottom_margin=150,
                 left_margin=50,
                 right_margin=50,
                 move_time=1.0):
        """
        Initialize the drink layer.
        """
        super(CenterLayer, self).__init__()

        self._top_margin = top_margin
        self._bottom_margin = bottom_margin
        self._left_margin = left_margin
        self._right_margin = right_margin
        
        self._screen_width, self._screen_height = cocos.director.director.get_window_size()

        self._content_width = self._screen_width - self._left_margin - self._right_margin
        self._content_height = self._screen_height - self._top_margin - self._bottom_margin
        
        self._point_offscreen_right = (self._screen_width + (self._content_width / 2), self._bottom_margin)
        self._point_offscreen_left = (0 - (self._content_width / 2), self._bottom_margin)
        self._point_onscreen = (self._screen_width / 2, self._bottom_margin)
        
        self._move_time = move_time

        # Current node on display
        self._current_node = None
        
        # Contains details to construct a new node. None when nothing scheduled.
        self._next_node = None
        
        # Has a clear request been issued?
        self._clear = False
        
    def schedule_next_node(self, node_constructor, in_place=False):
        """
        Schedule a node for display. The node will be instantiated in the render thread. 
        
        No queueing!
        Multiple calls without a render pass in between, will result in only the last request being honored.
        
        Parameters
        ----------
        node_constructor
            Constructor for the next node.
        in_place
            True if node should be replaced on current node location. False if it should be
            brought in as a new node.
        """
        self._next_node = (node_constructor, in_place)

    def show_drink(self, drink, in_place=False):
        """
        Change the drink currently being shown.
        """
        if isinstance(drink, Mix):
            node_type = MixDisplayConstructor
        else:
            node_type = DrinkHistoryDisplayConstructor

        node_constructor = node_type(drink, self._content_width, self._content_height)

        self.schedule_next_node(node_constructor,
                                in_place=in_place)
        
    def show_explanation(self):
        """
        Show an explanation of the game.
        """
        self.schedule_next_node(ExplanationConstructor(self._content_height))
    
    def clear(self):
        """
        Clear the display, removes the current content, even if it is locked
        """
        self._clear = True

    def draw(self, *args, **kwargs):
        """
        Called by Cocos2D. Performs actions on next render loop.
        """
        if self._clear:
            self._replace_node(None)
            self._clear = False
        
        if self._next_node:
            node_constructor, in_place = self._next_node
            if node_constructor.ready:
                self._next_node = None

                if in_place:
                    if debug_mode:
                        print('Doing in place update')
                    self._update_node(node_constructor.get_node())
                else:
                    if debug_mode:
                        print('Doing full update')
                    self._replace_node(node_constructor.get_node())

    def _replace_node(self, new_node):
        """
        Move a new node into display, slow animation.
        """
        if not self.is_running:
            if debug_mode:
                print("Not running")
            if self._current_node:
                self._current_node.kill()
                self._current_node = None

            return

        if self._current_node:
            self._current_node.do(MoveTo(self._point_offscreen_left, 0.5 * self._move_time) +
                                  CallFunc(self._current_node.kill))

        self._current_node = UpdatableNode(new_node, self._point_offscreen_right)

        self._current_node.do(Delay(0.5 * self._move_time) +
                              MoveTo(self._point_onscreen, 0.5 * self._move_time))
        self.add(self._current_node)
        
    def _update_node(self, new_contents):
        """
        Replace the contents of the current displayed node.
        """
        if self._current_node:
            self._current_node.update(new_contents)
    

class Explanation(LabelBatch):
    """
    Display an explanation of the game.
    """
    
    text = ("Let op!",
            "",
            "Op Quartjesavond kan alleen met",
            "10 eurocent munten betaald worden.",
            "Alle prijzen zijn zoals het systeem",
            "weergeeft in eenheden van 10 eurocent.")
    font = 'Times New Roman'
    
    def __init__(self, height):
        LabelBatch.__init__(self)
        
        center_x = 0
        max_y = height
        y = max_y - 50

        for line in Explanation.text:
            self.add_text(line,
                          font_name=Explanation.font,
                          font_size=40,
                          anchor_x='center', anchor_y='top',
                          position=(center_x, y))
            
            y -= 70


class ExplanationConstructor(SimpleNodeConstructor):
    """
    Constructor for the explanation node.
    """
    node_type = Explanation


class MixDisplayConstructor(ThreadedNodeConstructor):
    """
    Construct the node to display a mix.
    """
    def __init__(self, drink, width, height):
        self.__drink = drink
        self.__width = width
        self.__height = height

        self.__mix_image = None

        ThreadedNodeConstructor.__init__(self)

    def _construct_node(self):
        node = LabelBatch()

        font = 'Times New Roman'
        center_x = 0
        max_y = self.__height

        node.add_text(self.__drink.name,
                      font_name=font,
                      font_size=64,
                      anchor_x='center', anchor_y='top',
                      position=(center_x, max_y))

        node.add_text("Alcohol: %2.1f %%" % self.__drink.alc_perc,
                      font_name=font,
                      font_size=20,
                      anchor_x='center', anchor_y='top',
                      position=(center_x, max_y - 100))

        y = max_y - 150
        y_spacing = y / len(self.__drink.drinks)
        y -= y_spacing / 2
        for d in self.__drink.drinks:
            node.add_text(d.name,
                          font_name=font,
                          font_size=20,
                          anchor_x='center', anchor_y='top',
                          position=(center_x, y))
            y -= y_spacing

        node.add_text("%d" % self.__drink.current_price_quartjes,
                      font_name=font,
                      font_size=150,
                      anchor_x='center', anchor_y='center',
                      position=(center_x + 300, (max_y - 150) / 2))

        mix_drawing = cocos.sprite.Sprite(image=self.__mix_image,
                                          position=(center_x - 300, (max_y - 150) / 2),
                                          anchor=(100, (max_y - 150) / 2))
        node.add(mix_drawing)

        return node

    def _pre_construct(self):
        """
        Construct the mix drink image.
        """
        self.__mix_image = mix_drawer.create_mix_drawing(height=self.__height-150,
                                                         width=200,
                                                         mix=self.__drink)

class DrinkHistoryDisplayConstructor(ThreadedNodeConstructor):
    """
    Construct the node to display historic prices for a drink.
    """
    def __init__(self, drink, width, height):
        self.__drink = drink
        self.__width = width
        self.__height = height

        self.__graph = None

        ThreadedNodeConstructor.__init__(self)

    def _construct_node(self):
        return cocos.sprite.Sprite(image=self.__graph,
                                   anchor=(self.__width / 2, 0))

    def _pre_construct(self):
        """
        Construct the graph to display.
        """
        self.__graph = history_graph.create_pyglet_image(self.__drink,
                                                         self.__width,
                                                         self.__height)

