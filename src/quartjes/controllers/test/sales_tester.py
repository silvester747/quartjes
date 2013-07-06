import random
import time
from quartjes.connector.client import ClientConnector

debug_memory = False

if debug_memory:
    from meliae import scanner
else:
    scanner = None

__author__="rob"
__date__ ="$Jul 3, 2011 10:45:28 AM$"

if __name__ == "__main__":
    con = ClientConnector("localhost", 1234)
    con.start()
    while not con.is_connected():
        time.sleep(1)

    database = con.database
    exchange = con.stock_exchange

    current_drinks = {}
    max_position = 0
    
    mem_counter = 0

    def update_drinks(drinks):
        global current_drinks
        global max_position
        
        new_drinks = {}
        position = 0
        for drink in drinks:
            #print(drink)
            new_drinks[position] = drink
            position += int(1000.0 / drink.price_factor)
        
        current_drinks, max_position = new_drinks, position
        
        # Dump memory map at this point
        if debug_memory:
            global mem_counter
            mem_counter += 1
            scanner.dump_all_objects('memory%04d.json' % mem_counter)
            

    update_drinks(database.get_drinks())

    tmp = database.on_drinks_updated 
    tmp += update_drinks

    while True:
        rand_pos = random.randint(0, max_position)
        pos = 0
        for p in current_drinks.keys():
            if p > pos and p <= rand_pos:
                pos = p

        a = random.randint(1, 6)

        try:
            exchange.sell(drink=current_drinks[pos], amount=a)
        except:
            pass
        time.sleep(1.0)
