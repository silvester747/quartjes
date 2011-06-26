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

    def __init__(self, display_time=1.0, display_y=0, screen_width=1024, drinks=None):
        super(BottomTicker, self).__init__()

        self.display_time = display_time
        self.display_y = display_y
        self.screen_width = screen_width
        self.visible_segments = 8
        self.margin = 1
        self.interval = 2
        self.focus_segment = 5
        self.focus_length = 2
        self.focus_height = 40

        self._calculate_points()

        self.drinks = drinks
        self.current_drink = 0

        self.next_drink()

    def _calculate_points(self):

        distance = self.screen_width / self.visible_segments
        self.points = [(x*distance, self.display_y) for x in range(self.visible_segments + self.margin, -1 - self.margin, -1)]
        self.points[self.focus_segment] = (self.points[self.focus_segment][0], self.focus_height)

        self.segment_count = len(self.points) - 1

        self.focus_start = self.focus_segment - (self.focus_length / 2)
        self.focus_end = self.focus_segment + (self.focus_length / 2)



    def update_drinks(self, drinks):
        self.drinks, self.current_drink = drinks, 0

    def next_drink(self):

        text = ""

        if self.drinks != None and len(self.drinks) > 0:
            self.current_drink += 1
            if self.current_drink >= len(self.drinks):
                self.current_drink = 0
            drink = self.drinks[self.current_drink]
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
        move_actions += (MoveTo(self.points[self.focus_segment], self.display_time * (self.focus_length / 2)) |
                         (Delay((self.display_time * (self.focus_length / 2)) / 2) +
                         ScaleTo(1, (self.display_time * (self.focus_length / 2)) / 2)))
        move_actions += (MoveTo(self.points[self.focus_end], self.display_time * (self.focus_length / 2)) |
                         (ScaleTo(0.5, (self.display_time * (self.focus_length / 2)) / 2)) +
                         Delay((self.display_time * (self.focus_length / 2)) / 2))
        move_actions += MoveTo(self.points[-1], self.display_time * (self.segment_count - self.focus_end))

        next_label.do((spawn_actions | move_actions) + CallFunc(next_label.kill))


if __name__ == "__main__":

    def transition_to(dest):
        cocos.director.director.replace(cocos.scenes.transitions.ShrinkGrowTransition(dest))

    db = Database()

    cocos.director.director.init(width=1024, height=768, fullscreen=True)
    ticker_layer = BottomTicker()
    ticker_layer.update_drinks(db.drinks)
    title_layer = TitleLayer()
    main_scene = cocos.scene.Scene(ticker_layer, title_layer)
    cocos.director.director.run(main_scene)
