'''
Created on Jul 7, 2012

@author: rob
'''
import unittest
import quartjes.controllers.database_test
from quartjes.connector.client import ClientConnector
import random

test_port = 7451 # special port number for testing only

class TestDatabaseOnline(quartjes.controllers.database_test.TestDatabase):
    """
    Test cases for the the database, but now using a connector
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Prepare a database connection
        """
        start_test_server()
        
        cls.connector = ClientConnector("localhost", test_port)
        cls.connector.start()
        cls.db = cls.connector.database
        cls.random = random.Random()

    
    @classmethod
    def tearDownClass(cls):
        """
        Clean up the database connection
        """
        cls.connector.stop()
        
        stop_test_server()
    
_test_server_process =  None

def start_test_server():
    from multiprocessing import Process
    global _test_server_process
    _test_server_process = Process(target=_run_test_server)
    _test_server_process.start()

def stop_test_server():
    global _test_server_process
    if _test_server_process:
        _test_server_process.terminate()
        _test_server_process = None

def _run_test_server():
    from quartjes.connector.server import ServerConnector
    from quartjes.controllers.database import database
    
    server = ServerConnector(test_port)
    server.register_service(database, "database")
    server.start()
    
    import time
    while True:
        time.sleep(100)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()