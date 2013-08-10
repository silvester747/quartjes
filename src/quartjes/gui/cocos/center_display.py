"""
Main display area of the screen.
"""

from cocos.actions import CallFunc, Delay, MoveTo
import cocos.layer
import time

from quartjes.gui.cocos.basenodes import LabelBatch, UpdatableNode
import quartjes.gui.cocos.history_graph as history_graph
import quartjes.gui.cocos.mix_drawer as mix_drawer
from quartjes.models.drink import Mix

debug_mode = False

class CenterLayer(cocos.layer.base_layers.Layer):
    """
    Center part of the screen, handling display of the main content.
    
    Current content:
    - Display the drink or mix currently centered on the bottom ticker;
    - Display instructions on demand;
    
    TODO: Currently anchoring of content is bottom-left, change to center.
    
    Parameters
    ----------
    move_time : float
        Time in seconds to move an object in and out of the screen.
    explanation_time : float
        Minimum time in seconds to display the explanation.
    """

    def __init__(self, 
                 top=150, 
                 content_width=940, 
                 content_height=500,
                 screen_width=1024, 
                 move_time=1.0, 
                 explanation_time=10.0):
        """
        Initialize the drink layer.
        """
        super(CenterLayer, self).__init__()

        self._top = top
        self._content_width = content_width
        self._content_height = content_height
        self._screen_width = screen_width
        self._move_time = move_time
        self._explanation_time = explanation_time

        self._points = []
        self._points.append((screen_width + (content_width / 2), top))
        self._points.append((screen_width / 2, top))
        self._points.append((0 - (content_width / 2), top))

        # Current node on display
        self._current_node = None
        
        # Last drink for which a display was instantiated.
        self._current_drink = None
        
        # Contains details to construct a new node. None when nothing scheduled.
        self._next_node = None
        
        # Has a clear request been issued?
        self._clear = False
        
        self._lock_expires = 0

    def schedule_next_node(self, node_type, pargs=(), kwargs={}, min_display_time=None, in_place=False, drink=None):
        '''
        Schedule a node for display. The node will be instantiated in the render thread. 
        
        No queueing!
        If display is still locked due to another element with `min_display_time` the request is ignored.
        Also multiple calls without a render pass in between, will result in only the last request being honored.
        
        Parameters
        ----------
        node_type
            Callable that returns the node to display (usually the class).
        pargs : list
            Positional arguments to pass to `node_type`.
        kwargs : dict
            Keyword arguments to pass to `node_type`.
        min_display_time
            Minimum time in seconds to display the node.
        in_place
            True if node should be replaced on current node location. False if it should be
            brought in as a new node.
        
        Returns
        -------
        scheduled
            True if the node is scheduled. False if display is still locked.
        '''
        if time.time() < self._lock_expires:
            if debug_mode:
                print('Display still locked, ignoring next node')
            return False
        
        self._next_node = (node_type, pargs, kwargs, min_display_time, in_place, drink)

    def show_drink(self, drink):
        """
        Change the drink currently being shown.
        """
        if not drink:
            if self._current_drink:
                self.clear()
                self._current_drink = None
            return
        
        if isinstance(drink, Mix):
            node_type = MixDisplay
        else:
            node_type = DrinkHistoryDisplay
        
        if self._current_drink and self._current_drink.id == drink.id:
            self.schedule_next_node(node_type, pargs=(drink, self._content_width, self._content_height), in_place=True, drink=drink)
        else:
            self.schedule_next_node(node_type, pargs=(drink, self._content_width, self._content_height), in_place=False, drink=drink)
        
    def show_explanation(self, display_time=None):
        '''
        Show an explanation of the game.
        '''
        if not display_time:
            display_time = self._explanation_time
        self.schedule_next_node(Explanation, (self._content_height,), min_display_time=display_time)
    
    def clear(self):
        '''
        Clear the display, removes the current content, even if it is locked
        '''
        self._clear = True

    def draw(self, *args, **kwargs):
        """
        Called by Cocos2D. Performs actions on next render loop.
        """
        locked = time.time() < self._lock_expires
        
        if self._clear:
            self._replace_node(None)
            self._clear = False
            self._lock_expires = 0
        
        if self._next_node and not locked:
            node_type, pargs, kwargs, min_display_time, in_place, drink = self._next_node
            self._next_node = None
            
            try:
                next_node = node_type(*pargs, **kwargs)
            except:
                print('Failed to instantiate next node')
                print('\tNode type: %s' % node_type)
                print('\tPargs:     %s' % pargs)
                print('\tKwargs:    %s' % kwargs)
                print('Stacktrace:')
                import traceback
                traceback.print_exc()
            else:
                if min_display_time:
                    self._lock_expires = time.time() + min_display_time

                if in_place:
                    if debug_mode:
                        print('Doing in place update')
                    self._update_node(next_node)
                else:
                    if debug_mode:
                        print('Doing full update')
                    self._replace_node(next_node)
                
                if drink:
                    self._current_drink = drink


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
            self._current_node.do(MoveTo(self._points[2], 0.5 * self._move_time) +
                                 CallFunc(self._current_node.kill))

        self._current_node = UpdatableNode(new_node, self._points[0])

        self._current_node.do(Delay(0.5 * self._move_time) +
                              MoveTo(self._points[1], 0.5 * self._move_time))
        self.add(self._current_node)
        
    def _update_node(self, new_contents):
        """
        Replace the contents of the current displayed node.
        """
        if self._current_node:
            self._current_node.update(new_contents)
    


class Explanation(LabelBatch):
    '''
    Display an explanation of the game.
    '''
    
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
                          position = (center_x, y))
            
            y -= 70

class MixDisplay(LabelBatch):
    '''
    Display the contents of a mix drink.
    '''
    def __init__(self, mix, width, height):
        LabelBatch.__init__(self)
        
        font = 'Times New Roman'
        center_x = 0
        max_y = height

        self.add_text(mix.name,
                      font_name=font,
                      font_size=64,
                      anchor_x='center', anchor_y='top',
                      position = (center_x, max_y))

        self.add_text("Alcohol: %2.1f %%" % mix.alc_perc,
                      font_name=font,
                      font_size=20,
                      anchor_x='center', anchor_y='top',
                      position = (center_x, max_y - 100))

        y = max_y - 150
        y_spacing = y / len(mix.drinks)
        y -= y_spacing / 2
        for d in mix.drinks:
            self.add_text(d.name,
                          font_name=font,
                          font_size=20,
                          anchor_x='center', anchor_y='top',
                          position = (center_x, y))
            y -= y_spacing

        self.add_text("%d" % mix.current_price_quartjes,
                      font_name=font,
                      font_size=150,
                      anchor_x='center', anchor_y='center',
                      position = (center_x + 300, (max_y - 150) / 2))

        image=mix_drawer.create_mix_drawing(height=max_y-150, width=200, mix=mix)
        mix_drawing = cocos.sprite.Sprite(image=image,
                                          position=(center_x - 300, (max_y - 150) / 2),
                                          anchor=(100, (max_y - 150) / 2))
        self.add(mix_drawing)

class DrinkHistoryDisplay(cocos.sprite.Sprite):
    '''
    Display the historic prices for a drink.
    '''
    def __init__(self, drink, width, height):
        graph = history_graph.create_pyglet_image(drink, width, height)
        cocos.sprite.Sprite.__init__(self, image=graph, anchor=(width / 2, 0))
