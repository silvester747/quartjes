"""
Calculations to determine trends in sales and prices.

Functionality
-------------
- Get list ordered by percentage increase/decrease price


Limitations
-----------
- Assuming equal intervals between history items, ignore timestamps

@author Rob
"""

from quartjes.controllers.database import default_database
from quartjes.controllers.stock_exchange2 import simulate


def calculate_price_difference(drinks):
    """
    For each drink calculate the absolute and relative difference for each historic price
    against the current price. 
    
    Returns
    -------
    data
        A dictionary of drink: differences. The differences are a list of tuples (absolute, relative) going
        back in time (first pair is latest history). Relative is indexed at 1.0 for current price.
    """

    data = {}
    
    # Fill history data for each drink
    for drink in drinks:
        current_price = drink.current_price
        data[drink] = [(history_item.price-current_price, history_item.price/current_price)
                       for history_item
                       in reversed(drink.price_history)]
    
    return data


def order_by_relative_price_change(drinks, time_window):
    """
    Create a list of drinks ordered by their relative price change.
    
    Parameters
    ----------
    drinks
        Drinks to analyze.
    time_window
        Number of history samples to go back.
    """
    diff_data = calculate_price_difference(drinks)
    price_data = [(drink, price_data[time_window if len(price_data) > time_window else len(price_data)-1][1])
                  for drink, price_data
                  in diff_data.items()]
    price_data.sort(cmp=lambda x, y: cmp(x[1], y[1]))
    return price_data
    

if __name__ == '__main__':
    simulate(60*60)
    #default_database()._dump_drinks()
    test_data = order_by_relative_price_change(default_database().get_drinks(), 10)
    
    import pprint
    pprint.pprint(test_data)