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
    __serialize__ = ["name", "alc_perc", "color", "unit_price", "price_factor", "unit_amount", "history"]
    
    def __init__(self, name="Unnamed", alc_perc = 0,color = (255,255,255),price_per_liter = 70,price_factor = 1,amount = 200):
        self.name = name
        self.alc_perc = alc_perc
        self.color = color
        self.unit_price = price_per_liter
        self.unit_amount = unit_amount
        self.price_factor = price_factor        
        self.history = None

    def sellprice(self):
        price = self.price_per_liter * self.price_factor * self.amount/1000
        return price

    def __eq__(self, other):
        return (other != None and self.id == other.id and self.name == other.name
            and self.alc_perc == other.alc_perc and self.color == other.color
            and self.price_per_liter == other.price_per_liter and self.price_factor == other.price_factor
            and self.history == other.history)

    def __ne__(self, other):
        return (other == None or self.id != other.id or self.name != other.name
            or self.alc_perc != other.alc_perc or self.color != other.color
            or self.price_per_liter != other.price_per_liter or self.price_factor != other.price_factor
            or self.history != other.history)

class Mix(Drink):
    """
    Mix class
    """
    def __init__(self,name,drinks = []):
        Drink.__init__(self,name)
        self.drinks = drinks
        self.update_properties()

    def insert_drink(self,drink):
        """Add a drink to the mix"""
        self.drinks.append(drink)
        update_properties()

    def remove_drink(self):
        """Remove a drink from the mix"""
        update_properties()

    def update_properties(self):
        """Recalculate mix properties"""
        parts = len(self.drinks)
        if parts > 0:
            self.price_per_liter = 0
            self.alc_perc = 0
            color = array([0,0,0])
            for d in self.drinks:
                pass
                self.alc_perc = self.alc_perc + d.alc_perc / parts
                color += array(d.color)/parts
                self.price_per_liter = self.price_per_liter + d.price_per_liter/parts
            self.color = tuple(color)

if __name__ == "__main__":
    d1 = Drink('cola',color = (0,0,0),alc_perc = 0,price_per_liter = 3.50)
    d2 = Drink('bacardi',color = (255,255,255),alc_perc = 40,price_per_liter = 50)
    print d1
    print d2

    # example mix, 3 parts cola 1 part bacardi
    m = Mix(name = 'baco',drinks = [d1,d1,d1,d2])
    print m
    print "Selling price = " + str(m.sellprice()) + " euro"
