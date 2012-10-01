from __future__ import print_function
'''
New version of the stock exchange
=================================

Now uses the sales history to determine price fluctuations.

Current issues
--------------
* At the start a few drinks have enormous prices
* Pricefactor mostly varies between 0.6 - 1.7 (square) / 0.7 - 2.0 (linear & sqrt), should be more between 0.3 - 3.0

Possible todos
--------------
* Only consider sales within 2 standard deviations
* Merge sales per unit of time and do the above
* Add a twist to mix prices, e.g. first decrease price of popular mixes and
  then suddenly invert price again
* In simulation use alcohol percentage to favor certain drinks

@author: Rob
'''

import math
import time
import numpy

import quartjes.controllers.database
from quartjes.connector.services import remote_method, remote_event
from quartjes.models.drink import Mix

debug_mode = False

max_sales_age = 30 * 60
"""
Maximum age of sales information in seconds.
"""

def linear_demand_time_correction(value, age):
    """
    Linear function to correct demand for age.
    """
    if (age >= max_sales_age):
        return 0.0
    
    return float(value) * (1 - age / max_sales_age)

def sqrt_demand_time_correction(value, age):
    """
    Demand correction based on square root
    """
    if (age >= max_sales_age):
        return 0.0
    
    return float(value) * math.sqrt(1 - age / max_sales_age)
    
def square_demand_time_correction(value, age):
    """
    Demand correction based on square
    """
    if (age >= max_sales_age):
        return 0.0
    
    return float(value) * math.pow(1 - age / max_sales_age, 2)

default_demand_time_correction = sqrt_demand_time_correction
"""
Default function used to for correction of demand over time. Change this if you do not like the default.
"""

class StockExchange2(object):
    """
    Version 2 of the stock exchange.
    
    Exposes the same methods as version 1 for backwards compatibility.
    """
    
    def __init__(self):
        # Time between recalculations
        self._round_time = 20
        
        # Reference to the database
        self._db = quartjes.controllers.database.database
        
        # Function used to change weight of demand over time.
        self._demand_time_correction = default_demand_time_correction
        
    @remote_method
    def sell(self, drink, amount):
        """
        Sell some drinks. The sales will be stored to calculate price fluctuations.
        Returns the real price in quartjes for the entire sale.
        
        Parameters
        ----------
        drink : :class:`quartjes.models.drink.Drink`
            The drink to sell
        amount : integer
            Number of drinks to sell.
            
        Returns
        -------
        total_price : integer
            Total price of the sale in quartjes. If the drink does not exist, this will be None!
        """
        local_drink = self._db.get(drink.id)

        if not local_drink:
            return None
        
        total_price = amount * local_drink.current_price_quartjes
        local_drink.add_sales_history(amount)
        
        if debug_mode:
            print("Sold %d x %s for %d" % (amount, drink.name, total_price))
        
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

    on_next_round = remote_event()
    """
    Event triggered when prices have been recalculated.
    """
    
    def _recalculate_prices(self):
        """
        Recalculate prices based on the demand for each drink.
        
        Price factor is directly related to a demand factor. This already
        includes history.
        
        Todo
        ----
        Remove values outside x standard deviations
        Make sure prices are not below a treshold
        """
        
        if debug_mode:
            print("\n*** Recalculating Prices ***")
        
        drinks = self._db.get_drinks()
        if len(drinks) == 0:
            return # Nothing to do here
        
        average_demand, demand_per_drink = self._calculate_demands(drinks)
        
        for (drink, demand) in demand_per_drink:
            if not isinstance(drink, Mix):
                drink.price_factor = average_demand / demand
        
        for drink in drinks:
            if isinstance(drink, Mix):
                drink.update_properties()
            drink.add_price_history()
            
            if debug_mode:
                print("%s : Factor = %f, Price = %d" % (drink.name, drink.price_factor, drink.current_price_quartjes))
        
        self._db.force_save()
        self._notify_next_round()
        
        if debug_mode:
            print()
    
    def _calculate_demands(self, drinks):
        """
        Calculate the demands of all drinks.
        * Make sure mix sales are processed
        * If demand = 0 (e.g. no sales at all or only old sales) use the
          average demand (calculated without the 0s)
        
        Parameters
        ----------
        drinks : iterable of :class:`quartjes.models.drink.Drink`
            Drinks to calculate demand for.
        
        Returns
        -------
        average_demand : float
            The average demand after all calculations and corrections.
        demand_per_drink : list of tuples
            A list of tuples where each tuple is (drink, demand)
        
        """
        
        for drink in drinks:
            if isinstance(drink, Mix):
                drink.update_components_sale()
        
        total_demand = 0.0
        demand_per_drink = [] # Will contain tuples of (drink, demand)
        demand_values = [] # Only the demand values for standard deviation calculation
        drinks_without_sales = []
        
        for drink in drinks:
            if not isinstance(drink, Mix):
                demand = self._calculate_demand(drink)
                total_demand += demand
                if demand > 0:
                    demand_per_drink.append((drink, demand))
                    demand_values.append(demand)
                else:
                    drinks_without_sales.append(drink)
        
        average_demand = total_demand / len(demand_per_drink)
        std_deviation = numpy.std(demand_values)

        for drink in drinks_without_sales:
            demand_per_drink.append((drink, average_demand))

        if debug_mode:
            print("Average demand: %f" % average_demand)
            print("Std deviation: %f" % std_deviation)
            print("Nr of drinks without sales: %d" % len(drinks_without_sales))
        
        
        return average_demand, demand_per_drink
        
    
    def _calculate_demand(self, drink):
        """
        Calculate the total demand for the given drink. Takes in account a 
        limited amount of history. Each sale is weighted for the amount of
        time passed since the sale. Also the sale price is taken into account.
        
        Parameters
        ----------
        drink : :class:`quartjes.models.drink.Drink`
            Drink to calculate demand for.
            
        Returns
        -------
        demand : float
            Total demand over a limited period weighed for time passed.
        """
        current_time = time.time()
        demand = 0.0
        
        for (sales_time, amount, _, price_factor) in drink.sales_history:
            age = current_time - sales_time
            if age < 0: 
                age = 0
            
            demand += self._demand_time_correction(amount, age) * price_factor
        
        return demand
        
    def _notify_next_round(self):
        """
        Fire the on_next_round event.
        """
        self.on_next_round()

class time_mock(object):
    """
    Mock class for the time module.
    Use this to quickly skip forward in time. It starts with the time at which it is instantiated and then increases
    with one second every time do_tick is called.
    """
    
    def __init__(self):
        self._now = time.time()
    
    def do_tick(self):
        self._now += 1.0
    
    def time(self):
        return self._now

def install_time_mock():
    """
    Replace the installed time module with a mock class
    """
    global time
    time = time_mock()
    
    quartjes.models.drink.time = time

class PriceAgnosticDrinkRandomizer(object):
    def __init__(self, drinks):
        self._drinks = drinks
        
        self._max_priority = 0
        self._prioritized_drinks = {}
        
        self.update()
    
    def update(self):
        new_drinks = {}
        position = 0
        for drink in self._drinks:
            new_drinks[position] = drink
            position += int(1000.0 / drink.price_factor)
        
        self._max_priority, self._prioritized_drinks = position, new_drinks

    
    def get_random_drink(self):
        rand_pos = random.randint(0, self._max_priority)
        pos = 0
        for p in self._prioritized_drinks:
            if p > pos and p <= rand_pos:
                pos = p
        
        return self._prioritized_drinks[pos]

if __name__ == "__main__":
    # Do a self test
    import random
    
    debug_mode = True
    install_time_mock()
    
    exchange = StockExchange2()
    exchange._db.reset()
    drinks = exchange._db.get_drinks()
    rng = random.Random()
    randomizer = PriceAgnosticDrinkRandomizer(drinks)
    
    price_csv = open("stock_exchange2_prices.csv", "w")
    demand_csv = open("stock_exchange2_demands.csv", "w")
    
    names = ["time"]
    for drink in drinks:
        names.append(drink.name)
    print(";".join(names), file=price_csv)
    print(";".join(names), file=demand_csv)
    
    start_time = time.time()
    
    try:
        # run for 12 hours
        run_time = 12 * 60 * 60
        runs = run_time / exchange.get_round_time()
        for _ in range(0, runs):
            for _ in range(0, exchange.get_round_time()):
                exchange.sell(randomizer.get_random_drink(), rng.randint(1, 10))
                time.do_tick()
            exchange._recalculate_prices()
            randomizer.update()
            
            prices = [str(time.time() - start_time)]
            demands = [str(time.time() - start_time)]
            for drink in drinks:
                prices.append(str(drink.price_factor))
                demands.append(str(exchange._calculate_demand(drink)))
            print(";".join(prices), file=price_csv)
            print(";".join(demands), file=demand_csv)
    finally:
        price_csv.close()
        demand_csv.close()
    
    
    
    