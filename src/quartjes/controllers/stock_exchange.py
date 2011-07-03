import threading
import random
import time
import quartjes.controllers.database
import quartjes.connector.services
# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="rob"
__date__ ="$Jul 2, 2011 12:38:26 PM$"

class StockExchange(object):

    def __init__(self, start_thread=True):
        self.transactions = []
        self.db = quartjes.controllers.database.database
        self.service = None

        self.min_factor = 0.5
        self.max_factor = 2.0
        self.max_history = 120

        self.round_time = 10

        if start_thread:
            self.thread = StockExchangeUpdateThread(self)
            self.thread.start()

    def sell(self, drink, amount):
        local_drink = self.db.get_drink(drink.id)

        if not local_drink:
            return None
        
        total_price = amount * local_drink.sellprice()
        self.transactions.append((local_drink, amount))
        return total_price

    def recalculate_factors(self):
        sales = {}
        drinks = self.db.get_drinks()
        total_sales = len(drinks)

        for dr in drinks:
            sales[dr] = 1

        for (dr, amount) in self.transactions:
            total = sales.get(dr)
            if total != None:
                sales[dr] = total + amount
                total_sales += amount

        mean_sales = float(total_sales) / float(len(drinks))

        print("Total: %d, Mean: %f" % (total_sales, mean_sales))

        t = time.time()

        total_factors = 0
        for (dr, amount) in sales.items():
            sales_factor = float(amount) / mean_sales
            dr.price_factor *= sales_factor
            if dr.price_factor < self.min_factor:
                dr.price_factor = self.min_factor
            if dr.price_factor > self.max_factor:
                dr.price_factor = self.max_factor
            total_factors += dr.price_factor
            if not dr.history:
                dr.history = []
            dr.history.append((t, dr.sellprice()))
            if len(dr.history) > self.max_history:
                dr.history = dr.history[-self.max_history:]

        print("Total factors: %f" % total_factors)

        skew = float(len(drinks)) / total_factors

        print("Skew: %f" % skew)

        for (dr, amount) in sales.items():
            dr.price_factor *= skew

        self.transactions = []

        self.db.set_dirty()
        self._notify_next_round()
        
    def get_service(self):
        if not self.service:
            self.service = StockExchangeService(self)
        return self.service
    
    def _notify_next_round(self):
        if self.service:
            self.service.notify_next_round(self.db.get_drinks())

class StockExchangeUpdateThread(threading.Thread):
    def __init__(self, exchange):
        super(StockExchangeUpdateThread, self).__init__()
        self.exchange = exchange

    def run(self):
        while (True):
            time.sleep(self.exchange.round_time)
            self.exchange.recalculate_factors()

class StockExchangeService(quartjes.connector.services.Service):
    """
    Service to access the stock exchange.

    Service name: stock_exchange
    
    Supported methods
    =================
    
    sell(drink, amount)
    
    
    Supported topics
    ================

    next_round(drinks)

    """

    def __init__(self, exchange=None):
        super(StockExchangeService, self).__init__(name="stock_exchange")
        self.exchange = exchange

    def notify_next_round(self, drinks):
        self.send_topic_update("next_round", drinks=drinks)

    def action_sell(self, drink, amount):
        return self.exchange.sell(drink, amount)

if __name__ == "__main__":
    exchange = StockExchange(start_thread=False)
    drinks = exchange.db.drinks

    while True:
        for d in drinks:
            print("%s: %f" % (d.name, d.sellprice()))

        inp = raw_input()
        if len(inp) > 0:
            exit()

        for x in range(0, random.randint(30, 60)):
            i = random.randint(0, len(drinks) - 1)
            a = random.randint(1, 10)

            c = random.randint(1, int(drinks[i].price_factor))
            if c > 1:
                continue
            exchange.sell(drinks[i], a)

        exchange.recalculate_factors()


