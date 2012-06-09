'''
Unit tests for the database module.
Contains tests running directly on the database component without connector
features active.
'''
import unittest
from quartjes.controllers.database import Database

class TestDatabase(unittest.TestCase):


    def setUp(self):
        self.db = Database()
        self.db.db_reset()


    def tearDown(self):
        pass


    def testName(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()