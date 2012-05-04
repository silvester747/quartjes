"""
Graphical user interface using Cocos2D.
Displays the current prices of all _drinks in a ticker at the bottom. As each
drink passes the center of the ticker, related information is shown in the
center of the screen.
"""
from __future__ import print_function

__author__ = "Rob van der Most"

import argparse
from axel import Event
import cocos.scenes.transitions
import cocos.director
import cocos.text
import cocos.cocosnode
import cocos.layer.base_layers
from cocos.actions import Repeat, Waves3D, Delay, CallFunc, MoveTo, ScaleTo
import pyglet.text
from pyglet.gl import glPushMatrix, glPopMatrix
from quartjes.connector.client import ClientConnector
from quartjes.models.drink import Mix
import time
import quartjes.gui.mix_drawer as mix_drawer
import quartjes.gui.history_graph as history_graph

class TitleLayer(cocos.layer.Layer):
    """
    Simple layer to display a title at the top of the display.
    """

    def __init__(self):
        super(TitleLayer, self).__init__()
        
        title_label = cocos.text.Label("QuartjesAvond",
                                      font_name='Times New Roman',
                                      font_size=80,
                                      anchor_x='center', anchor_y='top')
        title_label.position = (512, 768)
        self.add(title_label)
        title_label.do(Repeat(Waves3D(duration=200, waves=100)))


class BottomTicker(cocos.layer.Layer):
    """
    Layer containing a ticker of drinks.
    The list of drinks scrolls from the right of the screen to the left. In the
    middle one of the drinks will gain focus and is shown larger.
    """

    def __init__(self, display_time=1.0, display_y=0, screen_width=1024, drinks=None,
                 visible_segments=10, margin=2, interval=3, focus_start=3,
                 focus_length=2, focus_height=40):
        """
        Initialize the ticker.
        """
        super(BottomTicker, self).__init__()

        # Time in pyglet units between each point on the ticker.
        self._display_time = display_time

        # Y coordinate on the screen where the ticker is shown.
        self._display_y = display_y

        # Width of the screen. This width is used to calculate the path the items
        # in the ticker follow.
        self._screen_width = screen_width

        # Number of segments to divide the visible screen in. Used to create the
        # path to follow.
        self._visible_segments = visible_segments

        # Number of segments outside the visible screen at each side.
        self._margin = margin

        # Number of segments between each item on the ticker.
        self._interval = interval

        # Number of the segment where the item starts to have focus. This includes
        # segments outside the visible screen.
        self._focus_start = focus_start + self._margin

        # Number of segments an item has focus.
        self._focus_length = focus_length

        # Increase in y position on the screen for items with focus.
        self._focus_height = focus_height
        
        # List of _drinks to show on the ticker
        self._drinks = drinks

        # Index of the drink last added to the ticker
        self._current_drink_index = 0
        
        # List of points followed by the ticker
        self._points = []
        
        # Total number of segments
        self._segment_count = 0
        
        # Segment the focus ends
        self._focus_end = 0

        # Drink currently having focus.
        self.focussed_drink = None

        # Event fired when the currently focused drink has changed. Listeners
        # should have two parameters: the sender and the new drink.
        self.on_focus_changed = Event(sender=self)

        self._calculate_points()
        self._next_drink()

    def _calculate_points(self):
        """
        Prepare the ticker by calculating all points on the path.
        """

        distance = self._screen_width / self._visible_segments
        self._points = [(x*distance, self._display_y) for x in range(self._visible_segments + self._margin, -1 - self._margin, -1)]
        self._segment_count = len(self._points) - 1

        self._focus_end = self._focus_start + 2 + self._focus_length
        for pnt in range(self._focus_start + 1, self._focus_end):
            self._points[pnt] = (self._points[pnt][0], self._focus_height)

    def update_drinks(self, drinks):
        """
        Replace the current list of drinks to show on the ticker. Will not remove
        already visible drinks.
        """
        print("Receiving update")
        cur_drink = self._current_drink_index
        if cur_drink >= len(drinks):
            cur_drink = 0
        self._drinks, self._current_drink_index = drinks, cur_drink

    def _safe_kill(self, child):
        """
        Safely remove a node from the tree.
        """
        try:
            child.kill()
        except:
            pass

    def _set_focussed_drink(self, drink):
        """
        Update the currently focussed drink and notify all listeners.
        """
        self.focussed_drink = drink
        self.on_focus_changed(drink)

    def _next_drink(self):
        """
        Prepare the next drink on the list to be shown on screen.
        """
        text = ""
        drink = None

        if self._drinks != None and len(self._drinks) > 0:
            self._current_drink_index += 1
            if self._current_drink_index >= len(self._drinks):
                self._current_drink_index = 0
            drink = self._drinks[self._current_drink_index]
            text = "%s - %d" % (drink.name, drink.sellprice_quartjes())

        next_label = cocos.text.Label(text,
                                 font_name='Times New Roman',
                                 font_size=64,
                                 anchor_x='center', anchor_y='bottom')
        next_label.position = self._points[0]
        next_label.scale = 0.5
        self.add(next_label)

        spawn_actions = Delay(self._display_time * self._interval) + CallFunc(self._next_drink)

        move_actions = MoveTo(self._points[self._focus_start], self._display_time * self._focus_start)
        move_actions += (MoveTo(self._points[self._focus_start + 1], self._display_time) |
                         (Delay(self._display_time / 2) +
                         ScaleTo(1, self._display_time / 2)) |
                         CallFunc(self._set_focussed_drink, drink))
        move_actions += (MoveTo(self._points[self._focus_end - 1], self._display_time * self._focus_length))
        move_actions += (MoveTo(self._points[self._focus_end], self._display_time) |
                         (ScaleTo(0.5, self._display_time / 2) +
                         Delay(self._display_time / 2)))
        move_actions += MoveTo(self._points[-1], self._display_time * (self._segment_count - self._focus_end))

        next_label.do((spawn_actions | move_actions) + CallFunc(self._safe_kill, next_label))


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

    def show_drink(self, drink):
        """
        Change the drink currently being shown.
        """
        self._next_drink = drink

    def draw(self, *args, **kwargs):
        """
        Called by Cocos2D. Performs actions on next render loop.
        """
        if self._next_drink:
            self._show_drink(self._next_drink)
            self._next_drink = None

    def _show_drink(self, drink):
        """
        Replace the current drink with the next drink to display.
        """
        if not self.is_running:
            print("Not running")
            if self._current_node:
                self._current_node.kill
                self._current_node = None

            return

        if self._current_node:
            self._current_node.do(MoveTo(self._points[2], 0.5 * self._move_time) +
                                 CallFunc(self._current_node.kill))

        if drink == None:
            print("No drink")
            return

        if isinstance(drink, Mix):
            self._current_node = self._get_mix(drink)
        else:
            self._current_node = self._get_drink_history(drink)

        self._current_node.do(Delay(0.5 * self._move_time) +
                              MoveTo(self._points[1], 0.5 * self._move_time))
        self.add(self._current_node)


    def _get_drink_history(self, drink):
        """
        Construct a node to display the historic price graph for a drink.
        """

        if drink.history == None:
            print("No history")
            return

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
        #font = 'Verdana'

        #center_x = self._graph_width / 2
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
        for d in mix.drinks:
            labels.add_text(d.name,
                            font_name=font,
                            font_size=20,
                            anchor_x='right', anchor_y='top',
                            position = (center_x - 20, y))
            y -= 30

        labels.add_text("%d" % mix.sellprice_quartjes(),
                        font_name=font,
                        font_size=100,
                        anchor_x='left', anchor_y='top',
                        position = (center_x + 20, max_y - 150))


        mix_drawing = cocos.sprite.Sprite(image=mix_drawer.create_mix_drawing(height=max_y-150, width=200, mix=mix),
                                          position=(-400, 0),anchor=(0,0))
        labels.add(mix_drawing)

        return labels

class LabelBatch(cocos.cocosnode.CocosNode):
    """
    Special CocosNode to contain a number of text objects
    """

    use_batch_rendering = True

    def __init__(self, position=(0,0)):
        super(LabelBatch, self).__init__()
        self.position = position
        self.group = None
        self.elements = []

        if self.use_batch_rendering:
            self.batch = pyglet.graphics.Batch()
        else:
            self.batch = None

    def add_text(self, text='', position=(0,0), **kwargs):
        kwargs['text']=text
        element = pyglet.text.Label(group=self.group, batch=self.batch,
                                    x=position[0], y=position[1], **kwargs)
        self.elements.append(element)

    def draw(self):
        glPushMatrix()
        self.transform()
        if self.batch:
            self.batch.draw()
        else:
            for e in self.elements:
                e.draw()
        glPopMatrix()


class CocosGui(object):

    def __init__(self, hostname=None, port=1234, width=1024, height=768,
                 fullscreen=True):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.hostname = hostname
        self.port = port

        self.refresh_ticker_on_update = True

        self.ticker_layer = None
        self.drink_layer = None
        self.title_layer = None
        self.mix_layer = None

        self._drinks = None
        self.mixes = None
        self.all = None

    def start(self):
        print("Starting Cocos GUI")
        print("\nUsing following settings:")
        print("\tConnection: %s:%d" % (self.hostname, self.port))
        print("\tGraphics: (%d, %d) fullscreen=%s" %(self.width, self.height, self.fullscreen))
        
        print()
        print("Included libraries:")
        print("\tPyglet:\t%s" % pyglet.version)
        print("\tCocos:\t%s" % cocos.version)
        import twisted
        print("\tTwisted:%s" % twisted.version.short())
        
        print()
        print("Opening connection to server...")
        self.connector = ClientConnector(self.hostname, self.port)
        self.connector.start()

        self._drinks = self.connector.database.get_drinks()
        self.mixes = self.connector.database.get_mixes()

        self.all = self._drinks + self.mixes

        #print("subscribe drinks_updated")
        #database.subscribe("drinks_updated", self._update_drinks)
        #database.subscribe("mixes_updated", self._update_mixes)
        #print("subscribe next_round")
        #stock_exchange.subscribe("next_round", self._next_round)

        print()
        print("Initializing graphics...")
        cocos.director.director.init(width=self.width, height=self.height,
                                     fullscreen=self.fullscreen)
        cocos.director.director.set_show_FPS(True)
        self.show_gl_info()

        print()
        print("Starting the show!")
        self.show_ticker_scene()
        
        print()
        print("Shut down in progress...")
        print()
        
        self.connector.stop()

    def show_gl_info(self):
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
        if not self.ticker_layer or new_ticker:
            self.ticker_layer = BottomTicker(screen_width=self.width)
        if not self.drink_layer:
            self.drink_layer = DrinkLayer(screen_width=self.width)
        if not self.title_layer:
            self.title_layer = TitleLayer()

        self.ticker_layer.update_drinks(self.all)

        if new_ticker:
            self.drink_layer.show_drink_history(None)

        scene = cocos.scene.Scene(self.ticker_layer, self.drink_layer, self.title_layer)

        self.ticker_layer.on_focus_changed += lambda sender, drink: self.drink_layer.show_drink(drink)

        self._display_scene(scene)


    def _display_scene(self, scene):
        if cocos.director.director.scene == None:
            cocos.director.director.run(scene)
        else:
            cocos.director.director.replace(cocos.scenes.transitions.FadeTransition(scene))

    def _update_drinks(self, drinks):
        self._drinks = drinks
        self.all = self.mixes + self._drinks
        if self.ticker_layer:
            self.ticker_layer.update_drinks(self.all)

    def _update_mixes(self, mixes):
        self.mixes = mixes
        self.all = self.mixes + self._drinks
        if self.ticker_layer:
            self.ticker_layer.update_drinks(self.all)

    def _next_round(self, drinks):
        self._drinks = drinks
        self.all = self.mixes + self._drinks
        if self.ticker_layer:
            self.ticker_layer.update_drinks(self.all)
            
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

def test_mix():
    """
    Self test for testing the mix drawing functionality.
    """
    cocos.director.director.init(width=1024, height=768,
                                     fullscreen=True)
    cocos.director.director.set_show_FPS(True)

    drink_layer = DrinkLayer()
    
    from threading import Thread

    class TestThread(Thread):

        def __init__(self, drink_layer):
            Thread.__init__(self, name="TestThread")
            self.daemon = True
            self.drink_layer = drink_layer

        def run(self):
            from quartjes.controllers.database import database
            mixes = database.get_mixes()[:]
            #mixes += database.get_drinks()[:]
            current = 0

            while True:
                current += 1
                if current >= len(mixes):
                    current = 0
                self.drink_layer.show_drink(mixes[current])
                time.sleep(20)

    t = TestThread(drink_layer)
    t.start()

    scene = cocos.scene.Scene(drink_layer)
    cocos.director.director.run(scene)

    print("Killed")

if __name__ == "__main__":
    #run_cocos_gui()
    test_mix()
