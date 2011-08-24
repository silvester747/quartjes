# To change this template, choose Tools | Templates
# and open the template in the editor.

import unittest

class ServicesTestCase(unittest.TestCase):
    def setUp(self):
        from quartjes.connector.services import TestService
        self.ts = TestService()

    def tearDown(self):
        self.ts = None

    def test_correct_service_call(self):
        input = "this is input"
        output = self.ts.call("test", text=input)
        self.assertEqual(input, output)

    def test_incorrect_action(self):
        from quartjes.connector.protocol import MessageHandleError

        with self.assertRaises(MessageHandleError):
            self.ts.call("bla", {})

    def test_incorrect_params(self):
        from quartjes.connector.protocol import MessageHandleError

        with self.assertRaises(MessageHandleError):
            self.ts.call("test", bla=12)


if __name__ == '__main__':
    unittest.main(verbosity=2)

