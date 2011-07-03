import time
import threading
# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$16-jun-2011 20:35:14$"
import shelve
import quartjes.connector.services
from quartjes.models.drink import Drink,Mix

class Database:
    def __init__(self):        
        self._drinks = []
        self._drink_index = {}
        self._mixes = []

        self.dirty = False
        self.service = None

        self.db_file = "database"

        self.monitor = DatabaseMonitor(self)


    def replace_drinks(self, drinks):
        index = {}
        for dr in drinks:
            index[dr.id] = dr
        self._drinks, self._drink_index = drinks, index
        self.dirty = True

    def update_drink(self, drink):
        local_drink = self.get_drink(drink.id)

        if not local_drink:
            self.add_drink(drink)
        else:
            local_drink.name = drink.name
            local_drink.alc_perc = drink.alc_perc
            local_drink.color = drink.color
            local_drink.price_per_liter = drink.price_per_liter
            local_drink.amount = drink.amount

            self.set_dirty()

    def add_drink(self, drink):
        self._drink_index[drink.id] = drink
        self._drinks.append(drink)
        self.dirty = True

    def remove_drink(self, drink):
        del self._drink_index[drink.id]
        self._drinks.remove(drink)
        self.dirty = True

    def get_drink(self, id):
        return self._drink_index.get(id)

    def get_drinks(self):
        if not self._drinks:
            self._load_drinks()
        return self._drinks

    def _load_drinks(self):
        db = shelve.open(self.db_file)
        if not db.has_key('drinks'):
            db.close()
            self.db_reset()

        else:
            self.replace_drinks(db['drinks'])
            self._mixes = db['mixes']
            db.close()

        self.monitor.start()


    def store(self):
        print("Storing db")
        db = shelve.open(self.db_file)
        db['drinks'] = self._drinks
        db['mixes'] =self._mixes
        db.close()

        self._drinks_updated()

        self.dirty = False

    def set_dirty(self):
        self.dirty = True

    def db_reset(self):
        #assert False
        print("Resetting database")
        names = ['Cola','Sinas','Cassis','7up','Safari','Bacardi lemon','Bacardi','Whiskey','Jenever','Oude Jenever']
        alc_perc = [0,0,0,0,14,20,40,40,40,40]
        price_per_liter = [3.50,3.50,3.50,3.50,20,25,40,50,35,45]
        color = [(0,0,0),(255,128,0),(128,0,128),(255,255,255),(255,200,0),(255,255,255),(255,255,255),(255,128,0),(255,255,255),(255,255,255)]
        amount = [200,200,200,200,100,40,40,40,40,40]

        drinks = []
        for i in range(len(names)):
            drinks.append(Drink(name = names[i], alc_perc = alc_perc[i],unit_price = price_per_liter[i],color=color[i],unit_amount=amount[i]))
        self.replace_drinks(drinks)

        d1 = self._drinks[0]
        d2 = self._drinks[6]
        self._mixes.append(Mix('Baco',[d1,d1,d1,d2]))

        self.store()

    def get_service(self):
        if not self.service:
            self.service = DatabaseService(self)
        return self.service

    def _drinks_updated(self):
        if self.service:
            self.service.notify_drinks_updated(self._drinks)


class DatabaseService(quartjes.connector.services.Service):
    """
    Service to access the database.

    Service name: database

    Supported methods
    =================

    get_drinks()
    update_drink(drink)
    add_drink(drink)
    remove_drink(drink)


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
        return self.db.get_drinks()

    def action_update_drink(self, drink):
        return self.db.update_drink(drink)

    def action_add_drink(self, drink):
        return self.db.add_drink(drink)

    def action_remove_drink(self, drink):
        return self.db.remove_drink(drink)

class DatabaseMonitor(threading.Thread):
    def __init__(self, db):
        super(DatabaseMonitor, self).__init__()
        self.daemon = True
        self.db = db
        
    def run(self):
        while True:
            time.sleep(1)
            if self.db.dirty:
                self.db.store()

'''
Singleton reference to the database.
'''
database = Database()

if __name__ == "__main__":
    print "Running self test"
     
    
    for drink in database.get_drinks():
        print drink

    for mix in database._mixes:
        print mix

    print "Selling price = " + str(mix.sellprice()) + " euro"

