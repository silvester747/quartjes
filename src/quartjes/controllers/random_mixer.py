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
mix_name_format = "CNOC Mix %i"
mix_name_prefix = "CNOC Mix "

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
    """
    Create a random mix and add it to the database.
    If the maximum number of mixes is already present, the oldest is removed.
    """
    global random_counter
    global random_mixes
    
    mix = create_random_mix()
    mix.name = mix_name_format % (random_counter)
    random_counter += 1
    if random_counter > max_random_mixes * 2:
        random_counter = 1
    
    if len(random_mixes) > max_random_mixes:
        remove = random_mixes.pop(0)
        try:
            database.remove(remove)
        except KeyError:
            pass # Drink might have been removed by admin
    
    random_mixes.append(mix)
    database.add(mix)
    
def find_existing_mixes():
    """
    Search the database for already existing random mixes. Searches for drinks using the default name given to random mixes.
    Adds them to the list of active mixes and if the number exceeds the maximum, some mixes are removed.
    """
    global random_mixes
    
    current_drinks = database.get_drinks()
    for drink in current_drinks:
        if isinstance(drink, Mix):
            if drink.name.startswith(mix_name_prefix):
                random_mixes.append(drink)
    
    while len(random_mixes) > max_random_mixes:
        remove = random_mixes.pop(0)
        try:
            database.remove(remove)
        except KeyError:
            pass # Drink might have been removed by admin
        
    
def run_random_mixer():
    """
    Entry point for the random mixer. Call this on the server to start.
    """
    find_existing_mixes()
    RandomMixThread().start()
    
class RandomMixThread(threading.Thread):
    """
    Thread for adding the random mixes. Sleeps most of the time unless it is time to add a new random mix.
    """
    def __init__(self):
        super(RandomMixThread, self).__init__()
        self.daemon = True

    def run(self):
        while True:
            time.sleep(random.randint(min_interval, max_interval))
            #print("Adding new mix ;-)")
            add_new_mix()