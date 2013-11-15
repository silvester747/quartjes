"""
Ticker modules for displaying current drink prices.
"""

from axel import Event
from cocos.actions import CallFunc, Delay, FadeIn, FadeOut, MoveTo, ScaleTo
import cocos.cocosnode
import cocos.layer
import cocos.text
import pyglet

debug_mode = True


class BottomTicker(cocos.layer.Layer):
    """
    Layer containing a ticker of drinks.
    The list of drinks scrolls from the right of the screen to the left. In the
    middle one of the drinks will gain focus and is shown larger.
    """

    def __init__(self, screen_width=1024, drinks=None):
        """
        Initialize the ticker.
        """
        super(BottomTicker, self).__init__()

        # Scroll speed in pixels/second
        self._scroll_speed = 80.0
        
        # Y coordinate of the normal ticker. Measured from the bottom of the text labels.
        self._ticker_y = 0
        
        # Y coordinate of the focus ticker. Measured from the bottom of the text labels.
        self._focus_y = 45
        
        # Percentage of the path the drink has focus.
        self._focus_length = 0.2
        
        # Percentage of the path for the center of the focus.
        self._focus_center = 0.5
        
        # Percentage of the path used to ramp up or down to focus.
        self._focus_ramp = 0.1
        
        # Width of the screen. This width is used to calculate the path the items
        # in the ticker follow.
        self._screen_width = screen_width
        
        # Distance in pixels between drinks
        self._drink_distance = 40

        # Path followed by the ticker elements. Each item is a tuple containing the coordinates and the time required to
        # reach those coordinates.
        self._path = []

        # List of _drinks to show on the ticker
        self._drinks = drinks

        # Index of the drink last added to the ticker
        self._current_drink_index = 0
        
        # Drink currently having focus.
        self.focused_drink = None

        # Event fired when the currently focused drink has changed. Listeners
        # should have the following signature:
        # drink
        #     The drink that is focused.
        # is_new
        #     True if this is a new drink, False if the drink itself was updated.
        self.on_focused_drink_changed = Event()
        
        # Add background layers
        background_layer = cocos.layer.ColorLayer(255, 128, 0, 200, width=screen_width, height=45)
        self.add(background_layer)
        
        background_layer = cocos.layer.ColorLayer(255, 128, 0, 100, width=screen_width, height=90)
        background_layer.position = (0, 45)
        self.add(background_layer)
        
        # Start ticking
        self._calculate_path()
        self._next_drink()

    def _calculate_path(self):
        """
        Prepare the ticker by calculating all points on the path.
        """
        
        self._path = []
        
        # Starting point (time is 0, this needs to be set for each element)
        x = self._screen_width
        y = self._ticker_y
        time = 0
        self._path.append([(x, y), time])  # this one is a list to be able to change the time
        
        # Just before ramp up
        prev_x = x
        x = (self._focus_center + (self._focus_length / 2) + self._focus_ramp) * self._screen_width
        y = self._ticker_y
        distance = prev_x - x
        time = distance / self._scroll_speed
        self._path.append(((x, y), time))
        
        # Start of focus
        prev_x = x
        x = (self._focus_center + (self._focus_length / 2)) * self._screen_width
        y = self._focus_y
        distance = prev_x - x
        time = distance / self._scroll_speed
        self._path.append(((x, y), time))

        # End of focus
        prev_x = x
        x = (self._focus_center - (self._focus_length / 2)) * self._screen_width
        y = self._focus_y
        distance = prev_x - x
        time = distance / self._scroll_speed
        self._path.append(((x, y), time))
        
        # End of ramp
        prev_x = x
        x = (self._focus_center - (self._focus_length / 2) - self._focus_ramp) * self._screen_width
        y = self._ticker_y
        distance = prev_x - x
        time = distance / self._scroll_speed
        self._path.append(((x, y), time))
        
        # End of screen
        prev_x = x
        x = 0
        y = self._ticker_y
        distance = prev_x - x
        time = distance / self._scroll_speed
        self._path.append(((x, y), time))
        
    def _add_animation(self, node, drink):
        """
        Construct an animation path for the label.
        """
        node.scale = 0.5
        
        content_offset = (node.scale * node.label.element.content_width + self._drink_distance) / 2
        
        # Make sure only one item has focus
        minimum_offset = ((self._focus_length + self._focus_ramp) * self._screen_width) / 2
        if content_offset < minimum_offset:
            content_offset = minimum_offset
        
        content_time = float(content_offset) / self._scroll_speed
        
        # Set start position
        node.position = (self._screen_width + content_offset, self._ticker_y)
        
        # Construct the path
        # Move to beginning of screen
        (coordinates, _) = self._path[0]
        move_actions = MoveTo(coordinates, content_time)
        
        # Move to ramp up    
        (coordinates, time) = self._path[1]
        move_actions += MoveTo(coordinates, time)
        
        # Do the ramp
        (coordinates, time) = self._path[2]
        move_actions += (MoveTo(coordinates, time) | (Delay(time / 2) + ScaleTo(1, time / 2)) 
                         | CallFunc(self._set_focused_drink, drink))

        # Move in focus
        (coordinates, time) = self._path[3]
        move_actions += MoveTo(coordinates, time) 
        
        # Ramp down
        (coordinates, time) = self._path[4]
        move_actions += MoveTo(coordinates, time) | (ScaleTo(0.5, time / 2))
        
        # Move to end of screen
        (coordinates, time) = self._path[5]
        move_actions += MoveTo(coordinates, time)
        
        # Move out of sight
        move_actions += MoveTo((0 - content_offset, self._ticker_y), content_time)
        
        # Prepare spawn point
        spawn_actions = Delay(content_time * 2) + CallFunc(self._next_drink)
        self.do(spawn_actions)
        
        # Start animation
        node.do(move_actions + CallFunc(self._safe_kill, node))

    def update_drinks(self, drinks):
        """
        Update the drinks in the ticker. Visible drinks are directly updated.
        """
        if debug_mode:
            print("Receiving update")
        cur_drink = self._current_drink_index
        if cur_drink >= len(drinks):
            cur_drink = 0
        self._drinks, self._current_drink_index = drinks, cur_drink
        
        pyglet.clock.schedule_once(self._update_visible_drinks, 0)
       
    def _update_visible_drinks(self, dt):
        nodes = self.get_children()
    
        for node in nodes:
            if isinstance(node, TickerDrinkNode):
                if node.drink is None:
                    continue
                for drink in self._drinks:
                    if drink.id == node.drink.id:
                        node.update_drink(drink)
                        break
                else:
                    # No longer present
                    node.hide()
        
        self._set_focused_drink(self.focused_drink)

    @staticmethod
    def _safe_kill(child):
        """
        Safely remove a node from the tree.
        """
        try:
            child.kill()
        except:
            pass

    def _set_focused_drink(self, drink):
        """
        Update the currently focused drink and notify all listeners.
        """
        # Keep track whether this is an update to the current focused drink or a change of focus
        if not drink or not self.focused_drink:
            is_new = True
        else:
            is_new = drink.id != self.focused_drink.id

        # Make sure we have the latest instance
        if not drink is None:
            for tmp_drink in self._drinks:
                if tmp_drink.id == drink.id:
                    drink = tmp_drink
                    break
            else:
                drink = None

        if debug_mode:
            print('Set %s drink: %s' % ('new' if is_new else 'updated',
                                        drink.name if drink else 'None'))

        self.focused_drink = drink
        self.on_focused_drink_changed(drink, is_new)

    def _next_drink(self):
        """
        Prepare the next drink on the list to be shown on screen.
        """
        drink = None

        if self._drinks:
            self._current_drink_index += 1
            if self._current_drink_index >= len(self._drinks):
                self._current_drink_index = 0
            drink = self._drinks[self._current_drink_index]

        drink_node = TickerDrinkNode(drink)
        self.add(drink_node)
        self._add_animation(drink_node, drink)


class TickerDrinkNode(cocos.cocosnode.CocosNode):
    """
    Cocos node representing a drink on the ticker.
    """
    
    def __init__(self, drink):
        super(TickerDrinkNode, self).__init__()

        self.label = None
        self.drink = drink
        self._next_z_level = 1
        self._set_label()
        
    def _set_label(self):
        if self.drink is None:
            text = ""
        else:
            text = "%s - %d" % (self.drink.name, self.drink.current_price_quartjes)
            
        self.label = cocos.text.Label(text,
                                      font_name='Times New Roman',
                                      font_size=64,
                                      anchor_x='center', anchor_y='bottom')
        self.add(self.label, z=self._next_z_level)
        self._next_z_level += 1
    
    def update_drink(self, drink):
        """
        Update the drink shown.
        """
        self.label.do(FadeOut(1))
        self.drink = drink
        self._set_label()
        self.label.do(FadeIn(1))
    
    def hide(self):
        self.label.do(FadeOut(1))
