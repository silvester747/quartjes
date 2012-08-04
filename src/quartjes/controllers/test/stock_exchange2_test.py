'''
Created on Aug 3, 2012

@author: rob
'''
import unittest
import random
import time

import quartjes
from quartjes.controllers.stock_exchange2 import StockExchange2, linear_demand_time_correction
from quartjes.models.drink import Mix

class StockExchange2Test(unittest.TestCase):
    """
    Test all functionality of the Stock Exchange version 2.
    Local version.
    """

    @classmethod
    def setUpClass(cls):
        quartjes.controllers.stock_exchange2.debug_mode=True
        cls.exchange = StockExchange2()
        cls.random = random.Random()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.exchange._db.reset()
        pass


    def tearDown(self):
        pass


    def test_01_sales_history(self):
        """
        Test that selling a drink results in sales history for that drink being updated.
        """
        drink = self.get_random_drink()
        self.assertEqual(len(drink.sales_history), 0, "Expecting no sales history yet")
        
        amount = self.random.randint(1, 10)
        price = drink.current_price
        current_time = time.time()
        
        self.exchange.sell(drink, amount)
        
        self.assertEqual(len(drink.sales_history), 1, "Expecting one entry in sales history")
        history_item = drink.sales_history[0]
        self.assertAlmostEqual(history_item[0], current_time, msg="Expecting correct time to be stored", delta=1000)
        self.assertEqual(history_item[1], amount, "Correct amount should be stored")
        self.assertEqual(history_item[2], price, "Expecting correcty price to be stored")
    
    def test_02a_demand_calculation_linear(self):
        """
        Test the demand calculation function.
        """
        drink = self.get_random_drink()
        self.assertEqual(len(drink.sales_history), 0, "Expecting no sales history yet")

        self.exchange._demand_time_correction = linear_demand_time_correction
        
        

    def get_random_drink(self):
        drinks = self.exchange._db.get_drinks()
        drink = self.random.choice(drinks)
        while isinstance(drink, Mix):
            drink = self.random.choice(drinks)
        
        return drink
        
    def get_random_mix(self):
        drinks = self.exchange._db.get_drinks()
        mix = self.random.choice(drinks)
        while not isinstance(mix, Mix):
            mix = self.random.choice(drinks)
        
        return mix
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()