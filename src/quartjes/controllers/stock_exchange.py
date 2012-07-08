"""
Stock exchange controller. Changes prices of drinks according to sales.
"""

import threading
import time
import quartjes.controllers.database
from quartjes.models.drink import Mix, Drink
from quartjes.connector.services import remote_service, remote_method, remote_event
import random

__author__ = "Rob van der Most"

debug_mode = False

default_round_time = 20

@remote_service
class StockExchange(object):
    """
    The Stock Exchange service controls the fluctuation of prices similar to
    a real stock exchange.
    
    Parameters
    ----------
    start_thread : bool
        Should a control thread be started. Default is true.
    damp_sales : integer
        Amount of sales to add to each component to dampen fluctuations.
    max_price_factor : double
        Maximum value the price factor of each drink may reach.
    min_price_factor : double
        Minimum value the price factor of each drink may reach.
    """

    def __init__(self, start_thread=True, damp_sales=2, max_price_factor=3,
                 min_price_factor=0.4, round_time=None):
        self._transactions = []
        self._db = quartjes.controllers.database.database
        self._max_history = 120

        if round_time:
            self._round_time = round_time
        else:
            self._round_time = default_round_time
        self._damp_sales = damp_sales
        self._max_price_factor = max_price_factor
        self._min_price_factor = min_price_factor
        self._min_mix_discount = 0.5
        self._max_mix_discount = 0.9

        if start_thread:
            self._thread = StockExchangeUpdateThread(self)
            self._thread.start()

    @remote_method
    def sell(self, drink, amount):
        """
        Sell some drinks. The sales will be stored to calculate price fluctuations.
        Returns the real price for the entire sale.
        
        Parameters
        ----------
        drink : :class:`quartjes.models.drink.Drink`
            The drink to sell
        amount : integer
            Number of drinks to sell.
            
        Returns
        -------
        total_price : integer
            Total price of the sale. If the drink does not exist, this will be None!
        """
        local_drink = self._db.get(drink.id)

        if not local_drink:
            return None
        
        total_price = amount * local_drink.sellprice_quartjes()
        self._transactions.append((local_drink, amount))
        return total_price
    
    @remote_method
    def set_round_time(self, time):
        """
        Update the time in seconds between rounds. After each round the prices
        are recalculated based on the amount of sales.
        
        Parameters
        ----------
        time : integer
            New round time in seconds.
        """
        self._round_time = time
    
    @remote_method
    def get_round_time(self):
        """
        Get the time in seconds between rounds.
        
        Returns
        -------
        time : integer
            Time in seconds between rounds.
        """
        return self._round_time

    def _recalculate_factors(self):
        """
        Recalculate all prices based on the current sales.
        """
        sales = {}
        drinks = self._db.get_drinks()
        total_sales = 0
        component_count = 0

        for dr in drinks:
            if not isinstance(dr, Mix):
                sales[dr] = 0
                component_count += 1

        for (dr, amount) in self._transactions:
            if isinstance(dr, Mix):
                parts = dr.drinks
                amount *= 1.0 / len(parts)
                for p in parts:
                    total = sales.get(p)
                    if total != None:
                        sales[p] = total + amount
                        total_sales += amount

            else:
                total = sales.get(dr)
                if total != None:
                    sales[dr] = total + amount
                    total_sales += amount

        mean_sales = float(total_sales) / float(len(drinks))

        if debug_mode:
            print("Total sales: %d, Mean sales: %f" % (total_sales, mean_sales))

        t = time.time()

        if total_sales > 0:
            
            total_factors = 0
            min_price_hits = 0
            max_price_hits = 0
            for (dr, amount) in sales.items():
                sales_factor = float(amount + self._damp_sales) / (mean_sales + self._damp_sales)
                dr.price_factor *= sales_factor
                if dr.price_factor > self._max_price_factor:
                    dr.price_factor = self._max_price_factor
                    max_price_hits += 1
                elif dr.price_factor < self._min_price_factor:
                    dr.price_factor = self._min_price_factor
                    min_price_hits += 1
    
                total_factors += dr.price_factor
                
                if debug_mode:
                    print("Factor for %s = %f" % (dr.name, dr.price_factor))
    
            if debug_mode:
                print("Amount of components: %i, Total factors: %f" % (component_count, total_factors))
    
            skew = total_factors / float(component_count)
            skew_correction = (float(component_count - (max_price_hits + min_price_hits)) /
                               (total_factors - (max_price_hits + min_price_hits)))
    
            if debug_mode:
                print("Skew=%f Skew correction=%f" % (skew, skew_correction))
 
            total_factors = 0   
            for (dr, amount) in sales.items():
                if dr.price_factor > self._min_price_factor and dr.price_factor < self._max_price_factor:
                    dr.price_factor *= skew_correction
                total_factors += dr.price_factor
                if debug_mode:
                    print("Corrected factor for %s = %f" % (dr.name, dr.price_factor))

            skew = total_factors / float(component_count)
            if debug_mode:
                print("Final skew=%f" % skew)
    
        for drink in drinks:
            if isinstance(drink, Mix):
                drink.update_properties()
                drink.discount = (self._min_mix_discount + 
                                  random.random() * (self._max_mix_discount - self._min_mix_discount))
            if not drink.history:
                drink.history = []
            drink.history.append((t, drink.sellprice_quartjes()))
            if len(drink.history) > self._max_history:
                drink.history = drink.history[-self._max_history:]

        self._transactions = []

        self._db.force_save()
        self._notify_next_round()
        
    def stop(self):
        print("Stock exchange stopping in 1 second...")
        self._thread.stop()

    on_next_round = remote_event()
    
    def _notify_next_round(self):
        self.on_next_round()


class StockExchangeUpdateThread(threading.Thread):
    def __init__(self, exchange):
        super(StockExchangeUpdateThread, self).__init__()
        self._exchange = exchange
        self._running = True

    def run(self):
        while self._running:
            # We use a manual counter, so we can react to updates to the round
            # time instantly.
            time_spend = 0
            while time_spend < self._exchange._round_time:
                if self._running:
                    time.sleep(1)
                    time_spend += 1
                else:
                    return
            self._exchange._recalculate_factors()
            
    def stop(self):
        self._running = False




