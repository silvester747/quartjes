'''
Give random mixes temporary discounts.

@author: rob
'''

from quartjes.controllers.database import default_database
from quartjes.models.drink import Mix
import random
import time
import threading

min_interval = 60
max_interval = 120
discount_factor = 0.5

def run_mix_discounter():
    """
    Entry point for the random mixer. Call this on the server to start.
    """
    MixDiscounterThread().start()


    
class MixDiscounterThread(threading.Thread):
    """
    Thread for adding the random mixes. Sleeps most of the time unless it is time to add a new random mix.
    """
    def __init__(self):
        super(MixDiscounterThread, self).__init__()
        self.daemon = True
        
        self._current_mix = None
        self._old_discount = 0.8
        
        self._random = random.Random()
        
    def get_random_mix(self):
        drinks = default_database().get_drinks()
        mix = self._random.choice(drinks)
        while not isinstance(mix, Mix):
            mix = self._random.choice(drinks)
        
        return mix

    def run(self):
        while True:
            time.sleep(self._random.randint(min_interval, max_interval))
            
            if self._current_mix:
                self._current_mix.discount = self._old_discount
            
            self._current_mix = self.get_random_mix()
            self._current_mix.discount *= discount_factor
            
            print("Mix %s now has discount %f" % (self._current_mix.name, self._current_mix.discount))
            
