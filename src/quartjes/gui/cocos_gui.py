__author__="rob"
__date__ ="$Jun 23, 2011 10:13:35 PM$"

import cocos
from cocos.actions import *
from cocos.particle_systems import *
import cocos.scenes.transitions
import cocos.director
import cocos.text
from quartjes.controllers.database import Database

class TitleLayer(cocos.layer.Layer):

    def __init__(self):
        super(TitleLayer, self).__init__()
        
        demo_label = cocos.text.Label("QuartjesAvond",
                                      font_name='Times New Roman',
                                      font_size=80,
                                      anchor_x='center', anchor_y='top')
        demo_label.position = (512, 768)
        self.add(demo_label)
        demo_label.do(Repeat(Waves3D(duration=200, waves=200)))


class BottomTicker(cocos.layer.Layer):

    def __init__(self, display_time=1.0, display_y=0, screen_width=1024, drinks=None,
                 visible_segments=10, margin=1, interval=3, focus_start=3,
                 focus_length=2, focus_height=40, reset_on_update=True):
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

        self._calculate_points()

        self.drinks = drinks
        self.current_drink_index = 0
        self.focussed_drink = None

        self.next_drink()

        self.history_graph = None

    def _calculate_points(self):

        distance = self.screen_width / self.visible_segments
        self.points = [(x*distance, self.display_y) for x in range(self.visible_segments + self.margin, -1 - self.margin, -1)]
        self.segment_count = len(self.points) - 1

        self.focus_end = self.focus_start + 2 + self.focus_length
        for pnt in range(self.focus_start + 1, self.focus_end):
            self.points[pnt] = (self.points[pnt][0], self.focus_height)

    def update_drinks(self, drinks):
        self.drinks, self.current_drink_index = drinks, 0
        if self.reset_on_update:
            self.reset()

    def reset(self):
        for child in self.get_children():
            child.do(FadeOut(1))
        time.sleep(1)

    def _set_focussed_drink(self, drink):
        self.focussed_drink = drink
        if drink != None:
            if self.history_graph != None:
                self.history_graph.kill()
            self.history_graph = Graph(position=(100, 150), width = 824, height=400, data=drink.history)
            self.add(self.history_graph)
        #print(drink)

    def next_drink(self):

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
                         ScaleTo(1, self.display_time / 2)))
        move_actions += (MoveTo(self.points[self.focus_end - 1], self.display_time * self.focus_length) |
                         CallFunc(self._set_focussed_drink, drink))
        move_actions += (MoveTo(self.points[self.focus_end], self.display_time) |
                         (ScaleTo(0.5, self.display_time / 2) +
                         Delay(self.display_time / 2)))
        move_actions += MoveTo(self.points[-1], self.display_time * (self.segment_count - self.focus_end))

        next_label.do((spawn_actions | move_actions) + CallFunc(next_label.kill))

class Graph(cocos.draw.Canvas):

    def __init__(self, position=(0,0), width=400, height=300, data=None):
        super(Graph, self).__init__()
        self.position = position
        self.width = width
        self.height = height

        # a dictionary: key is x, value = y
        self.data = data
        self._prepare_data()

    def update_data(self, data):
        self.data = data
        self._prepare_data()

    def _prepare_data(self):
        if self.data == None:
            return

        #max_x = 0
        #for x in self.data.keys():
        #    if x > max_x:
        #        max_x = x
        #min_x = max_x
        #for x in self.data.keys():
        #    if x < min_x:
        #        min_x = x

        max_y = 0
        for y in self.data.values():
            if y > max_y:
                max_y = y
        min_y = max_y
        for y in self.data.values():
            if y < min_y:
                min_y = y

        #self._min_x, self._max_x = min_x, max_x
        self._min_y, self._max_y = min_y, max_y

    def render(self):
        self.draw_graph()

    def draw_graph(self):

        w, h = self.width, self.height
        margin = 30

        self.set_color((255, 255, 255, 255))
        self.set_stroke_width(0.5)

        self.move_to((margin, h - margin))
        self.line_to((margin, margin))
        self.line_to((w - margin, margin))

        if self.data == None:
            return

        x_spacing = (w - 2 * margin) / (len(self.data) - 1)
        x = margin
        for key in self.data.keys():
            self.move_to((x, margin))
            self.line_to((x, margin/2))
            x += x_spacing

        y_count = self._max_y - self._min_y + 1
        y_spacing = (h - 2 * margin) / (y_count - 1)
        y = margin
        for y_val in range(self._min_y, self._max_y + 1):
            self.move_to((margin, y))
            self.line_to((margin/2, y))
            y += y_spacing

        self.set_stroke_width(1.0)
        self.set_color((255, 0, 0, 255))

        x = margin
        self.move_to((x, margin + (self.data.values()[0] - self._min_y) * y_spacing))
        x += x_spacing
        for (x_val, y_val) in self.data.items()[1:]:
            y = margin + (y_val - self._min_y) * y_spacing
            self.line_to((x, y))
            x += x_spacing


if __name__ == "__main__":
    import time
    import threading
    import random

    def transition_to(dest):
        cocos.director.director.replace(cocos.scenes.transitions.ShrinkGrowTransition(dest))

    class UpdateTestThread(threading.Thread):
        def __init__(self, ticker):
            threading.Thread.__init__(self, name="TestThread")
            self.daemon = True
            self.ticker = ticker

        def run(self):
            db = Database()

            while True:
                time.sleep(20)
                #print("Updating...")
                self.ticker.update_drinks(db.drinks)


    cocos.director.director.init(width=1024, height=768, fullscreen=True)
    ticker_layer = BottomTicker()
    title_layer = TitleLayer()
    main_scene = cocos.scene.Scene(ticker_layer, title_layer)

    db = Database()
    drinks = db.drinks
    for drink in drinks:
        drink.history = dict(zip(range(1, 8), [random.randint(6, 15) for x in range(1,8)]))
    ticker_layer.update_drinks(db.drinks)

    #thread = UpdateTestThread(ticker_layer)
    #thread.start()

    cocos.director.director.run(main_scene)
