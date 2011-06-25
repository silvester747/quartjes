# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$16-jun-2011 20:35:14$"
import shelve
from quartjes.models import drink,mix

class Database:
    def __init__(self):        
        self.drinks = []
        self.mix = mix.Mix
        self.db = shelve.open('database')
        if 'drinks' not in self.db.keys():
            self.db_reset()

    def db_write(self,tag,values):
        self.db[tag] = values

    def db_read(self,tag):
        values = self.db[tag]
        return values

    def db_reset(self):
        names = ['Cola','Sinas','Cassis','7up','Safari','Bacardi lemon','Bacardi','Whiskey','Jenever','Oude Jenever']
        for name in names:
            self.drinks.append(drink.Drink(name))
        self.db_write('drinks',self.drinks)

if __name__ == "__main__":
    print "Running self test"
    d = Database()
    drinks = d.db['drinks']
    
    for drink in drinks:        
        print drink

