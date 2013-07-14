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

class DrinkLayer(cocos.layer.base_layers.Layer):
    """
    Layer to display details on the currently focussed drink.
    In case a normal drink is focussed, the price graph is displayed.
    In case a mix drink is focussed, the details of the mix are displayed.
    
    Parameters
    ----------
    move_time : float
        Time in seconds to move an object in and out of the screen.
    explanation_time : float
        Minimum time in seconds to display the explanation.
    """

    def __init__(self, 
                 top=150, 
                 graph_width=940, 
                 graph_height=500,
                 screen_width=1024, 
                 move_time=1.0, 
                 explanation_time=10.0):
        """
        Initialize the drink layer.
        """
        super(DrinkLayer, self).__init__()

        self._top = top
        self._graph_width = graph_width
        self._graph_height = graph_height
        self._screen_width = screen_width
        self._move_time = move_time
        self._explanation_time = explanation_time

        self._points = []
        self._points.append((screen_width + (graph_width / 2), top))
        self._points.append((screen_width / 2, top))
        self._points.append((0 - (graph_width / 2), top))

        self._current_node = None
        self._current_drink = None
        
        self._explanation_active = False
        self._explanation_expires = 0

        self._next_drink = None
        self._clear_drink = False
        self._show_explanation = False

    def show_drink(self, drink):
        """
        Change the drink currently being shown.
        """
        self._next_drink = drink
        
    def clear_drink(self):
        """
        Clear the current selection
        """
        self._clear_drink = True
    
    def show_explanation(self):
        self._show_explanation = True

    def draw(self, *args, **kwargs):
        """
        Called by Cocos2D. Performs actions on next render loop.
        """
        
        if self._next_drink:
            if time.time() > self._explanation_expires:
                self._show_drink(self._next_drink)
            self._next_drink = None
            
        if self._clear_drink:
            if time.time() > self._explanation_expires:
                self._clear_drink = False
                self._replace_node(None)
                self._next_drink = None
                
        if self._show_explanation:
            self._clear_drink = False
            self._next_drink = None
            self._show_explanation = False
            
            self._explanation_expires = time.time() + self._explanation_time
            self._replace_node(self._get_explanation())
            

    def _show_drink(self, drink):
        """
        Replace the current drink with the next drink to display or update the
        details of the current drink if it is the same.
        """

        if drink:
            
            if isinstance(drink, Mix):
                new_node = self._get_mix(drink)
            else:
                new_node = self._get_drink_history(drink)
            
            if self._current_drink and self._current_drink.id == drink.id:
                self._update_node(new_node)
            else:
                self._replace_node(new_node)
            
            self._current_drink = drink
            
        else:
            self._replace_node(None)


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

        if not self._current_node:
            return

        self._current_node.do(Delay(0.5 * self._move_time) +
                              MoveTo(self._points[1], 0.5 * self._move_time))
        self.add(self._current_node)
        
    def _update_node(self, new_contents):
        """
        Replace the contents of the current displayed node.
        """
        if self._current_node:
            self._current_node.update(new_contents)
    
    def _get_explanation(self):
        """
        Construct a node with an explanation of the game.
        
        """
        
        text = ("Let op!",
                "",
                "Op Quartjesavond kan alleen met",
                "10 eurocent munten betaald worden.",
                "Alle prijzen zijn zoals het systeem",
                "weergeeft in eenheden van 10 eurocent.")
        
        font = 'Times New Roman'
        center_x = 0
        max_y = self._graph_height
        y = max_y - 50

        labels = LabelBatch()

        for line in text:
            labels.add_text(line,
                            font_name=font,
                            font_size=40,
                            anchor_x='center', anchor_y='top',
                            position = (center_x, y))
            
            y -= 70

        return labels


    def _get_drink_history(self, drink):
        """
        Construct a node to display the historic price graph for a drink.
        """

        graph = history_graph.create_pyglet_image(drink, self._graph_width, self._graph_height)

        node = cocos.sprite.Sprite(image = graph,
                                   anchor=(self._graph_width / 2, 0))

        return node

    def _get_mix(self, mix):
        """
        Construct a node to show a mix drink.
        """

        font = 'Times New Roman'
        center_x = 0
        max_y = self._graph_height

        labels = LabelBatch()

        labels.add_text(mix.name,
                        font_name=font,
                        font_size=64,
                        anchor_x='center', anchor_y='top',
                        position = (center_x, max_y))

        labels.add_text("Alcohol: %2.1f %%" % mix.alc_perc,
                        font_name=font,
                        font_size=20,
                        anchor_x='center', anchor_y='top',
                        position = (center_x, max_y - 100))

        y = max_y - 150
        y_spacing = y / len(mix.drinks)
        y -= y_spacing / 2
        for d in mix.drinks:
            labels.add_text(d.name,
                            font_name=font,
                            font_size=20,
                            anchor_x='center', anchor_y='top',
                            position = (center_x, y))
            y -= y_spacing

        labels.add_text("%d" % mix.current_price_quartjes,
                        font_name=font,
                        font_size=150,
                        anchor_x='center', anchor_y='center',
                        position = (center_x + 300, (max_y - 150) / 2))

        image=mix_drawer.create_mix_drawing(height=max_y-150, width=200, mix=mix)
        mix_drawing = cocos.sprite.Sprite(image=image,
                                          position=(center_x - 300, (max_y - 150) / 2),
                                          anchor=(100, (max_y - 150) / 2))
        labels.add(mix_drawing)

        return labels

