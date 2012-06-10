'''
Unit tests for the database module.
Contains tests running directly on the database component without connector
features active.
'''
import unittest
from quartjes.controllers.database import Database
from quartjes.models.drink import Drink, Mix
import random

class TestDatabase(unittest.TestCase):


    def setUp(self):
        self.db = Database()
        self.db.clear()
        self.random = random.Random()


    def tearDown(self):
        self.db.reset()


    def test_add_drink(self):
        """
        Test adding a new drink.
        """
        drink = self._create_random_drink()
        self.assertNotIn(drink, self.db, "New drink should be unique")
        
        count_before = len(self.db)
        
        self.db.add(drink)
        self.assertIn(drink, self.db, "New drink should be added")
        
        get = self.db.get(drink.id)
        self.assertIs(get, drink, "Should be able to get drink by id")
        
        self.assertTrue(self.db.contains(drink), "Database should contain new drink")
        self.assertEqual(len(self.db), count_before + 1, "Database should contain exactly one item more")
        
    def test_add_mix(self):
        """
        Test adding a new mix.
        """
        mix = self._create_random_mix()
        self.assertNotIn(mix, self.db, "New mix should be unique")
        
        count_before = len(self.db)
        
        self.db.add(mix)
        self.assertIn(mix, self.db, "New mix should be added")
        
        for drink in mix.drinks:
            self.assertIn(drink, self.db, "Components from the mix should be added")
        
        get = self.db.get(mix.id)
        self.assertIs(get, mix, "Should be able to get mix by id")
        
        self.assertTrue(self.db.contains(mix), "Database should contain new mix")
        self.assertEqual(len(self.db), count_before + 1 + len(mix.drinks), 
                         "Database should contain mix plus contents now")
    
    def test_add_existing_drink(self):
        """
        Test adding a drink that already exists.
        """
        drink = self._create_random_drink()
        self.assertNotIn(drink, self.db, "New drink should be unique")
        
        self.db.add(drink)
        self.assertIn(drink, self.db, "New drink should be added")

        with self.assertRaises(ValueError, "Adding the drink twice should raise a ValueError."):
            self.db.add(drink)
            
    
    def test_remove_drink(self):
        """
        Test removing a drink from the database.
        """
        drink = self._create_random_drink()
        self.assertNotIn(drink, self.db, "New drink should be unique")
        self.db.add(drink)
        self.assertIn(drink, self.db, "New drink should be added")

        self.db.remove(drink)
        self.assertNotIn(drink, self.db, "Drink should no longer be present")
        
    def test_remove_drink_using_copy(self):
        """
        Test removing a drink from the database using a copy of the drink.
        """
        drink = self._create_random_drink()
        self.assertNotIn(drink, self.db, "New drink should be unique")
        self.db.add(drink)
        self.assertIn(drink, self.db, "New drink should be added")
        
        copy = Drink()
        copy.id = drink.id
        
        self.db.remove(copy)
        self.assertNotIn(drink, self.db, "Drink should no longer be present")
    
    def test_remove_nonexisting_drink(self):
        """
        Test removing a drink from the database that does not exist.
        """
        drink = self._create_random_drink()
        self.assertNotIn(drink, self.db, "New drink should be unique")
        self.db.add(drink)
        self.assertIn(drink, self.db, "New drink should be added")

        other = self._create_random_drink()
        self.assertNotIn(other, self.db, "Other drink should not exist yet")
        
        with self.assertRaises(KeyError, "Adding the drink twice should raise a KeyError."):
            self.db.remove(other)
    
    def _create_random_drink(self):
        drink = Drink()
        drink.name = [chr(self.random.randint(ord('a'), ord('z'))) for _ in range(0, self.random.randint(8, 30))]
        drink.alc_perc = self.random.random()
        drink.color = (self.random.randint(0, 255), self.random.randint(0, 255), self.random.randint(0, 255))
        drink.price_factor = self.random.random() * 2
        drink.unit_amount = self.random.randint(100, 1000)
        drink.unit_price = self.random.random() * 4
        
        return drink
    
    def _create_random_mix(self):
        mix = Mix()
        mix.name = [chr(self.random.randint(ord('a'), ord('z'))) for _ in range(0, self.random.randint(8, 30))]
        mix.unit_amount = self.random.randint(100, 1000)
        
        for drink in (self._create_random_drink() for _ in range(1, self.random.randint(2, 10))):
            mix.insert_drink(drink)
        
        return mix

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()