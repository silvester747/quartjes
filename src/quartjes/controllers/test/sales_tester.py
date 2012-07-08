import random
import time
from quartjes.connector.client import ClientConnector
from quartjes.models.drink import Mix


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
        
        #print(current_drinks)
            

    update_drinks(database.get_drinks())

    database.on_drinks_updated += update_drinks

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
