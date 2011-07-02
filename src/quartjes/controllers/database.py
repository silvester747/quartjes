# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$16-jun-2011 20:35:14$"
import shelve
from quartjes.models.drink import Drink,Mix

class Database:
    def __init__(self):        
        self.drinks = []
        self.mixes = []
        self.db = shelve.open('database')
        if 'drinks' not in self.db.keys():
            self.db_reset()
        else:
            self.drinks = self.db_read('drinks')
            self.mixes = self.db_read('mixes')

    def db_write(self,tag,values):
        self.db[tag] = values

    def db_read(self,tag):
        values = self.db[tag]
        return values

    def db_reset(self):
        names = ['Cola','Sinas','Cassis','7up','Safari','Bacardi lemon','Bacardi','Whiskey','Jenever','Oude Jenever']
        alc_perc = [0,0,0,0,14,20,40,40,40,40]
        price_per_liter = [3.50,3.50,3.50,3.50,20,25,40,50,35,45]
        color = [(0,0,0),(255,128,0),(128,0,128),(255,255,255),(255,200,0),(255,255,255),(255,255,255),(255,128,0),(255,255,255),(255,255,255)]
        amount = [200,200,200,200,100,40,40,40,40,40]

        for i in range(len(names)):
            self.drinks.append(Drink(name = names[i], alc_perc = alc_perc[i],price_per_liter = price_per_liter[i],color=color[i],amount=amount[i]))

        self.db_write('drinks',self.drinks)        
        d1 = self.drinks[0]
        d2 = self.drinks[6]
        self.mixes.append(Mix('Baco',[d1,d1,d1,d2]))
        self.db_write('mixes',self.mixes)

if __name__ == "__main__":
    print "Running self test"
    d = Database()    
    
    for drink in d.drinks:
        print drink

    for mix in d.mixes:
        print mix

    print "Selling price = " + str(mix.sellprice()) + " euro"

