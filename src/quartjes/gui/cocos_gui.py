"""
Graphical user interface using Cocos2D.
Displays the current prices of all _drinks in a ticker at the bottom. As each
drink passes the center of the ticker, related information is shown in the
center of the screen.

TODO
* Create trend overview
* Make screen look like financial TV show, with nice bar for ticker, channel logo, etc
"""
from __future__ import print_function

__author__ = "Rob van der Most"

debug_mode = False

# Do pyglet settings
import pyglet

if debug_mode:
    pyglet.options["debug_gl"] = True
    pyglet.options["debug_gl_trace"] = True
    #pyglet.options["debug_gl_trace_args"] = True
    #pyglet.options["debug_graphics_batch"] = True


import argparse
from axel import Event
import cocos.scenes.transitions
import cocos.director
import cocos.text
import cocos.cocosnode
import cocos.layer.base_layers
from cocos.actions import Delay, CallFunc, MoveTo, ScaleTo, FadeOut, FadeIn
from cocos.sprite import Sprite
import pyglet.resource
import pyglet.text
from pyglet.gl import glPushMatrix, glPopMatrix
from quartjes.connector.client import ClientConnector
from quartjes.models.drink import Mix
import quartjes.gui.mix_drawer as mix_drawer
import quartjes.gui.history_graph as history_graph
import random

pyglet.resource.path = ["@quartjes.resources"]
pyglet.resource.reindex()

class TitleLayer(cocos.layer.Layer):
    """
    Simple layer to display a title at the top of the display.
    """

    def __init__(self):
        super(TitleLayer, self).__init__()
        
        logo = Sprite("cnocbs_logo.png", position=(930,715), scale=0.5, opacity=200)
        self.add(logo)
        
        title = Sprite("title.png", position=(0, 680), anchor=(0,0), opacity=200)
        self.add(title)
        

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

        # Path followed by the ticker elements. Each item is a tuple containing the coordinates and the time required to reach those
        # coordinates.
        self._path = []

        # List of _drinks to show on the ticker
        self._drinks = drinks

        # Index of the drink last added to the ticker
        self._current_drink_index = 0
        
        # Drink currently having focus.
        self.focussed_drink = None

        # Event fired when the currently focused drink has changed. Listeners
        # should have two parameters: the sender and the new drink.
        self.on_focus_changed = Event(sender=self)
        
        # Current round. Used to suppress old actions.
        self._round_number = 0
        
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
        self._path.append([(x, y), time]) # this one is a list to be able to change the time
        
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
                | CallFunc(self._set_focussed_drink, drink, self._round_number))

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
        
        self._set_focussed_drink(self.focussed_drink, self._round_number)

    def _safe_kill(self, child):
        """
        Safely remove a node from the tree.
        """
        try:
            child.kill()
        except:
            pass

    def _set_focussed_drink(self, drink, round_nr):
        """
        Update the currently focussed drink and notify all listeners.
        """
        if round_nr == self._round_number:
            
            # Make sure we have the latest instance
            if not drink is None:
                for tmp_drink in self._drinks:
                    if tmp_drink.id == drink.id:
                        drink = tmp_drink
                        break
                else:
                    drink = None
            
            self.focussed_drink = drink
            self.on_focus_changed(drink)

    def _next_drink(self):
        """
        Prepare the next drink on the list to be shown on screen.
        """
        drink = None

        if self._drinks != None and len(self._drinks) > 0:
            self._current_drink_index += 1
            if self._current_drink_index >= len(self._drinks):
                self._current_drink_index = 0
            drink = self._drinks[self._current_drink_index]

        
        drink_node = TickerDrinkNode(drink)
        self.add(drink_node)
        self._add_animation(drink_node, drink)
        
    def next_round(self):
        self._round_number += 1

class TickerDrinkNode(cocos.cocosnode.CocosNode):
    """
    Cocos node representing a drink on the ticker.
    """
    
    def __init__(self, drink):
        super(TickerDrinkNode, self).__init__()
        
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
            
            

class DrinkLayer(cocos.layer.base_layers.Layer):
    """
    Layer to display details on the currently focussed drink.
    In case a normal drink is focussed, the price graph is displayed.
    In case a mix drink is focussed, the details of the mix are displayed.
    """

    def __init__(self, top=150, graph_width=940, graph_height=500,
                 screen_width=1024, move_time=1.0):
        """
        Initialize the drink layer.
        """
        super(DrinkLayer, self).__init__()

        self._top = top
        self._graph_width = graph_width
        self._graph_height = graph_height
        self._screen_width = screen_width
        self._move_time = move_time

        self._points = []
        self._points.append((screen_width + (graph_width / 2), top))
        self._points.append((screen_width / 2, top))
        self._points.append((0 - (graph_width / 2), top))

        self._current_node = None

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
            self._show_drink(self._next_drink)
            self._next_drink = None
        if self._clear_drink:
            self._clear_drink = False
            self._replace_node(None)
            self._next_drink = None
        if self._show_explanation:
            self._clear_drink = False
            self._next_drink = None
            self._show_explanation = False
            self._replace_node(self._get_explanation())
            

    def _show_drink(self, drink):
        """
        Replace the current drink with the next drink to display.
        """

        new_node = None

        if drink:
            if isinstance(drink, Mix):
                new_node = self._get_mix(drink)
            else:
                new_node = self._get_drink_history(drink)
        
        self._replace_node(new_node)


    def _replace_node(self, new_node):
        if not self.is_running:
            if debug_mode:
                print("Not running")
            if self._current_node:
                self._current_node.kill
                self._current_node = None

            return

        if self._current_node:
            self._current_node.do(MoveTo(self._points[2], 0.5 * self._move_time) +
                                 CallFunc(self._current_node.kill))

        self._current_node = new_node

        if not self._current_node:
            return

        self._current_node.do(Delay(0.5 * self._move_time) +
                              MoveTo(self._points[1], 0.5 * self._move_time))
        self.add(self._current_node)
        
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

        labels = LabelBatch(position=self._points[0])

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
                                   position=self._points[0],
                                   anchor=(self._graph_width / 2, 0))

        return node

    def _get_mix(self, mix):
        """
        Construct a node to show a mix drink.
        """

        font = 'Times New Roman'
        center_x = 0
        max_y = self._graph_height

        labels = LabelBatch(position=self._points[0])

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


class CocosGui(object):
    """
    Main object containing the Cocos2D GUI.
    Initialize and start this object to start a show.
    """

    def __init__(self, hostname=None, port=1234, width=1024, height=768,
                 fullscreen=True, explanation_interval=20):
        """
        Set up all parameters and objects for the GUI.
        """
        self._width = width
        self._height = height
        self._fullscreen = fullscreen
        self._hostname = hostname
        self._port = port

        self._explanation_interval = explanation_interval
        self._refresh_ticker_on_update = True

        self._ticker_layer = None
        self._drink_layer = None
        self._title_layer = None
        self._mix_layer = None

        self._drinks = None
        self._round_count = 0

    def start(self):
        """
        Start running the Cocos GUI.
        This method will block until the GUI has been shut down. After
        returning there might still be some processes cleaning up.
        """
        print("Starting Cocos GUI")
        print("\nUsing following settings:")
        print("\tConnection: %s:%d" % (self._hostname, self._port))
        print("\tGraphics: (%d, %d) fullscreen=%s" %(self._width, self._height, self._fullscreen))
        
        print()
        print("Included libraries:")
        print("\tPyglet:\t%s" % pyglet.version)
        print("\tCocos:\t%s" % cocos.version)
        import twisted
        print("\tTwisted:%s" % twisted.version.short())
        
        print()
        print("Opening connection to server...")
        self._connector = ClientConnector(self._hostname, self._port)
        self._connector.start()

        self._drinks = self._connector.database.get_drinks()
        random.shuffle(self._drinks)

        self._connector.database.on_drinks_updated += self._update_drinks
        self._connector.stock_exchange.on_next_round += self._next_round

        print()
        print("Initializing graphics...")
        cocos.director.director.init(width=self._width, height=self._height,
                                     fullscreen=self._fullscreen)
        cocos.director.director.set_show_FPS(debug_mode)
        self.show_gl_info()

        print()
        print("Starting the show!")
        self.show_ticker_scene()
        
        print()
        print("Shut down in progress...")
        print()
        
        self._connector.stop()

    def show_gl_info(self):
        """
        Display some information about the GL renderer.
        """
        from pyglet.gl.gl_info import GLInfo
        info = GLInfo()
        info.set_active_context()
        
        print("GL Info:")
        print("\tVersion:\t%s" % info.get_version())
        print("\tRenderer:\t%s" % info.get_renderer())
        print("\tVendor:\t\t%s" % info.get_vendor())
        print("\tExtensions:\t%s" % info.get_extensions())
        
        from pyglet.gl.glu_info import GLUInfo
        info = GLUInfo()
        info.set_active_context()
        
        print()
        print("GLU Info:")
        print("\tVersion:\t%s" % info.get_version())
        print("\tExtensions:\t%s" % info.get_extensions())
        

    def show_ticker_scene(self, new_ticker=False):
        """
        Replace everything on screen with the scene displaying the drink ticker.
        If the engine is not yet running, this method will start a new engine
        and will block until the engine has stopped.
        """
        if not self._ticker_layer or new_ticker:
            self._ticker_layer = BottomTicker(screen_width=self._width)
        if not self._drink_layer:
            self._drink_layer = DrinkLayer(screen_width=self._width)
        if not self._title_layer:
            self._title_layer = TitleLayer()

        self._ticker_layer.update_drinks(self._drinks)

        if new_ticker:
            self._drink_layer.show_drink_history(None)

        scene = cocos.scene.Scene(self._ticker_layer, self._drink_layer, self._title_layer)

        self._ticker_layer.on_focus_changed += lambda sender, drink: self._drink_layer.show_drink(drink)
        self._ticker_layer.on_focus_changed += lambda sender, drink: self._title_layer.next_round_started()

        self._drink_layer.show_explanation()

        self._display_scene(scene)


    def _display_scene(self, scene):
        """
        Change the display to show the given scene.
        If no engine is running yet, an engine will be started. In that case this method
        will not return until the engine has stopped again.
        """
        if cocos.director.director.scene == None:
            cocos.director.director.run(scene)
        else:
            cocos.director.director.replace(cocos.scenes.transitions.FadeTransition(scene))

    def _update_drinks(self, drinks):
        self._drinks = drinks
        random.shuffle(self._drinks)
        if self._ticker_layer:
            self._ticker_layer.update_drinks(self._drinks)

    def _next_round(self):
        self._round_count += 1
        self._round_count %= self._explanation_interval
        if self._round_count == 0:
            self._ticker_layer.next_round()
            self._drink_layer.show_explanation()
            
def parse_command_line():
    """
    Parse the command line.
    Returns a namespace object containing the arguments.
    """
    parser = argparse.ArgumentParser(description="2D OpenGL accelerated GUI for Quartjesavond.")
    parser.add_argument("--hostname", help="Hostname to connect too. Default runs local server.")
    parser.add_argument("--port", type=int, default=1234, help="Port to connect to.")
    parser.add_argument("--no-fullscreen", action="store_false", dest="fullscreen", 
                        help="Do not run in fullscreen mode.")
    parser.add_argument("--width", type=int, default=1024, help="Width of the display window.")
    parser.add_argument("--height", type=int, default=768, help="Height of the display window.")
    args = parser.parse_args()
    return args

def run_cocos_gui():
    """
    Do a normal startup of the Cocos GUI.
    Parses the command line and starts the gui.
    """
    args = parse_command_line()
    gui = CocosGui(hostname=args.hostname, port = args.port, width=args.width, height=args.height,
                   fullscreen=args.fullscreen)
    gui.start()


if __name__ == "__main__":
    run_cocos_gui()
