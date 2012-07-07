'''
Created on Jul 7, 2012

@author: rob
'''
import unittest
from quartjes.connector.client import ClientConnector
from quartjes.connector.exceptions import TimeoutError

test_port = 3421

class ClientServerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare a server
        """
        start_test_server()

    def testClientServer(self):
        """
        Do some client server tests.
        """
        import time
    
        def callback(text):
            callback.count += 1
            callback.last_result = text
        
        def testfunc():
            pass
    
        callback.count = 0
    
        cl = ClientConnector("localhost", test_port)
        cl.start()
        self.assertTrue(cl.is_connected(), "Connection failed.")
    
        testService = cl.get_service_interface("test")
    
        result = testService.test(text="Spam")
        self.assertEqual(result, "Spam", "Expecting same message back.")
        result = testService.test("Spam")
        self.assertEqual(result, "Spam", "Expecting same message back.")
        
        with self.assertRaises(TypeError):
            result = testService.test(testfunc)
    
    
        testService.on_trigger += callback
    
        testService.trigger(text="Eggs")
        self.assertEqual(callback.count, 1, "No callback received")
        self.assertEqual(callback.last_result, "Callback: Eggs", "Received incorrect result text.")
        
        testService.trigger2("Ham")
        self.assertEqual(callback.count, 2, "No callback received")
        self.assertEqual(callback.last_result, "Callback2: Ham", "Received incorrect result text.")
        
        from quartjes.connector.protocol import default_timeout
        with self.assertRaises(TimeoutError):
            testService.test_timeout(default_timeout + 10)
            
    
        time.sleep(10)
        cl.stop()
        time.sleep(10)
        cl.start()
    
        result = testService.test(text="Spam")
        self.assertEqual(result, "Spam", "Expecting same message back.")
    
        cl.stop()
    
    @classmethod
    def tearDownClass(cls):
        """
        Clean up the server
        """
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
    from quartjes.connector.services import TestRemoteService
    
    server = ServerConnector(test_port)
    server.register_service(TestRemoteService(), "test")
    server.start()
    
    import time
    while True:
        time.sleep(100)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()