import threading
import random
import time
import quartjes.controllers.database
from quartjes.models.drink import Mix
from quartjes.connector.services import remote_service, remote_method, remote_event

__author__ = "Rob van der Most"

debug_mode = False

@remote_service
class StockExchange(object):

    def __init__(self, start_thread=True):
        self.transactions = []
        self.db = quartjes.controllers.database.database
        self.service = None
        self.max_history = 120

        self.round_time = 30

        if start_thread:
            self.thread = StockExchangeUpdateThread(self)
            self.thread.start()

    @remote_method
    def sell(self, drink, amount):
        local_drink = self.db.get(drink.id)

        if not local_drink:
            return None
        
        total_price = amount * local_drink.sellprice_quartjes()
        self.transactions.append((local_drink, amount))
        return total_price

    def recalculate_factors(self):
        sales = {}
        drinks = self.db.get_drinks()
        total_sales = len(drinks)

        for dr in drinks:
            sales[dr] = 1

        for (dr, amount) in self.transactions:
            if isinstance(dr, Mix):
                parts = dr.drinks
                amount *= 1.0 / len(parts)
                for p in parts:
                    total = sales.get(p)
                    if total != None:
                        sales[dr] = total + amount
                        total_sales += amount

            else:
                total = sales.get(dr)
                if total != None:
                    sales[dr] = total + amount
                    total_sales += amount

        mean_sales = float(total_sales) / float(len(drinks))

        if debug_mode:
            print("Total: %d, Mean: %f" % (total_sales, mean_sales))

        t = time.time()

        total_factors = 0
        for (dr, amount) in sales.items():
            sales_factor = float(amount) / mean_sales
            """
            #Als de huidige price factor hoog is: stijging dempen
            #TODO: we kunnen ook alleen dempen als > 1,2 bijvoorbeeld
            if dr.price_factor > 1: #prijs is hoger dan normaal
                if sales_factor > 1: #hij blijft stijgen: dempen
                    dampvalue = 1+((sales_factor-1)/dr.price_factor)
                    dr.price_factor *= dampvalue
                else: #hij gaat dalen: niet dempen
                    dr.price_factor *= sales_factor
            else: #prijs is lager dan normaal
                if sales_factor > 1: #hij blijft dalen: dempen
                    dampvalue = 1+((sales_factor-1)/dr.price_factor)
                    dr.price_factor *= dampvalue
                else: #hij gaat stijgen: niet dempen
                    dr.price_factor *= sales_factor
            """
            dr.price_factor *= sales_factor
            if dr.price_factor > 3:
                dr.price_factor = 3
            elif dr.price_factor < 0.4:
                dr.price_factor = 0.4

            total_factors += dr.price_factor
            if not dr.history:
                dr.history = []
            dr.history.append((t, dr.sellprice_quartjes()))
            if len(dr.history) > self.max_history:
                dr.history = dr.history[-self.max_history:]

        if debug_mode:
            print("Total factors: %f" % total_factors)

        skew = float(len(drinks)) / total_factors

        if debug_mode:
            print("Skew: %f" % skew)

        for (dr, amount) in sales.items():
            dr.price_factor *= skew

        mixes = self.db.get_mixes()
        for m in mixes:
            m.update_properties()

        self.transactions = []

        self.db.set_dirty()
        self._notify_next_round()
        
    def stop(self):
        print("Stock exchange stopping in 1 second...")
        self.thread.stop()

    on_next_round = remote_event()
    
    def _notify_next_round(self):
        self.on_next_round()


class StockExchangeUpdateThread(threading.Thread):
    def __init__(self, exchange):
        super(StockExchangeUpdateThread, self).__init__()
        self.exchange = exchange
        self.running = True

    def run(self):
        while (self.running):
            for _ in range(0, self.exchange.round_time):
                if self.running:
                    time.sleep(1)
                else:
                    return
            self.exchange.recalculate_factors()
            
    def stop(self):
        self.running = False


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


