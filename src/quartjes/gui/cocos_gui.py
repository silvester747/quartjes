import cocos.actions.base_actions
import cocos.layer.base_layers
__author__="rob"
__date__ ="$Jun 23, 2011 10:13:35 PM$"

import cocos
from cocos.actions import *
from cocos.particle_systems import *
import cocos.scenes.transitions
import cocos.director
import cocos.text
from quartjes.connector.client import ClientConnector
import time
import cocos.cocosnode
import pyglet.text
from pyglet.gl import *

class TitleLayer(cocos.layer.Layer):

    def __init__(self):
        super(TitleLayer, self).__init__()
        
        demo_label = cocos.text.Label("QuartjesAvond",
                                      font_name='Times New Roman',
                                      font_size=80,
                                      anchor_x='center', anchor_y='top')
        demo_label.position = (512, 768)
        self.add(demo_label)
        demo_label.do(Repeat(Waves3D(duration=2, waves=1) + RandomDelay(30, 90)))


class BottomTicker(cocos.layer.Layer):

    def __init__(self, display_time=1.0, display_y=0, screen_width=1024, drinks=None,
                 visible_segments=10, margin=2, interval=3, focus_start=3,
                 focus_length=2, focus_height=40, reset_on_update=False, graph_layer=None):
        super(BottomTicker, self).__init__()

        self.display_time = display_time
        self.display_y = display_y
        self.screen_width = screen_width
        self.visible_segments = visible_segments
        self.margin = margin
        self.interval = interval
        self.focus_start = focus_start + self.margin
        self.focus_length = focus_length
        self.focus_height = focus_height
        self.reset_on_update = reset_on_update
        self.graph_layer = graph_layer

        self._calculate_points()

        self.drinks = drinks
        self.current_drink_index = 0
        self.focussed_drink = None

        # True if a reset is currently in progress, should block all creation
        # of new nodes until reset is finished
        self._resetting = False

        self.next_drink()

    def _calculate_points(self):

        distance = self.screen_width / self.visible_segments
        self.points = [(x*distance, self.display_y) for x in range(self.visible_segments + self.margin, -1 - self.margin, -1)]
        self.segment_count = len(self.points) - 1

        self.focus_end = self.focus_start + 2 + self.focus_length
        for pnt in range(self.focus_start + 1, self.focus_end):
            self.points[pnt] = (self.points[pnt][0], self.focus_height)

    def update_drinks(self, drinks):
        print("Receiving update")
        self.drinks, self.current_drink_index = drinks, 0
        if self.reset_on_update:
            self.do(CallFunc(self.reset))

    def reset(self):
        """
        WARNING: Currently causes invalid operation in GL.
        """
        return
        self._resetting = True
        for child in self.get_children():
            child.do(FadeOut(1) + CallFunc(self._safe_kill, child))
            #child.do(Kill())

        if self.graph_layer != None:
            self.graph_layer.reset()

        time.sleep(1)
        self._resetting = False
        self.do(CallFunc(self.next_drink))

    def _safe_kill(self, child):
        try:
            child.kill()
        except:
            pass

    def _set_focussed_drink(self, drink):
        if self._resetting:
            drink = None

        self.focussed_drink = drink
        if drink != None:
            if self.graph_layer != None:
                self.graph_layer.show_drink_history(drink)

    def next_drink(self):

        if self._resetting:
            return

        text = ""
        drink = None

        if self.drinks != None and len(self.drinks) > 0:
            self.current_drink_index += 1
            if self.current_drink_index >= len(self.drinks):
                self.current_drink_index = 0
            drink = self.drinks[self.current_drink_index]
            text = "%s - %d" % (drink.name, drink.sellprice())

        next_label = cocos.text.Label(text,
                                 font_name='Times New Roman',
                                 font_size=64,
                                 anchor_x='center', anchor_y='bottom')
        next_label.position = self.points[0]
        next_label.scale = 0.5
        self.add(next_label)

        spawn_actions = Delay(self.display_time * self.interval) + CallFunc(self.next_drink)

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

        next_label.do((spawn_actions | move_actions) + CallFunc(next_label.kill))

class GraphLayer(cocos.layer.base_layers.Layer):
    def __init__(self, graph_position=(100,150), graph_width=840, graph_height=400,
                 screen_width=1024, move_time=1.0):
        super(GraphLayer, self).__init__()

        self.graph_position = graph_position
        self.graph_width = graph_width
        self.graph_height = graph_height
        self.screen_width = screen_width
        self.move_time = move_time

        self._points = []
        self._points.append((screen_width, graph_position[1]))
        self._points.append(graph_position)
        self._points.append((0-graph_width, graph_position[1]))

        self.current_graph = None

    def show_drink_history(self, drink):
        if not self.is_running:
            if self.current_graph:
                self.current_graph.kill
                self.current_graph = None

            return

        if self.current_graph:
            self.current_graph.do(CallFunc(self.current_graph.hide_text) +
                                  MoveTo(self._points[2], 0.5 * self.move_time) +
                                  CallFunc(self.current_graph.kill))

        if drink == None:
            return
        if drink.history == None:
            return

        self.current_graph = HistoryGraph(position=self._points[0],
                                          width = self.graph_width,
                                          height=self.graph_height,
                                          data=drink.history)
        self.current_graph.do(Delay(0.5 * self.move_time) +
                              MoveTo(self._points[1], 0.5 * self.move_time) +
                              CallFunc(self.current_graph.show_text))

        self.add(self.current_graph)

    def reset(self):
        return # unsafe
        for child in self.get_children():
            if self.is_running:
                child.do(FadeOut(1) + CallFunc(child.kill))
            else:
                child.kill()

class HistoryGraph(cocos.draw.Canvas):

    def __init__(self, position=(0,0), width=400, height=300, margin=30, data=None):
        super(HistoryGraph, self).__init__()
        self.position = position
        self.width = width
        self.height = height
        self.margin = margin
        self.labels = None
        self.text_visible = False

        # a list containing either lists or tuples
        # each list or tuple should contain exactly 2 values
        # the first value can be of any type implementing __str__
        # the second value must be a numeric value
        self.data = data

    def show_text(self):
        if not self.text_visible:
            self.text_visible = True
            if self.labels != None:
                #for lbl in self.labels:
                #    self.add(lbl)
                self.add(self.labels)

    def hide_text(self):
        if self.text_visible:
            self.text_visible = False
            if self.labels != None:
                #for lbl in self.labels:
                #    lbl.kill()
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
            return
        if len(self.data) < 2:
            return

        self.labels = GraphLabels()

        # draw x axis marks
        x_count = len(self.data)
        x_spacing = (w - 2 * margin) / (x_count - 1)
        x_label_interval = 1
        while x_spacing / x_label_interval < 50:
            x_label_interval += 1

        for i in range(x_count -1, -1, 0 - x_label_interval):
            x = margin + i * x_spacing
            self.move_to((x, margin))
            self.line_to((x, margin* 3/4))

            #self.labels.append(cocos.text.Label(str(self.data[i][0]),
            #                          font_name='Times New Roman',
            #                          font_size=10,
            #                          anchor_x='center', anchor_y='top',
            #                          position = (x, margin * 3/4)))
            self.labels.add_text(str(self.data[i][0]),
                                      font_name='Times New Roman',
                                      font_size=10,
                                      anchor_x='center', anchor_y='top',
                                      position = (x, margin * 3/4))

        # draw y axis marks
        max_y = 0
        for (x, y) in self.data:
            if y > max_y:
                max_y = y
        min_y = max_y
        for (x, y) in self.data:
            if y < min_y:
                min_y = y

        y_count = max_y - min_y + 1
        if min_y > 0:   # only start from the bottom if we start at 0
            min_y -= 1
            y_count += 1

        y_spacing = (h - 2 * margin) / (y_count - 1)
        y_label_interval = 1
        while y_spacing / y_label_interval < 25:
            y_label_interval += 1

        for y_val in range(max_y, min_y, 0 - y_label_interval):
            y = margin + (y_val - min_y) * y_spacing
            self.move_to((margin, y))
            self.line_to((margin * 3/4, y))
            #self.labels.append(cocos.text.Label(str(y_val),
            #                          font_name='Times New Roman',
            #                          font_size=10,
            #                          anchor_x='right', anchor_y='center',
            #                          position = (margin * 3/4, y)))
            self.labels.add_text(str(y_val),
                                      font_name='Times New Roman',
                                      font_size=10,
                                      anchor_x='right', anchor_y='center',
                                      position = (margin * 3/4, y))

        # draw the graph
        self.set_stroke_width(1.0)
        self.set_color((255, 0, 0, 255))

        x = margin
        self.move_to((x, margin + (self.data[0][1] - min_y) * y_spacing))
        x += x_spacing
        for (x_val, y_val) in self.data[1:]:
            y = margin + (y_val - min_y) * y_spacing
            self.line_to((x, y))
            x += x_spacing

class GraphLabels(cocos.cocosnode.CocosNode):
    """
    Special CocosNode to contain a number of text objects
    """
    def __init__(self, position=(0,0)):
        super(GraphLabels, self).__init__()
        self.position = position
        self.group = None
        self.elements = []

        self.batch = pyglet.graphics.Batch()

    def add_text(self, text='', position=(0,0), **kwargs):
        kwargs['text']=text
        self.elements.append(self.klass(group=self.group, batch=self.batch,
                                        x=position[0], y=position[1], **kwargs))

    def draw(self):
        glPushMatrix()
        self.transform()
        self.batch.draw()
        glPopMatrix()

    klass = pyglet.text.Label

class Kill(cocos.actions.base_actions.InstantAction):

    def start(self):
        self.target.pause_scheduler()
        for a in self.target.actions:
            self.target.remove_action(a)
        #self.target.do(Delay(0.1) + CallFunc(self.target.kill))
        self.target.resume_scheduler()
        #self.target.kill()

class CocosGui(object):

    def __init__(self, hostname="localhost", port=1234, width=1024, height=768,
                 fullscreen=True):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.hostname = hostname
        self.port = port

        self.refresh_ticker_on_update = True

        self.ticker_layer = None
        self.graph_layer = None
        self.title_layer = None

        self.drinks = None


    def start(self):
        cocos.director.director.init(width=self.width, height=self.height,
                                     fullscreen=self.fullscreen)
        cocos.director.director.set_show_FPS(True)

        self.connector = ClientConnector(self.hostname, self.port)
        self.connector.start()

        while not self.connector.is_connected():
            time.sleep(1)

        stock_exchange = self.connector.get_service_interface("stock_exchange")
        database = self.connector.get_service_interface("database")
        self.drinks = database.get_drinks()
        database.subscribe("drinks_updated", self._update_drinks)
        stock_exchange.subscribe("next_round", self._next_round)

        self.show_ticker_scene()

    def show_ticker_scene(self, new_ticker=False):
        if not self.ticker_layer or new_ticker:
            self.ticker_layer = BottomTicker()
        if not self.graph_layer:
            self.graph_layer = GraphLayer()
        if not self.title_layer:
            self.title_layer = TitleLayer()

        self.ticker_layer.update_drinks(self.drinks)

        if new_ticker:
            self.graph_layer.show_drink_history(None)

        scene = cocos.scene.Scene(self.ticker_layer, self.graph_layer, self.title_layer)
        self.ticker_layer.graph_layer = self.graph_layer

        self._display_scene(scene)

    def _display_scene(self, scene):
        if cocos.director.director.scene == None:
            cocos.director.director.run(scene)
        else:
            cocos.director.director.replace(cocos.scenes.transitions.FadeTransition(scene))

    def _update_drinks(self, drinks):
        self.drinks = drinks
        self.ticker_layer.update_drinks(drinks)

    def _next_round(self, drinks):
        self.drinks = drinks
        self.show_ticker_scene(True)

def run_cocos_gui():
    gui = CocosGui()
    gui.start()
    #gui.show_ticker_scene()

if __name__ == "__main__":
    run_cocos_gui()