"""
The 'database' used by the Quartjesavond server. 
Just a simple memory store of drinks that uses shelve to constantly write
a copy to disk.
"""

import time
import threading
import shelve
from quartjes.models.drink import Drink,Mix
from quartjes.connector.services import remote_event, remote_method, remote_service

debug_mode = False

@remote_service
class Database:
    """
    Very basic database containing all drinks for Quartjesavond.
    
    When constructed, it will try to load the file 'database' from the current
    working directory. If the file does not exist, a new default database
    containing default drinks is created.
    
    A monitor thread is started to keep track of changes. As soon as changes
    are detected they will be saved to disk. This will only happen once per
    second for performance reasons.
    """
    
    def __init__(self):        
        self._drinks = None
        self._drink_index = {}
        self._drink_dirty = False
        self._service = None
        self._db_file = "database"

        self._monitor = DatabaseMonitor(self)
        
        self._load_drinks()

    @remote_method
    def replace_drinks(self, drinks):
        """
        Replace all drinks in the database.
        
        Parameters
        ----------
        drinks : iterable of :class:`quartjes.models.drink.Drink`
            A new list of drinks to replace the current in the database.
        """
        index = {}
        for dr in drinks:
            if isinstance(dr, Mix):
                self._localize_mix(dr)
            index[dr.id] = dr
        self._drinks, self._drink_index = drinks, index
        self._drink_dirty = True

    @remote_method
    def update(self, drink):
        """
        Update an existing drink in the database. Uses the internal id of the
        drink to find the object to update. If the id is unknown, the drink
        will be added as a new drink.
        
        Parameters
        ----------
        drink : :class:`quartjes.models.drink.Drink`
            The drink to update. Can be a copy.
        """
        local_drink = self.get(drink.id)

        if not local_drink:
            self.add(drink)
        else:
            if isinstance(drink, Mix):
                self._localize_mix(drink)
                local_drink.name = drink.name
                local_drink.drinks = drink.drinks
                local_drink.update_properties()
                
            else:
                local_drink.name = drink.name
                local_drink.alc_perc = drink.alc_perc
                local_drink.color = drink.color
                local_drink.unit_amount = drink.unit_amount
                local_drink.unit_price = drink.unit_price

            self._drink_dirty = True

    @remote_method
    def add(self, drink):
        """
        Add a new drink to the database.
        
        Parameters
        ----------
        drink : :class:`quartjes.models.drink.Drink`
            The drink to add. Must not exist in the database yet.
        
        Raises
        ------
        ValueError
            A drink with the same id already exists in the database.
        """
        if self.contains(drink):
            raise ValueError
        
        if isinstance(drink, Mix):
            self._localize_mix(drink)
        
        self._drink_index[drink.id] = drink
        self._drinks.append(drink)
        self._drink_dirty = True
        if debug_mode:
            self._dump_drinks()
        
    @remote_method
    def remove(self, drink):
        """
        Remove a drink from the database.
        
        Parameters
        ----------
        drink : :class:`quartjes.models.drink.Drink`
            The drink to remove. Can be a copy.
        
        Raises
        ------
        KeyError
            The drink does not exist in the database.
        """
        local_drink = self._drink_index.get(drink.id, None)
        if local_drink:
            if debug_mode:
                print("Removing drink %s" % local_drink.name)
            del self._drink_index[local_drink.id]
            self._drinks.remove(local_drink)
            self._drink_dirty = True
            if debug_mode:
                self._dump_drinks()
        else:
            raise KeyError

    @remote_method
    def get(self, id):
        """
        
        """
        return self._drink_index.get(id)

    @remote_method
    def get_drinks(self):
        return self._drinks[:]

    def contains(self, drink):
        """
        Does the database already contain (a copy of) the given drink?
        
        Parameters
        ----------
        drink : :class:`quartjes.models.drink.Drink`
            The drink to find.
        
        Returns
        -------
        contains : boolean
            True if (a copy of) the drink is already present.
        """
        return drink.id in self._drink_index

    def _localize_mix(self, mix):
        """
        Make sure all components of a mix exist locally.
        """
        local_drinks = []
        for remote_drink in mix.drinks:
            local_drink = self.get(remote_drink.id)
            if not local_drink:
                self.add(remote_drink)
                local_drinks.append(remote_drink)
            else:
                local_drinks.append(local_drink)
        
        mix.drinks = local_drinks

    def _dump_drinks(self):
        for drink in self._drinks:
            print(drink)
    
    def _load_drinks(self):
        db = shelve.open(self._db_file)
        if not db.has_key('drinks'):
            db.close()
            self.db_reset()

        else:
            self._internal_replace_drinks(db['drinks'])
            db.close()

        self._monitor.start()

    def _internal_replace_drinks(self, drinks):
        index = {}
        for dr in drinks:
            index[dr.id] = dr
        self._drinks, self._drink_index = drinks, index

    def store(self):
        if debug_mode:
            print("Storing db")
        db = shelve.open(self._db_file)
        db['drinks'] = self._drinks
        db.close()

        if self._drink_dirty:
            self._drinks_updated()

        self._drink_dirty = False

    def set_dirty(self):
        self._drink_dirty = True

    def db_reset(self):
        if debug_mode:
            print("Resetting database")
        names = ['Cola','Sinas','Cassis','7up','Safari','Bacardi lemon','Bacardi','Whiskey','Jenever','Oude Jenever']
        alc_perc = [0,0,0,0,14,20,40,40,40,40]
        unit_price = [0.75 ,0.75, 0.75, 0.75, 3.00, 3.00 , 3.00, 4.0,2.5,3.5]
        color = [(0,0,0),(255,128,0),(128,0,128),(255,255,255),(255,200,0),(255,255,255),(255,255,255),(255,128,0),(255,255,255),(255,255,255)]
        amount = [200,200,200,200,100,40,40,40,40,40]

        drinks = []
        for i in range(len(names)):
            drinks.append(Drink(name = names[i], alc_perc = alc_perc[i],unit_price = unit_price[i],color=color[i],unit_amount=amount[i]))
        d1 = drinks[0]
        d2 = drinks[6]
        drinks.append(Mix('Baco',[d1,d1,d1,d2]))
        d1 = drinks[2]
        d2 = drinks[4]
        drinks.append(Mix('Safari Cassis',[d1,d1,d1,d2]))
        self._internal_replace_drinks(drinks)

        self.store()

    on_drinks_updated = remote_event()

    def _drinks_updated(self):
        self.on_drinks_updated(self._drinks)


class DatabaseMonitor(threading.Thread):
    def __init__(self, db):
        super(DatabaseMonitor, self).__init__()
        self.daemon = True
        self.db = db
        
    def run(self):
        while True:
            time.sleep(1)
            if self.db._drink_dirty:
                self.db.store()

'''
Singleton reference to the database.
'''
database = Database()

if __name__ == "__main__":
    print "Running self test"
     
    
    for drink in database.get_drinks():
        print drink

    print "Selling price = " + str(drink.sellprice()) + " euro"

