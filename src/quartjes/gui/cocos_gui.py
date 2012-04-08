__author__="rob"
__date__ ="$Jun 23, 2011 10:13:35 PM$"

import argparse
from axel import Event
import cocos.scenes.transitions
import cocos.director
import cocos.text
import cocos.cocosnode
import cocos.layer.base_layers
from cocos.actions import Repeat, Waves3D, Delay, CallFunc, MoveTo, ScaleTo
import datetime
import math
import pyglet.text
from pyglet.gl import glPushMatrix, glPopMatrix
from quartjes.connector.client import ClientConnector
from quartjes.models.drink import Mix
import time
from quartjes.gui.mix_drawer import create_mix_drawing

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
                 focus_length=2, focus_height=40, drink_layer=None):
        """
        Initialize the ticker.
        """
        super(BottomTicker, self).__init__()

        # Time in pyglet units between each point on the ticker.
        self.display_time = display_time

        # Y coordinate on the screen where the ticker is shown.
        self.display_y = display_y

        # Width of the screen. This width is used to calculate the path the items
        # in the ticker follow.
        self.screen_width = screen_width

        # Number of segments to divide the visible screen in. Used to create the
        # path to follow.
        self.visible_segments = visible_segments

        # Number of segments outside the visible screen at each side.
        self.margin = margin

        # Number of segments between each item on the ticker.
        self.interval = interval

        # Number of the segment where the item starts to have focus. This includes
        # segments outside the visible screen.
        self.focus_start = focus_start + self.margin

        # Number of segments an item has focus.
        self.focus_length = focus_length

        # Increase in y position on the screen for items with focus.
        self.focus_height = focus_height
        
        # List of drinks to show on the ticker
        self.drinks = drinks

        # Index of the drink last added to the ticker
        self.current_drink_index = 0

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

        distance = self.screen_width / self.visible_segments
        self.points = [(x*distance, self.display_y) for x in range(self.visible_segments + self.margin, -1 - self.margin, -1)]
        self.segment_count = len(self.points) - 1

        self.focus_end = self.focus_start + 2 + self.focus_length
        for pnt in range(self.focus_start + 1, self.focus_end):
            self.points[pnt] = (self.points[pnt][0], self.focus_height)

    def update_drinks(self, drinks):
        """
        Replace the current list of drinks to show on the ticker. Will not remove
        already visible drinks.
        """
        print("Receiving update")
        cur_drink = self.current_drink_index
        if cur_drink >= len(drinks):
            cur_drink = 0
        self.drinks, self.current_drink_index = drinks, cur_drink

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

        if self.drinks != None and len(self.drinks) > 0:
            self.current_drink_index += 1
            if self.current_drink_index >= len(self.drinks):
                self.current_drink_index = 0
            drink = self.drinks[self.current_drink_index]
            text = "%s - %d" % (drink.name, drink.sellprice_quartjes())

        next_label = cocos.text.Label(text,
                                 font_name='Times New Roman',
                                 font_size=64,
                                 anchor_x='center', anchor_y='bottom')
        next_label.position = self.points[0]
        next_label.scale = 0.5
        self.add(next_label)

        spawn_actions = Delay(self.display_time * self.interval) + CallFunc(self._next_drink)

        move_actions = MoveTo(self.points[self.focus_start], self.display_time * self.focus_start)
        move_actions += (MoveTo(self.points[self.focus_start + 1], self.display_time) |
                         (Delay(self.display_time / 2) +
                         ScaleTo(1, self.display_time / 2)) |
                         CallFunc(self._set_focussed_drink, drink))
        move_actions += (MoveTo(self.points[self.focus_end - 1], self.display_time * self.focus_length))
        move_actions += (MoveTo(self.points[self.focus_end], self.display_time) |
                         (ScaleTo(0.5, self.display_time / 2) +
                         Delay(self.display_time / 2)))
        move_actions += MoveTo(self.points[-1], self.display_time * (self.segment_count - self.focus_end))

        next_label.do((spawn_actions | move_actions) + CallFunc(self._safe_kill, next_label))


class DrinkLayer(cocos.layer.base_layers.Layer):
    """
    Layer to display details on the currently focussed drink.
    In case a normal drink is focussed, the price graph is displayed.
    In case a mix drink is focussed, the details of the mix are displayed.
    """

    def __init__(self, graph_position=(50,150), graph_width=940, graph_height=500,
                 screen_width=1024, move_time=1.0):
        super(DrinkLayer, self).__init__()

        self.graph_position = graph_position
        self.graph_width = graph_width
        self.graph_height = graph_height
        self.screen_width = screen_width
        self.move_time = move_time

        self._points = []
        self._points.append((screen_width, graph_position[1]))
        self._points.append(graph_position)
        self._points.append((0-graph_width, graph_position[1]))

        self.current_node = None

        self.next_drink = None

    def show_drink(self, drink):
        self.next_drink = drink

    def draw(self, *args, **kwargs):
        if self.next_drink:
            self._show_drink(self.next_drink)
            self.next_drink = None

    def _show_drink(self, drink):
        #print("_show_drink called")
        if not self.is_running:
            print("Not running")
            if self.current_node:
                self.current_node.kill
                self.current_node = None

            return

        if self.current_node:
            self.current_node.do(MoveTo(self._points[2], 0.5 * self.move_time) +
                                 CallFunc(self.current_node.kill))

        if drink == None:
            print("No drink")
            return

        if isinstance(drink, Mix):
            self._show_mix(drink)
        else:
            self._show_drink_history(drink)

    def _show_drink_history(self, drink):

        if drink.history == None:
            print("No history")
            return

        self.current_node = HistoryGraph(position=self._points[0],
                                          width = self.graph_width,
                                          height=self.graph_height,
                                          data=drink.history)
        self.current_node.do(Delay(0.5 * self.move_time) +
                              MoveTo(self._points[1], 0.5 * self.move_time))

        self.add(self.current_node)

    def _show_mix(self, mix):

        font = 'Times New Roman'
        #font = 'Verdana'

        center_x = self.graph_width / 2
        max_y = self.graph_height

        labels = GraphLabels(position=self._points[0])

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


        mix_drawing = cocos.sprite.Sprite(image=create_mix_drawing(height=max_y-150, width=200, mix=mix),
                                          position=(100, 0))
        labels.add(mix_drawing)
        #labels.add(MixGlass(position=(100, 0), height=max_y-150, width=200, mix=mix))

        self.add(labels)
        self.current_node = labels

        labels.do(Delay(0.5 * self.move_time) +
                              MoveTo(self._points[1], 0.5 * self.move_time))



class HistoryGraph(cocos.draw.Canvas):

    def __init__(self, position=(0,0), width=400, height=300, margin=30, data=None, initial_visible=True):
        super(HistoryGraph, self).__init__()
        self.position = position
        self.width = width
        self.height = height
        self.margin = margin
        self.labels = None
        self.text_visible = False
        self.initial_visible = initial_visible

        # a list containing either lists or tuples
        # each list or tuple should contain exactly 2 values
        # the first value can be of any type implementing __str__
        # the second value must be a numeric value
        self.data = data

    def show_text(self):
        if not self.text_visible:
            self.text_visible = True
            if self.labels != None:
                self.add(self.labels)

    def hide_text(self):
        if self.text_visible:
            self.text_visible = False
            if self.labels != None:
                self.labels.kill()

    def render(self):
        self._draw_graph()

    def _draw_graph(self):

        w, h = self.width, self.height
        margin = self.margin

        # draw x and y axis lines
        self.set_color((255, 255, 255, 255))
        self.set_stroke_width(0.5)

        self.move_to((margin, h - margin))
        self.line_to((margin, margin))
        self.line_to((w - margin, margin))

        if self.data == None:
            #print("No data")
            return
        if len(self.data) < 2:
            #print("Not enough data")
            return

        self.labels = GraphLabels()

        # draw x axis marks
        #print("draw x axis")
        max_x = 0
        for (x, y) in self.data:
            if x > max_x:
                max_x = x
        min_x = max_x
        for (x, y) in self.data:
            if x < min_x:
                min_x = x

        x_count = len(self.data)
        x_spacing = (w - 2 * margin) / (x_count - 1)
        x_label_interval = 1
        while x_spacing * x_label_interval < 100:
            x_label_interval += 1

        for i in range(x_count -1, -1, 0 - x_label_interval):
            x = margin + i * x_spacing
            self.move_to((x, margin))
            self.line_to((x, margin* 3/4))

            txt = datetime.datetime.fromtimestamp(self.data[i][0]).strftime("%H:%M")

            self.labels.add_text(txt,
                                      font_name='Times New Roman',
                                      font_size=12,
                                      anchor_x='center', anchor_y='top',
                                      position = (x, margin * 3/4))

        # draw y axis marks
        #print("draw y axis")
        max_y = 0
        for (x, y) in self.data:
            if y > max_y:
                max_y = y
        min_y = max_y
        for (x, y) in self.data:
            if y < min_y:
                min_y = y

        max_y = int(math.ceil(max_y))
        min_y = int(math.floor(min_y))

        y_count = max_y - min_y + 1
        if min_y > 0:   # only start from the bottom if we start at 0
            min_y -= 1
            y_count += 1

        y_spacing = float(h - 2 * margin) / (y_count - 1)
        #print(y_spacing)
        y_label_interval = 1
        while y_spacing * y_label_interval < 50:
            y_label_interval += 1

        #print("start drawing y")
        for y_val in range(max_y, min_y, 0 - y_label_interval):
            y = margin + (y_val - min_y) * y_spacing
            self.move_to((margin, y))
            self.line_to((margin * 3/4, y))
            self.labels.add_text(str(y_val),
                                      font_name='Times New Roman',
                                      font_size=12,
                                      anchor_x='right', anchor_y='center',
                                      position = (margin * 3/4, y))

        # draw the graph
        #print("draw graph")
        self.set_stroke_width(1.0)
        self.set_color((255, 0, 0, 255))

        x = margin
        self.move_to((x, margin + (self.data[0][1] - min_y) * y_spacing))
        x += x_spacing
        for (x_val, y_val) in self.data[1:]:
            y = margin + (y_val - min_y) * y_spacing
            self.line_to((x, y))
            x += x_spacing

        if self.initial_visible:
            self.show_text()

class MixGlass(cocos.draw.Canvas):

    def __init__(self, position=(0,0), width=400, height=300, taper=0.1, mix=None):
        super(MixGlass, self).__init__()
        self.position = position
        self.width = width
        self.height = height
        self.taper = taper
        self.mix = mix

    def render(self):

        h, w, t = self.height, self.width, self.taper

        # draw contents
        middle_x = w / 2
        fill = 0.8
        current_radius = lambda y_fact: w * (0.5 - ((1- y_fact) * t))
        y_fact = lambda y: float(y) / float(h)

        count = len(self.mix.drinks)
        current_drink_id = lambda y: int(math.floor((float(y) / (float(h) * fill)) * count) % count)

        self.mix.update_properties()
        self.set_stroke_width(1.0)
        self.set_color(self.mix.color + (140,))

        for y in range(0, int(h*fill)):
            r = current_radius(y_fact(y))
            self.move_to((middle_x - r, y))
            self.line_to((middle_x, y))

        for y in range(0, int(h*fill)):
            self.set_color(self.mix.drinks[-1 - current_drink_id(y)].color + (140,))
            r = current_radius(y_fact(y))
            self.move_to((middle_x, y))
            self.line_to((middle_x + r, y))

        # draw the glass
        self.set_stroke_width(5.0)
        self.set_color((255, 255, 255, 255))
        self.move_to((0, h))
        self.line_to((t*w, 0))
        self.line_to(((1-t)*w, 0))
        self.line_to((w, h))


class GraphLabels(cocos.cocosnode.CocosNode):
    """
    Special CocosNode to contain a number of text objects
    """

    use_batch_rendering = True

    def __init__(self, position=(0,0)):
        super(GraphLabels, self).__init__()
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

        self.drinks = None
        self.mixes = None
        self.all = None

    def start(self):
        print("Starting Cocos GUI")
        print("\nUsing following settings:")
        print("\tConnection: %s:%d" % (self.hostname, self.port))
        print("\tGraphics: (%d, %d) fullscreen=%s" %(self.width, self.height, self.fullscreen))
        
        self.connector = ClientConnector(self.hostname, self.port)
        self.connector.start()

        self.drinks = self.connector.database.get_drinks()
        self.mixes = self.connector.database.get_mixes()

        self.all = self.drinks + self.mixes

        print("subscribe drinks_updated")
        #database.subscribe("drinks_updated", self._update_drinks)
        #database.subscribe("mixes_updated", self._update_mixes)
        print("subscribe next_round")
        #stock_exchange.subscribe("next_round", self._next_round)

        cocos.director.director.init(width=self.width, height=self.height,
                                     fullscreen=self.fullscreen)
        cocos.director.director.set_show_FPS(True)

        self.show_ticker_scene()
        
        self.connector.stop()

    def show_ticker_scene(self, new_ticker=False):
        if not self.ticker_layer or new_ticker:
            self.ticker_layer = BottomTicker(screen_width=self.width)
        if not self.drink_layer:
            self.drink_layer = DrinkLayer(screen_width=self.width)
        if not self.title_layer:
            self.title_layer = TitleLayer()

        self.ticker_layer.update_drinks(self.drinks)

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
        self.drinks = drinks
        self.all = self.mixes + self.drinks
        if self.ticker_layer:
            self.ticker_layer.update_drinks(self.all)

    def _update_mixes(self, mixes):
        self.mixes = mixes
        self.all = self.mixes + self.drinks
        if self.ticker_layer:
            self.ticker_layer.update_drinks(self.all)

    def _next_round(self, drinks):
        self.drinks = drinks
        self.all = self.mixes + self.drinks
        if self.ticker_layer:
            self.ticker_layer.update_drinks(self.all)
            
def parse_command_line():
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
    args = parse_command_line()
    gui = CocosGui(hostname=args.hostname, port = args.port, width=args.width, height=args.height,
                   fullscreen=args.fullscreen)
    gui.start()
    #gui.show_ticker_scene()

def test_mix():
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
