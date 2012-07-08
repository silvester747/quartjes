"""
Server component adding random mixes at random moments
"""

from quartjes.controllers.database import database
from quartjes.models.drink import Mix
import random
import time
import threading

random_mixes = []
max_random_mixes = 5
random_counter = 1
min_interval = 60
max_interval = 120


def create_random_mix():
    """
    Generate a random mix
    """
    
    available_drinks = database.get_drinks()
    available_components = []
    for drink in available_drinks:
        if not isinstance(drink, Mix):
            available_components.append(drink)
    
    nr_of_components = random.randint(2, 4)
    components = [random.choice(available_components) for _ in range(0, nr_of_components)]
    
    mix = Mix()
    mix.name = "CNOC"
    for comp in components:
        mix.insert_drink(comp)
        if comp.alc_perc < 7:
            mix.insert_drink(comp)
    
    return mix

def add_new_mix():
    global random_counter
    global random_mixes
    
    mix = create_random_mix()
    mix.name = "CNOC Mix %i" % random_counter
    random_counter += 1
    if random_counter > max_random_mixes * 2:
        random_counter = 1
    
    if len(random_mixes) > max_random_mixes:
        remove = random_mixes.pop(0)
        database.remove(remove)
    
    random_mixes.append(mix)
    database.add(mix)
    
def run_random_mixer():
    RandomMixThread().start()
    
class RandomMixThread(threading.Thread):
    def __init__(self):
        super(RandomMixThread, self).__init__()
        self.daemon = True

    def run(self):
        while True:
            time.sleep(random.randint(min_interval, max_interval))
            #print("Adding new mix ;-)")
            add_new_mix()