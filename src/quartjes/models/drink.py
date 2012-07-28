# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$5-jun-2011 12:34:35$"

from quartjes.util.classtools import QuartjesBaseClass
from numpy import array

class Drink(QuartjesBaseClass):
    """
    Drink class
    """

    def __init__(self, name="Unnamed", alc_perc = 0.0,color = (255,255,255),unit_price = 0.70,price_factor = 1.0,unit_amount = 200):
        super(Drink, self).__init__()
        self.name = name
        self.alc_perc = alc_perc
        self.color = color
        self.unit_price = unit_price
        self.unit_amount = unit_amount
        self.price_factor = price_factor        
        self.history = None

    def price_per_liter(self):
        return self.unit_price / (float(self.unit_amount) / 1000)

    def sellprice(self):
        return self.unit_price * self.price_factor

    def sellprice_quartjes(self):
        return int(round(self.sellprice()*10))

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
        self.discount = 0.8

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

    def insert_drink(self,drink):
        """Add a drink to the mix"""
        self._drinks.append(drink)
        self.update_properties()

    def remove_drink(self,index):
        """Remove a drink from the mix"""
        self._drinks.pop(index)
        self.update_properties()

    def update_properties(self):
        """Recalculate mix properties"""
        parts = len(self._drinks)
        if parts > 0:
            self.unit_price = 0
            self.alc_perc = 0
            self.price_factor = 0
            color = array([0,0,0])
            for d in self._drinks:
                self.alc_perc = self.alc_perc + float(d.alc_perc) / parts
                color += array(d.color)/parts
                self.unit_price = self.unit_price + (d.price_per_liter()/parts)*(float(self.unit_amount)/1000)
                self.price_factor = self.price_factor + float(d.price_factor)/parts
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
    print "Selling price = " + str(m.sellprice()) + " euro"