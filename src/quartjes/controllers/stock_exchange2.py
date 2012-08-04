from __future__ import print_function
'''
New version of the stock exchange.

Now uses the sales history to determine price fluctuations.

@author: rob
'''

import math
import time

import quartjes.controllers.database
from quartjes.connector.services import remote_method, remote_event

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
        """
        
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
        
    def _process_mix_sales(self, mix):
        """
        Process sales history for a mix. Counts the sales towards the 
        components making up the mix.
        
        Parameters
        ----------
        mix : :class:`quartjes.models.drink.Mix`
            Mix to process
        """
    
    def _notify_next_round(self):
        """
        Fire the on_next_round event.
        """
        self.on_next_round()
