from __future__ import print_function
'''
New version of the stock exchange.

Now uses the sales history to determine price fluctuations.

Possible todos
--------------
* Only consider sales within 2 standard deviations
* Merge sales per unit of time and do the above
* Add a twist to mix prices, e.g. first decrease price of popular mixes and
  then suddenly invert price again

@author: rob
'''

import math
import time
import numpy

import quartjes.controllers.database
from quartjes.connector.services import remote_method, remote_event
from quartjes.models.drink import Mix

debug_mode = False

max_sales_age = 30 * 60 * 1000
"""
Maximum age of sales information in milliseconds.
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

default_demand_time_correction = linear_demand_time_correction
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
                drink.price_factor = demand / average_demand
        
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
        
        for (sales_time, amount, price) in drink.sales_history:
            age = current_time - sales_time
            if age < 0: 
                age = 0
            
            demand += self._demand_time_correction(amount, age) * price
        
        return demand
        
    def _notify_next_round(self):
        """
        Fire the on_next_round event.
        """
        self.on_next_round()

if __name__ == "__main__":
    # Do a self test
    # TODO: use simulated time: replace imported time with manually ticking clock
    import random
    
    debug_mode = True
    
    exchange = StockExchange2()
    
    drinks = exchange._db.get_drinks()
    
    rng = random.Random()
    
    while True:
        for _ in range(0, 10):
            exchange.sell(rng.choice(drinks), rng.randint(1, 10))
            time.sleep(1)
        exchange._recalculate_prices()
    
    
    
    
    