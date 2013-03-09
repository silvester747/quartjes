'''
Created on Aug 3, 2012

@author: rob
'''
import unittest
import random
import time

import quartjes
from quartjes.controllers.stock_exchange2 import StockExchange2, linear_demand_time_correction, max_sales_age, sqrt_demand_time_correction
from quartjes.controllers.stock_exchange2 import square_demand_time_correction
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
        self.assertAlmostEqual(history_item.timestamp, current_time, msg="Expecting correct time to be stored", delta=1000)
        self.assertEqual(history_item.amount, amount, "Correct amount should be stored")
        self.assertEqual(history_item.price, price, "Expecting correct price to be stored")
    
    def test_02_demand_calculation_comparison(self):
        """
        Test the demand calculation function.
        """
        drink = self.get_random_drink()
        self.assertEqual(len(drink.sales_history), 0, "Expecting no sales history yet")

        recent = time.time() - 0.1 * max_sales_age
        old = time.time() - 0.5 * max_sales_age
        very_old = time.time() - 0.9 * max_sales_age
        amount = 10
        
        functions = (square_demand_time_correction, linear_demand_time_correction, sqrt_demand_time_correction)
        recent_demand = []
        old_demand = []
        very_old_demand = []
        
        # For each function test that the older the sale, the less the demand
        for correction_function in functions:
            
            self.exchange._demand_time_correction = correction_function
    
            drink.add_sales_history(amount, recent)
            recent_demand.append(self.exchange._calculate_demand(drink))
            
            drink.clear_sales_history()
            drink.add_sales_history(amount, old)
            old_demand.append(self.exchange._calculate_demand(drink))
            
            drink.clear_sales_history()
            drink.add_sales_history(amount, very_old)
            very_old_demand.append(self.exchange._calculate_demand(drink))
            
            self.assertGreater(recent_demand[-1], old_demand[-1], "The older the sale, the less the demand number")
            self.assertGreater(old_demand[-1], very_old_demand[-1], "The older the sale, the less the demand number")
        
        # Functions are sorted by expected output. The first function should result in the lowest values
        for i in range(len(functions) - 1):
            self.assertGreater(recent_demand[i + 1], recent_demand[i])
            self.assertGreater(old_demand[i + 1], old_demand[i])
            self.assertGreater(very_old_demand[i + 1], very_old_demand[i])
        
        # Output results for logging
        # Please note that these values still require normalization before being usable for calculations
        print("Recent_demand : %r" % recent_demand)
        print("Old_demand : %r" % old_demand)
        print("Very_old_demand : %r" % very_old_demand)

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