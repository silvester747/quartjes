import random
import time
from quartjes.connector.client import ClientConnector


__author__="rob"
__date__ ="$Jul 3, 2011 10:45:28 AM$"

if __name__ == "__main__":
    con = ClientConnector("localhost", 1234)
    con.start()
    while not con.is_connected():
        time.sleep(1)

    database = con.get_service_interface("database")
    exchange = con.get_service_interface("stock_exchange")

    current_drinks = database.get_drinks()
    current_mixes = database.get_mixes()
    current_all = current_drinks + current_mixes

    def update_drinks(drinks):
        global current_drinks
        global current_all
        current_drinks = drinks
        current_all = current_drinks + current_mixes

    def update_mixes(mixes):
        global current_mixes
        global current_all
        current_mixes = mixes
        current_all = current_drinks + current_mixes

    database.subscribe("drinks_updated", update_drinks)
    database.subscribe("mixes_updated", update_mixes)

    while True:
        i = random.randint(0, len(current_all) - 1)

        #if current_drinks[i].price_factor > 1.4:
        #    continue

        #a = random.randint(1, 6 - int((current_drinks[i].price_factor - 1) * 10))
        a = random.randint(1, 6)

        exchange.sell(drink=current_all[i], amount=a)
        time.sleep(5.0)
