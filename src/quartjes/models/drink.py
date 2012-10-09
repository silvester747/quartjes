# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$5-jun-2011 12:34:35$"

from quartjes.util.classtools import QuartjesBaseClass
from numpy import array
import time

def to_quartjes(price):
    """
    Convert price in euro to price in quartjes.
    """
    return int(round(price * 10))


class Drink(QuartjesBaseClass):
    """
    Base class to model all drinks.
    
    Attributes
    ----------
    name
    alc_perc
    color
    unit_price
    price_factor
    unit_amount
    price_history
    sales_history
    """

    MAX_PRICE_HISTORY = 120
    """
    Maximum number of entries in the price history.
    """

    MAX_SALES_HISTORY = 1200
    """
    Maximum number entries in the sales history.
    """
    
    DEFAULT_COLOR = (255, 255, 255)
    """
    Default color for drinks.
    """

    def __init__(self, name="Unnamed", alc_perc = 0.0, color = None, unit_price = 0.70, price_factor = 1.0, unit_amount = 200):
        super(Drink, self).__init__()
        self.name = name
        self.alc_perc = alc_perc
        self.color = color
        self.unit_price = unit_price
        self.unit_amount = unit_amount
        self.price_factor = price_factor        
        self._price_history = []
        self._sales_history = []
    
    @property
    def name(self):
        """
        Name of the drink.
        """
        return self._name
    
    @name.setter
    def name(self, value):
        if value is None:
            raise TypeError("Drink.name is not allowed to be None")
        value = str(value)
        if value == "":
            raise ValueError("Drink.name should be a proper, non-empty string")
        self._name = value
    
    @property
    def alc_perc(self):
        """
        Alcohol percentage of the drink. Value between 0.0 and 100.0
        """
        return self._alc_perc
    
    @alc_perc.setter
    def alc_perc(self, value):
        if value is None:
            raise TypeError("Drink.alc_perc is not allowed to be None")
        if value < 0 or value > 100:
            raise ValueError("Drink.alc_perc must be [0.0-100.0]")
        self._alc_perc = float(value)
    
    @property
    def color(self):
        """
        Color of the drink.
        Must be an iterable of either (r, g, b) or (r, g, b, a).
        """
        return self._color
    
    @color.setter
    def color(self, value):
        if value is None:
            self._color = self.DEFAULT_COLOR
            return # No need to check
        if len(value) < 3 or len(value) > 4:
            raise ValueError("Drink.color must be either (r, g, b) or (r, g, b, a)")
        proper_color = []
        for part in value:
            part = int(part)
            if part < 0 or part > 255:
                raise ValueError("Values in Drink.color must be [0-255]")
            proper_color.append(part)
        self._color = tuple(proper_color)
              
    @property
    def unit_price(self):
        """
        Price in euro per unit.
        """
        return self._unit_price
    
    @unit_price.setter
    def unit_price(self, value):
        if value is None:
            raise TypeError("Drink.unit_price is not allowed to be None")
        value = float(value)
        if value < 0.0:
            raise ValueError("Drink.unit price must be > 0.0")
        self._unit_price = value
    
    @property
    def unit_amount(self):
        """
        Size of the drink per unit in milliliters.
        """
        return self._unit_amount
    
    @unit_amount.setter
    def unit_amount(self, value):
        if value is None:
            raise TypeError("Drink.unit_amount is not allowed to be None")
        value = float(value)
        if value < 0.0:
            raise ValueError("Drink.unit_amount must be > 0.0")
        self._unit_amount = value
    
    @property
    def price_factor(self):
        """
        Factor used to determine the price in the stock exchange.
        Must be > 0 or a ValueError will be raised.
        """
        return self._price_factor
    
    @price_factor.setter
    def price_factor(self, value):
        if value <= 0:
            raise ValueError
        # Make sure this is a float
        self._price_factor = float(value)
    
    @property
    def price_history(self):
        """
        Historic prices of this drink. Tuple of tuples. Each tuple is (timestamp, price).
        Timestamp is time in seconds since epoch. Price is in euro.
        You should not modify this property directly.
        """
        return tuple(self._price_history)
    
    @property
    def sales_history(self):
        """
        History of sales for this drink. Tuple of tuples. Each tuple is (timestamp, amount, price, price_factor).
        Timestamp is time in seconds since epoch. Price is in euro.
        You should not modify this property directly.
        """
        return tuple(self._sales_history)
    
    @property
    def current_price(self):
        """
        Current price in euro
        """
        return self.unit_price * self._price_factor
    
    @property
    def current_price_quartjes(self):
        """
        Current price in quartjes.
        """
        return to_quartjes(self.current_price)
    
    def clear_price_history(self):
        """
        Remove all historic prices of this drink.
        """
        self._price_history = []
        
    def clear_sales_history(self):
        """
        Remove all sales history.
        """
        self._sales_history = []
    
    def add_price_history(self, timestamp=None, price=None):
        """
        Add a new historic price.
        
        Parameters
        ----------
        timestamp : float
            Time in seconds since epoch (time.time())
        price : float
            Price in euro.
        """
        if not timestamp:
            timestamp = time.time()
        if not price:
            price = self.current_price
        
        self._price_history.append((timestamp, price))
        if len(self._price_history) > self.MAX_PRICE_HISTORY:
            self._price_history = self._price_history[-self.MAX_PRICE_HISTORY:]

    def add_sales_history(self, amount, timestamp=None, price=None, price_factor=None):
        """
        Add sales to the history.
        
        Parameters
        ----------
        timestamp : float
            Time in seconds since epoch (time.time())
        amount : int
            Number of units sold.
        price : float
            Price in euro.
        """
        if not timestamp:
            timestamp = time.time()
        if not price:
            price = self.current_price
        if not price_factor:
            price_factor = self.price_factor
        
        self._sales_history.append((timestamp, amount, price, price_factor))
        if len(self._sales_history) > self.MAX_SALES_HISTORY:
            self._sales_history = self._sales_history[-self.MAX_SALES_HISTORY:]

    def price_per_liter(self):
        return self.unit_price / (float(self.unit_amount) / 1000)

    def sellprice(self):
        assert False, "Please do not call this function anymore"

    def sellprice_quartjes(self):
        assert False, "Please do not call this function anymore"

    def __eq__(self, other):
        if other == None:
            return False
        return vars(self)==vars(other)

    def __ne__(self, other):
        if other == None:
            return True
        return vars(self)!=vars(other)

class Mix(Drink):
    """
    Mix class
    """
    def __init__(self,name="Unnamed",drinks = None,unit_amount = 200):
        super(Mix, self).__init__(unit_amount = unit_amount, name=name)
        if drinks:
            self._drinks = drinks
        else:
            self._drinks = []
        self._discount = 0.8
        
        self._last_component_sales_update = 0

        self.update_properties()

    @property
    def drinks(self):
        """
        The drinks used to make this mix.
        """
        return self._drinks
    
    @drinks.setter
    def drinks(self, value):
        if value:
            self._drinks = value
        else:
            self._drinks = []
        
        self.update_properties()
    
    @property
    def last_component_sales_update(self):
        """
        Last time the sales were updated to the components making up the mix.
        """
        return self._last_component_sales_update
    
    @last_component_sales_update.setter
    def last_component_sales_update(self, value):
        self._last_component_sales_update = value

    @property
    def discount(self):
        """
        Percentage of the normal added prices of the components that will be
        the actual price of the mix. Makes mixes cheaper than their components.
        """
        return self._discount
    
    @discount.setter
    def discount(self, value):
        self._discount = value

    def insert_drink(self,drink):
        """Add a drink to the mix"""
        self._drinks.append(drink)
        self.update_properties()

    def remove_drink(self,index):
        """Remove a drink from the mix"""
        self._drinks.pop(index)
        self.update_properties()

    def update_components_sale(self):
        """
        Update the sales of the components using the sales of this mix.
        Internally the timestamp of the last sales updated to the components
        is stored to make sure each sale is only processed once.
        """
        new_last_update_time = 0
        parts = len(self._drinks)
        for (timestamp, amount, price, price_factor) in self._sales_history:
            if timestamp > self._last_component_sales_update:
                for component in self._drinks:
                    component.add_sales_history(amount / parts, timestamp, price / parts, price_factor)
                if timestamp > new_last_update_time:
                    new_last_update_time = timestamp
        
        if new_last_update_time > self._last_component_sales_update:
            self._last_component_sales_update = new_last_update_time

    def update_properties(self):
        """Recalculate mix properties"""
        parts = len(self._drinks)
        if parts > 0:
            self.unit_price = 0
            self.alc_perc = 0
            self._price_factor = 0
            color = array([0,0,0])
            for d in self._drinks:
                self.alc_perc = self.alc_perc + float(d.alc_perc) / parts
                color += array(d.color)/parts
                self.unit_price = self.unit_price + (d.price_per_liter()/parts)*(float(self.unit_amount)/1000)
                self._price_factor = self._price_factor + float(d.price_factor)/parts
            self.color = tuple(color)
            self.price_factor *= self.discount

if __name__ == "__main__":
    d1 = Drink('cola',color = (0,0,0),alc_perc = 0,unit_price = 0.70, unit_amount = 200)
    d2 = Drink('bacardi',color = (255,255,255),alc_perc = 40,unit_price = 2, unit_amount = 50)
    d1.price_factor = 0.8
    d2.price_factor = 0.9
    print d1
    print d2

    # example mix, 3 parts cola 1 part bacardi
    m = Mix(name = 'baco',drinks = [d1,d1,d1,d2],unit_amount = 200)
    
    print m
    print "Liter price = " + str(m.price_per_liter()) + " euro"
    print "Selling price = " + str(m.current_price) + " euro"