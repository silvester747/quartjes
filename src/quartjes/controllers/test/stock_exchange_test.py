'''
Created on Jul 7, 2012

@author: rob
'''
import unittest
import quartjes
from quartjes.controllers.stock_exchange import StockExchange
from quartjes.models.drink import Drink, Mix
import random

class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        quartjes.controllers.stock_exchange.debug_mode=True
        cls.exchange = StockExchange(start_thread=False)
        cls.exchange._db.reset()
        cls.random = random.Random()

    @classmethod
    def tearDownClass(cls):
        pass


    def test_no_sales(self):
        """
        Test prices remain the same if there are no sales.
        """
        prices_before = self._get_drink_prices()
        self.exchange._recalculate_factors()
        prices_after = self._get_drink_prices()
        
        for id in prices_before:
            self.assertAlmostEqual(prices_before[id], prices_after[id], delta=0.01)

    def test_single_sale(self):
        """
        Test that for a single sale, only that drink increases in price and
        the rest decreases.
        """
        drinks = self.exchange._db.get_drinks()
        drink = self.random.choice(drinks)
        while isinstance(drink, Mix):
            drink = self.random.choice(drinks)

        amount = 1
        price = self.exchange.sell(drink, amount)
        self.assertEqual(price, drink.sellprice_quartjes() * amount, "Resulting price does not match.")
        
        prices_before = self._get_drink_prices()
        self.exchange._recalculate_factors()
        prices_after = self._get_drink_prices()
        
        self.exchange._db._dump_drinks()
        
        for id in prices_before:
            if id == drink.id:
                self.assertGreaterEqual(prices_after[id], prices_before[id], "Expected sold drink price to rise.")
            else:
                self.assertLessEqual(prices_after[id], prices_before[id], "Expected other drink prices to fall")
    
    def test_different_amount_sales(self):
        """
        Test that if two sales of different sizes are submitted, both will increase in price
        but the larger sale increases more.
        """    
        drinks = self.exchange._db.get_drinks()
        drink1 = self.random.choice(drinks)
        while isinstance(drink1, Mix):
            drink1 = self.random.choice(drinks)
        drink2 = self.random.choice(drinks)
        while isinstance(drink2, Mix):
            drink2 = self.random.choice(drinks)

        amount1 = 1
        price = self.exchange.sell(drink1, amount1)
        self.assertEqual(price, drink1.sellprice_quartjes() * amount1, "Resulting price does not match.")
        
        amount2 = 10
        price = self.exchange.sell(drink2, amount2)
        self.assertEqual(price, drink2.sellprice_quartjes() * amount2, "Resulting price does not match.")
        
        prices_before = self._get_drink_prices()
        self.exchange._recalculate_factors()
        prices_after = self._get_drink_prices()
        
        self.exchange._db._dump_drinks()
        
        for id in prices_before:
            if id == drink1.id or id == drink2.id:
                self.assertGreaterEqual(prices_after[id], prices_before[id], "Expected sold drink price to rise.")
            else:
                self.assertLessEqual(prices_after[id], prices_before[id], "Expected other drink prices to fall")
        
        diff1 = prices_after[drink1.id] - prices_before[drink1.id]
        diff2 = prices_after[drink2.id] - prices_before[drink2.id]
        self.assertGreater(diff2, diff1, "Expected large sale to have larger difference.")

    def _get_drink_prices(self):
        
        prices = {}
        drinks = self.exchange._db.get_drinks()
        for drink in drinks:
            if not isinstance(drink, Mix):
                prices[drink.id] = drink.sellprice()
        return prices

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()