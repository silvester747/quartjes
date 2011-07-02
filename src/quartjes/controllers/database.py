# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$16-jun-2011 20:35:14$"
import shelve
import quartjes.connector.services
from quartjes.models.drink import Drink,Mix

class Database:
    def __init__(self):        
        self.drinks = []
        self.drink_index = {}
        self.mixes = []

        self.dirty = False
        self.service = None

        self.db = shelve.open('database')
        if 'drinks' not in self.db.keys():
            self.db_reset()
        else:
            self.replace_drinks(self.db_read('drinks'))
            self.mixes = self.db_read('mixes')



    def replace_drinks(self, drinks):
        index = {}
        for dr in drinks:
            index[dr.id] = dr
        self.drinks, self.drink_index = drinks, index
        self.dirty = True

    def update_drink(self, drink):
        local_drink = self.db.get_drink(drink.id)

        if not local_drink:
            self.db.add_drink(drink)
        else:
            local_drink.name = drink.name
            local_drink.alc_perc = drink.alc_perc
            local_drink.color = drink.color
            local_drink.price_per_liter = drink.price_per_liter
            local_drink.amount = drink.amount

            self.set_dirty()

    def add_drink(self, drink):
        self.drink_index[drink.id] = drink
        self.drinks.append(drink)
        self.dirty = True

    def remove_drink(self, drink):
        del self.drink_index[drink.id]
        self.drinks.remove(drink)
        self.dirty = True

    def get_drink(self, id):
        return self.drink_index.get(id)

    def store(self):
        self.db_write('drinks',self.drinks)
        self.db_write('mixes',self.mixes)

        self._drinks_updated()

        self.dirty = False

    def set_dirty(self):
        self.dirty = True

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

        drinks = []
        for i in range(len(names)):
            drinks.append(Drink(name = names[i], alc_perc = alc_perc[i],unit_price = price_per_liter[i],color=color[i],unit_amount=amount[i]))
        self.replace_drinks(drinks)

        d1 = self.drinks[0]
        d2 = self.drinks[6]
        self.mixes.append(Mix('Baco',[d1,d1,d1,d2]))

        self.store()

    def get_service(self):
        if not self.service:
            self.service = DatabaseService(self)
        return self.service

    def _drinks_updated(self):
        if self.service:
            self.service.notify_drinks_updated(self.db.get_drinks())


class DatabaseService(quartjes.connector.services.Service):
    """
    Service to access the database.

    Service name: database

    Supported methods
    =================

    get_drinks()
    update_drink(drink)


    Supported topics
    ================

    drinks_updated(drinks)

    """

    def __init__(self, db=None):
        super(DatabaseService, self).__init__(name="database")
        self.db = db

    def notify_drinks_updated(self, drinks):
        self.send_topic_update("drinks_updated", drinks=drinks)

    def action_get_drinks(self):
        return self.db.drinks

    def action_update_drink(self, drink):
        return self.db.update_drink(drink)


database = Database()

if __name__ == "__main__":
    print "Running self test"
    d = Database()    
    
    for drink in d.drinks:
        print drink

    for mix in d.mixes:
        print mix

    print "Selling price = " + str(mix.sellprice()) + " euro"

