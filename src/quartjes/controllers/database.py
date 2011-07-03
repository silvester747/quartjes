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
        self._drinks = None
        self._drink_index = {}
        self._mixes = None
        self._mix_index = {}

        self.mix_dirty = False
        self.drink_dirty = False
        self.service = None

        self.db_file = "database"

        self.monitor = DatabaseMonitor(self)


    def replace_drinks(self, drinks):
        index = {}
        for dr in drinks:
            index[dr.id] = dr
        self._drinks, self._drink_index = drinks, index
        self.drink_dirty = True

    def replace_mixes(self, mixes):
        index = {}
        for mix in mixes:
            index[mix.id] = mix
        self._mixes, self._mix_index = mixes, index
        self.mix_dirty = True

    def update(self, obj):
        if isinstance(obj, Mix):
            self.update_mix(obj)
        else:
            self.update_drink(obj)

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

            self.drink_dirty = True

    def update_mix(self, mix):
        local_mix = self.get_mix(mix.id)

        if not local_mix:
            self.add_mix(mix)
        else:
            local_mix.name = mix.name
            #TODO
            self.mix_dirty = True

    def add(self, obj):
        if isinstance(obj, Mix):
            self.add_mix(obj)
        else:
            self.add_drink(obj)

    def add_drink(self, drink):
        self._drink_index[drink.id] = drink
        self._drinks.append(drink)
        self.drink_dirty = True

    def add_mix(self, mix):
        self._mix_index[mix.id] = mix
        self._mixes.append(mix)
        self.mix_dirty = True

    def remove(self, obj):
        if isinstance(obj, Mix):
            self.remove_mix(obj)
        else:
            self.remove_drink(obj)

    def remove_drink(self, drink):
        del self._drink_index[drink.id]
        self._drinks.remove(drink)
        self.drink_dirty = True

    def remove_mix(self, mix):
        del self._mix_index[mix.id]
        self._mixes.remove(mix)
        self.mix_dirty = True

    def get(self, id):
        val = self.get_drink(id)
        if not val:
            return self.get_mix(id)
        else:
            return val

    def get_drink(self, id):
        return self._drink_index.get(id)

    def get_mix(self, id):
        return self._mix_index.get(id)

    def get_drinks(self):
        if not self._drinks:
            self._load_drinks()
        return self._drinks

    def get_mixes(self):
        if not self._mixes:
            self._load_drinks()
        return self._mixes

    def _load_drinks(self):
        db = shelve.open(self.db_file)
        if not db.has_key('drinks'):
            db.close()
            self.db_reset()

        else:
            self.replace_drinks(db['drinks'])
            self.replace_mixes(db['mixes'])
            db.close()

        self.monitor.start()


    def store(self):
        print("Storing db")
        db = shelve.open(self.db_file)
        db['drinks'] = self._drinks
        db['mixes'] =self._mixes
        db.close()

        if self.drink_dirty:
            self._drinks_updated()
        if self.mix_dirty:
            self._mixes_updated()

        self.drink_dirty = False
        self.mix_dirty = False

    def set_dirty(self):
        self.drink_dirty = True
        self.mix_dirty = True

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

    def _mixes_updated(self):
        if self.service:
            self.service.notify_mixes_updated(self._mixes)


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

    get_mixes()
    update_mix(mix)
    add_mix(mix)
    remove_mix(mix)

    add(obj)
    remove(obj)
    update(obj)

    Supported topics
    ================

    drinks_updated(drinks)
    mixes_update(mixes)

    """

    def __init__(self, db=None):
        super(DatabaseService, self).__init__(name="database")
        self.db = db

    def notify_drinks_updated(self, drinks):
        self.send_topic_update("drinks_updated", drinks=drinks)

    def notify_drinks_updated(self, mixes):
        self.send_topic_update("mixes_updated", mixes=mixes)

    def action_get_drinks(self):
        return self.db.get_drinks()

    def action_update_drink(self, drink):
        return self.db.update_drink(drink)

    def action_add_drink(self, drink):
        return self.db.add_drink(drink)

    def action_remove_drink(self, drink):
        return self.db.remove_drink(drink)

    def action_get_mixes(self):
        return self.db.get_mixes()

    def action_update_mix(self, mix):
        return self.db.update_mix(mix)

    def action_add_mix(self, mix):
        return self.db.add_drink(drink)

    def action_remove_mix(self, mix):
        return self.db.remove_mix(mix)

    def action_update(self, obj):
        return self.db.update(obj)

    def action_add(self, obj):
        return self.db.add(obj)

    def action_remove(self, obj):
        return self.db.remove(obj)

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

