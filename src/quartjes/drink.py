# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$5-jun-2011 12:34:35$"

import uuid
from quartjes.util.classtools import AttrDisplay

class Drink(AttrDisplay):
    """
    Drink class
    """

    __serialize__ = ["name", "alc_perc", "color", "realprice", "price_factor"]
    
    def __init__(self, name="Unnamed"):
        self.id = uuid.uuid4()
        self.name = name
        self.alc_perc = 0
        self.color = [0,0,0,0]
        self.realprice = 0
        self.price_factor = 1

    def sellprice(self):
        price = self.realprice * self.price_factor
        return price

if __name__ == "__main__":
    print "Hello World"
