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

    def update_drinks(drinks):
        global current_drinks
        current_drinks = drinks

    database.subscribe("drinks_updated", update_drinks)

    while True:
        i = random.randint(0, len(current_drinks) - 1)

        if current_drinks[i].price_factor > 1.4:
            continue

        a = random.randint(1, 6 - int((current_drinks[i].price_factor - 1) * 10))

        exchange.sell(drink=current_drinks[i], amount=a)
        time.sleep(0.5)
