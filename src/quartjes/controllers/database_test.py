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


    @classmethod
    def setUpClass(cls):
        print("Running offline")
        cls.db = Database()
        cls.db.clear()
        cls.random = random.Random()


    @classmethod
    def tearDownClass(cls):
        cls.db.reset()

    def test_add_drink(self):
        """
        Test adding a new drink.
        """
        drink = self._create_random_drink()
        self.assertFalse(self.db.contains(drink), "New drink should be unique")
        
        count_before = self.db.count()
        
        self.db.add(drink)
        self.assertTrue(self.db.contains(drink), "New drink should be added")
        
        get = self.db.get(drink.id)
        self.assertEquals(get, drink, "Should be able to get drink by id")
        
        self.assertTrue(self.db.contains(drink), "Database should contain new drink")
        self.assertEqual(self.db.count(), count_before + 1, "Database should contain exactly one item more")
        
    def test_add_mix_with_new_drinks(self):
        """
        Test adding a new mix where the components are not in the database yet.
        """
        mix = self._create_random_mix()
        self.assertFalse(self.db.contains(mix), "New mix should be unique")
        for drink in mix.drinks:
            self.assertNotIn(drink, self.db, "Components from the mix should be unique")
        
        count_before = self.db.count()
        
        self.db.add(mix)
        self.assertIn(mix, self.db, "New mix should be added")
        
        for drink in mix.drinks:
            self.assertIn(drink, self.db, "Components from the mix should be added")
        
        get = self.db.get(mix.id)
        self.assertEquals(get.id, mix.id, "Should be able to get mix by id") # TODO better checking
        
        self.assertTrue(self.db.contains(mix), "Database should contain new mix")
        self.assertEqual(self.db.count(), count_before + 1 + len(mix.drinks), 
                         "Database should contain mix plus contents now")
    
    def test_add_mix_with_existing_drinks(self):
        """
        Test adding a new mix where the components are already in the database.
        """
        mix = self._create_random_mix()
        self.assertNotIn(mix, self.db, "New mix should be unique")
        
        for drink in mix.drinks:
            self.db.add(drink)
        
        count_before = self.db.count()
        
        self.db.add(mix)
        self.assertIn(mix, self.db, "New mix should be added")
        
        self.assertEqual(self.db.count(), count_before + 1, "Only the mix should be added")
    
    def test_add_mix_with_some_new_drinks(self):
        """
        Test adding a new mix where the components are already in the database.
        """
        mix = self._create_random_mix()
        self.assertNotIn(mix, self.db, "New mix should be unique")
        
        drinks_added_before = len(mix.drinks)/2
        for drink in mix.drinks[0:drinks_added_before]:
            self.db.add(drink)
        
        count_before = self.db.count()
        
        self.db.add(mix)
        self.assertIn(mix, self.db, "New mix should be added")
        
        expected_drinks_added = len(mix.drinks) - drinks_added_before
        self.assertEqual(self.db.count(), count_before + 1 + expected_drinks_added, 
                         "Only the mix should be added")
    
    def test_add_existing_drink(self):
        """
        Test adding a drink that already exists.
        """
        drink = self._create_random_drink()
        self.assertNotIn(drink, self.db, "New drink should be unique")
        
        self.db.add(drink)
        self.assertIn(drink, self.db, "New drink should be added")

        with self.assertRaises(ValueError):
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
        
        with self.assertRaises(KeyError):
            self.db.remove(other)
    
    def test_update_drink(self):
        """
        Test updating a drink in the database
        """
        drink = self._create_random_drink()
        self.assertNotIn(drink, self.db, "New drink should be unique")
        self.db.add(drink)
        self.assertIn(drink, self.db, "New drink should be added")

        other = self._create_random_drink()
        other.id = drink.id
        self.assertNotEqual(drink, other, "Other drink object should differ from first drink")
        
        count = self.db.count()
        self.db.update(other)
        drink = self.db[other.id]
        
        self.assertEqual(drink.name, other.name, 
                         "Original drink object should be updated to match other drink object")
        self.assertEqual(drink.alc_perc, other.alc_perc, 
                         "Original drink object should be updated to match other drink object")
        self.assertEqual(drink.color, other.color, 
                         "Original drink object should be updated to match other drink object")
        self.assertEqual(drink.unit_amount, other.unit_amount, 
                         "Original drink object should be updated to match other drink object")
        self.assertEqual(drink.unit_price, other.unit_price, 
                         "Original drink object should be updated to match other drink object")
        self.assertEqual(count, self.db.count(), "No new drinks should be added.")
        
        drink = self.db.get(other.id)
        self.assertEqual(drink.name, other.name, 
                         "Drink in database should be updated to match other drink object")
        self.assertEqual(drink.alc_perc, other.alc_perc, 
                         "Drink in database should be updated to match other drink object")
        self.assertEqual(drink.color, other.color, 
                         "Drink in database should be updated to match other drink object")
        self.assertEqual(drink.unit_amount, other.unit_amount, 
                         "Drink in database should be updated to match other drink object")
        self.assertEqual(drink.unit_price, other.unit_price, 
                         "Drink in database should be updated to match other drink object")
    
    def test_update_nonexisting_drink(self):
        """
        Test that when a non existing drink is updated, it is added to the database.
        """
        drink = self._create_random_drink()
        self.assertNotIn(drink, self.db, "New drink should be unique")
        count = self.db.count()
        
        self.db.update(drink)
        self.assertIn(drink, self.db, "New drink should be added")
        self.assertEqual(self.db.count(), count + 1, "A drink should be added.")

    
    def _create_random_drink(self):
        drink = Drink()
        drink.name = "".join([chr(self.random.randint(ord('a'), ord('z'))) for _ in range(0, self.random.randint(8, 30))])
        drink.alc_perc = self.random.random()
        drink.color = (self.random.randint(0, 255), self.random.randint(0, 255), self.random.randint(0, 255))
        drink.price_factor = self.random.random() * 2
        drink.unit_amount = self.random.randint(100, 1000)
        drink.unit_price = self.random.random() * 4
        
        return drink
    
    def _create_random_mix(self):
        mix = Mix()
        mix.name = "".join([chr(self.random.randint(ord('a'), ord('z'))) for _ in range(0, self.random.randint(8, 30))])
        mix.unit_amount = self.random.randint(100, 1000)
        
        for drink in (self._create_random_drink() for _ in range(1, self.random.randint(2, 10))):
            mix.insert_drink(drink)
        
        return mix

if __name__ == "__main__":
    unittest.main()
    