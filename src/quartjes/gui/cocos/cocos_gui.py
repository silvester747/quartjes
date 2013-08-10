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
import cocos.layer
import cocos.scenes.transitions
import cocos.director
from cocos.sprite import Sprite
import pyglet.resource
import random

from quartjes.connector.client import ClientConnector
from quartjes.gui.cocos.center_display import CenterLayer
from quartjes.gui.cocos.ticker import BottomTicker

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
        

            

class CocosGui(object):
    """
    Main object containing the Cocos2D GUI.
    Initialize and start this object to start a show.
    """

    def __init__(self, 
                 hostname=None, 
                 port=1234, 
                 width=1024, 
                 height=768,
                 fullscreen=True, 
                 explanation_interval=9):
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
        self._center_layer = None
        self._title_layer = None
        self._mix_layer = None
        self._connector = None

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
        print("Loaded libraries:")
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
        if not self._center_layer:
            self._center_layer = CenterLayer(screen_width=self._width)
        if not self._title_layer:
            self._title_layer = TitleLayer()

        self._ticker_layer.update_drinks(self._drinks)

        scene = cocos.scene.Scene(self._ticker_layer, self._center_layer, self._title_layer)

        self._ticker_layer.on_focus_changed += lambda sender, drink: self._center_layer.show_drink(drink)

        self._center_layer.show_explanation()

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
            self._center_layer.show_explanation()
            
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
    gui = CocosGui(hostname=args.hostname, 
                   port=args.port, 
                   width=args.width, 
                   height=args.height,
                   fullscreen=args.fullscreen)
    gui.start()


if __name__ == "__main__":
    run_cocos_gui()
