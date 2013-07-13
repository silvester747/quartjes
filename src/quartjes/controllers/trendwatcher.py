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

def calculate_absolute_factor_difference_data():
    """
    Get all drink history from the database. Calculate for each history item
    the difference with the current price.
    """
    drinks = default_database().get_drinks()
    
    data = {}
    
    # Fill history data for each drink
    for drink in drinks:
        current_price_factor = drink.price_factor
        factor_diffs = []
        for history_item in reversed(drink.price_history):
            factor_diffs.append(current_price_factor / history_item.price_factor)
        data[drink] = factor_diffs
    
    return data      