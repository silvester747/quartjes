import random
import time
import quartjes.controllers.database
import quartjes.connector.services
# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="rob"
__date__ ="$Jul 2, 2011 12:38:26 PM$"

class StockExchange(object):

    def __init__(self):
        self.transactions = []
        self.db = quartjes.controllers.database.database
        self.service = None

    def sell(self, drink, amount):
        local_drink = self.db.get_drink(drink.id)

        if not local_drink:
            return None
        
        total_price = amount * local_drink.sellprice()
        self.transactions.append((local_drink, amount))
        return total_price

    def recalculate_factors(self):
        total_sales = 0
        sales = {}
        drinks = self.db.drinks

        for dr in drinks:
            sales[dr] = 0

        for (dr, amount) in self.transactions:
            total_sales += amount
            total = sales.get(dr)
            if total != None:
                sales[dr] = total + amount

        mean_sales = float(total_sales) / float(len(drinks))

        print("Total: %d, Mean: %f" % (total_sales, mean_sales))

        t = time.time()

        for (dr, amount) in sales.items():
            sales_factor = float(amount) / mean_sales
            if sales_factor < 1.0:
                sales_factor = 0.5 + sales_factor * 0.5
            print(sales_factor)
            dr.price_factor *= sales_factor
            if not dr.history:
                dr.history = []
            dr.history.append((t, dr.sellprice()))

        self.transactions = []

        self.db.set_dirty()
        
    def get_service(self):
        if not self.service:
            self.service = StockExchangeService(self)
        return self.service
    
    def _notify_next_round(self):
        if self.service:
            self.service.notify_next_round(self.db.drinks)

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
        self.sent_topic_update("next_round", drinks=drinks)

    def action_sell(self, drink, amount):
        return self.exchange.sell(drink, amount)

if __name__ == "__main__":
    exchange = StockExchange()
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


