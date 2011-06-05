# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$5-jun-2011 12:34:42$"
from drink import Drink

class Mix(Drink):
    """
    Mix class
    """

    def __init__(self,mixname):
        self.__init__(mixname)
        self.drinks = []

    def insert_drank(self,drink):
        self.drinks.append(drink)
        update_properties()
    def remove_drank(self):
        update_properties()
    def update_properties(self):
        parts = len(self.drinks)
        if parts > 0:
            for d in self.drinks:
                self.alc_perc.add(d.alc_perc / parts)
                #self.color
                self.realprice.add = (d.realprice / parts)
    

if __name__ == "__main__":
    print "Hello World"
