"""
The 'database' used by the Quartjesavond server. 
Just a simple memory store of drinks that uses shelve to constantly write
a copy to disk.
"""
import os
import shelve
import time
import threading

from quartjes.models.drink import Drink, Mix, __version__
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

        self._monitor = Database._DatabaseMonitor(self)
        
        self._load_database()

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
        
        Please note that this method does not update the 
        :attr:`quartjes.models.drink.Drink.price_factor` and
        :attr:`quartjes.models.drink.Drink.history` of the drink. These attributes
        are protected by the server. You can however clear those using
        :meth:`clear_history` or :meth:`clear_price_factor`.
        
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
    def clear_history(self, drink):
        """
        Remove all history from the drink.
        
        Parameters
        ----------
        drink : :class:`quartjes.models.drink.Drink`
            The drink clear history for. Can be a copy.
        
        Raises
        ------
        KeyError
            The drink does not exist in the database.
        """
        local_drink = self.get(drink.id)
        if not local_drink:
            raise KeyError
        
        local_drink.clear_price_history()
        self._drink_dirty = True

    @remote_method
    def clear_price_factor(self, drink):
        """
        Reset the price factor of the drink.
        
        Parameters
        ----------
        drink : :class:`quartjes.models.drink.Drink`
            The drink to reset. Can be a copy.
        
        Raises
        ------
        KeyError
            The drink does not exist in the database.
        """
        local_drink = self.get(drink.id)
        if not local_drink:
            raise KeyError
        
        local_drink.price_factor = 1.0
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
    def get(self, id_):
        """
        Get a drink from the database by id.
        
        Parameters
        ----------
        id_ : UUID
            Id of the drink to get.
            
        Returns
        -------
        drink : :class:`quartjes.models.drink.Drink`
            The drink with the given id. None if it does not exist.
        """
        return self._drink_index.get(id_)

    @remote_method
    def get_drinks(self):
        """
        Get all drinks in the database.
        
        Returns
        -------
        drinks : list of :class:`quartjes.models.drink.Drink`
            All drinks in the database.
        """
        return self._drinks[:]

    @remote_method
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
                if debug_mode:
                    print "Drink not local"
                self.add(remote_drink)
                local_drinks.append(remote_drink)
            else:
                if debug_mode:
                    print "Drink local"
                local_drinks.append(local_drink)
        
        mix.drinks = local_drinks

    def _dump_drinks(self):
        """
        Debug method to dump the contents to the console.
        """
        for drink in self._drinks:
            print(drink)
    
    def _load_database(self):
        """
        Load the current database from disk.
        If no database exists on disk, create a new one.
        """
        if not os.path.exists(self._db_file):
            print("No database available yet, creating one")
            db_valid = False
        else:
            db_valid = True
            
        db = shelve.open(self._db_file)
        
        if db_valid:
            if not db.has_key('version'):
                print("Invalid database, creating new")
                db_valid = False
            elif db['version'] != __version__:
                print("Database version mismatch, creating new")
                db_valid = False
            elif not db.has_key('drinks'):
                db_valid = False
                print("Invalid database, creating new")

        if db_valid:
            self._internal_replace_drinks(db['drinks'])
        else:
            self.reset()
        db.close()

        self._monitor.start()

    def _internal_replace_drinks(self, drinks):
        """
        Replace all drinks in the database.
        Internal use only. Does not trigger any updates or saves.
        """
        index = {}
        for dr in drinks:
            index[dr.id] = dr
        self._drinks, self._drink_index = drinks, index

    def _store(self):
        """
        Save the database to disk.
        """
        if debug_mode:
            print("Storing db")
        db = shelve.open(self._db_file)
        db['version'] = __version__
        db['drinks'] = self._drinks
        db.close()

        if self._drink_dirty:
            self._notify_drinks_updated()

        self._drink_dirty = False

    def force_save(self):
        """
        Force the database to be saved the next time the monitor checks.
        Will also trigger an update message to listeners.
        """
        self._drink_dirty = True

    def reset(self):
        """
        Reset the database to a predefined default database.
        """
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

        self._store()
    
    def clear(self):
        """
        Remove all contents from the database.
        """
        self._drinks = []
        self._drink_index = {}
        self._drink_dirty = True
        
        self._store()

        

    on_drinks_updated = remote_event()
    """
    Event triggered when the contents of the database has changed.
    
    Attributes
    ----------
    drinks : iterable of :class:`quartjes.models.drink.Drink`
        The latest contents of the database.
    """

    def _notify_drinks_updated(self):
        """
        Notify event listeners that the list of drinks has been updated.
        """
        self.on_drinks_updated(self._drinks)

    @remote_method
    def count(self):
        """
        Get the number of drinks in the database.
        """
        return len(self._drinks)

    __contains__ = contains
    __getitem__ = get
    __len__ = count


    class _DatabaseMonitor(threading.Thread):
        """
        Internal monitoring thread to ensure the database is saved to disk
        on a regular base. This will also cause event listeners to be
        notified.
        
        Attributes
        ----------
        db : Database
            The database to monitor.
        """
        def __init__(self, db):
            super(Database._DatabaseMonitor, self).__init__()
            self.daemon = True
            self.db = db
            
        def run(self):
            """
            This is where the magic happens.
            """
            while True:
                time.sleep(1)
                if self.db._drink_dirty:
                    self.db._store()

_database = Database()
'''
Singleton reference to the database.
'''

def default_database():
    """
    Get a reference to the active database.
    """
    global _database
    if _database is None:
        _database = Database()
    return _database

if __name__ == "__main__":
    print "Running self test"
     
    
    for drink in default_database().get_drinks():
        print drink

    print "Selling price = " + str(drink.sellprice()) + " euro"

