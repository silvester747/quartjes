import cocos.director
import cocos.text
# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="rob"
__date__ ="$Jun 23, 2011 10:13:35 PM$"

import cocos
from cocos.actions import *
from cocos.particle_systems import *

class BottomTicker(cocos.layer.Layer):


    def __init__(self):
        super(BottomTicker, self).__init__()

        demo_label = cocos.text.Label("Proof of Concept",
                                      font_name='Times New Roman',
                                      font_size=80,
                                      anchor_x='center', anchor_y='center')
        demo_label.position = (512, 400)
        self.add(demo_label)
        demo_label.do(Repeat(Waves3D(duration=200, waves=200)))

        fire = Fire()
        fire.position = (512, 500)
        self.add(fire)

        sun = Sun()
        sun.position = (712, 500)
        self.add(sun)

        meteor = Meteor()
        meteor.position = (312, 500)
        self.add(meteor)


        self.drinks = ["Cola - 4", "Bier - 10", "Sinas - 8", "Vodka - 1"]
        self.current_drink = 0

        self.next_drink(None, None)

    def next_drink(self, current_label, next_label):
        self.current_drink += 1
        if self.current_drink >= len(self.drinks):
            self.current_drink = 0

        if next_label != None:
            next_label.kill()

        next_label = cocos.text.Label(self.drinks[self.current_drink],
                                 font_name='Times New Roman',
                                 font_size=64,
                                 anchor_x='center', anchor_y='center')
        next_label.position = 1424,50
        next_label.scale = 0.5
        self.add(next_label)

        next_label.do((MoveTo((512, 50), 1) | ScaleTo(1, 1)) + Delay(2) + CallFunc(self.next_drink, next_label, current_label) + (ScaleTo(0.5, 1) | MoveTo((-400, 50), 1)))



if __name__ == "__main__":
    cocos.director.director.init(width=1024, height=768, fullscreen=True)
    ticker_layer = BottomTicker()
    main_scene = cocos.scene.Scene(ticker_layer)
    cocos.director.director.run(main_scene)
