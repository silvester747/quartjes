import time
import threading
# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$16-jun-2011 20:35:14$"
import shelve
from quartjes.models.drink import Drink,Mix
from quartjes.connector.services import remote_event, remote_method, remote_service

@remote_service
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

    @remote_method
    def replace_drinks(self, drinks):
        index = {}
        for dr in drinks:
            index[dr.id] = dr
        self._drinks, self._drink_index = drinks, index
        self.drink_dirty = True

    @remote_method
    def replace_mixes(self, mixes):
        index = {}
        for mix in mixes:
            index[mix.id] = mix
        self._mixes, self._mix_index = mixes, index
        self.mix_dirty = True

    @remote_method
    def update(self, obj):
        if isinstance(obj, Mix):
            self.update_mix(obj)
        else:
            self.update_drink(obj)

    @remote_method
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

    @remote_method
    def update_mix(self, mix):
        local_mix = self.get_mix(mix.id)

        if not local_mix:
            self.add_mix(mix)
        else:
            local_mix.name = mix.name
            #TODO
            self.mix_dirty = True

    @remote_method
    def add(self, obj):
        if isinstance(obj, Mix):
            self.add_mix(obj)
        else:
            self.add_drink(obj)

    @remote_method
    def add_drink(self, drink):
        self._drink_index[drink.id] = drink
        self._drinks.append(drink)
        self.drink_dirty = True

    @remote_method
    def add_mix(self, mix):
        self._mix_index[mix.id] = mix
        self._mixes.append(mix)
        self.mix_dirty = True

    @remote_method
    def remove(self, obj):
        if isinstance(obj, Mix):
            self.remove_mix(obj)
        else:
            self.remove_drink(obj)

    @remote_method
    def remove_drink(self, drink):
        del self._drink_index[drink.id]
        self._drinks.remove(drink)
        self.drink_dirty = True

    @remote_method
    def remove_mix(self, mix):
        del self._mix_index[mix.id]
        self._mixes.remove(mix)
        self.mix_dirty = True

    @remote_method
    def get(self, id):
        val = self.get_drink(id)
        if not val:
            return self.get_mix(id)
        else:
            return val

    @remote_method
    def get_drink(self, id):
        return self._drink_index.get(id)

    @remote_method
    def get_mix(self, id):
        return self._mix_index.get(id)

    @remote_method
    def get_drinks(self):
        if not self._drinks:
            self._load_drinks()
        return self._drinks

    @remote_method
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
        unit_price = [0.75 ,0.75, 0.75, 0.75, 3.00, 3.00 , 3.00, 4.0,2.5,3.5]
        color = [(0,0,0),(255,128,0),(128,0,128),(255,255,255),(255,200,0),(255,255,255),(255,255,255),(255,128,0),(255,255,255),(255,255,255)]
        amount = [200,200,200,200,100,40,40,40,40,40]

        drinks = []
        for i in range(len(names)):
            drinks.append(Drink(name = names[i], alc_perc = alc_perc[i],unit_price = unit_price[i],color=color[i],unit_amount=amount[i]))
        self.replace_drinks(drinks)

        mixes = []
        d1 = self._drinks[0]
        d2 = self._drinks[6]
        mixes.append(Mix('Baco',[d1,d1,d1,d2]))
        d1 = self._drinks[2]
        d2 = self._drinks[4]
        mixes.append(Mix('Safari Cassis',[d1,d1,d1,d2]))
        self.replace_mixes(mixes)

        self.store()

    on_drinks_updated = remote_event()
    on_mixes_updated = remote_event()

    def _drinks_updated(self):
        self.on_drinks_updated(self._drinks)

    def _mixes_updated(self):
        self.on_mixes_updated(self._mixes)


class DatabaseMonitor(threading.Thread):
    def __init__(self, db):
        super(DatabaseMonitor, self).__init__()
        self.daemon = True
        self.db = db
        
    def run(self):
        while True:
            time.sleep(1)
            if self.db.drink_dirty or self.db.mix_dirty:
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

