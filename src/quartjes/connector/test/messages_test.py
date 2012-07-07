"""
Set of test cases for quartjes.connector.messages
"""

__author__ = "Rob van der Most"
__docformat__ = "restructuredtext en"

import unittest

from quartjes.connector.messages import MethodCallMessage, create_message_string, parse_message_string
from quartjes.models.drink import Drink

class TestMessages(unittest.TestCase):
    """
    Test basic functionality for message objects.
    
    Methods
    -------
    setUp
    test_equality
    test_create_and_parse
    """

    def setUp(self):
        """
        Prepare some objects to perform the test on.
        """
        self.drink = Drink("Cola")
        self.pargs = [3, 2.10, "bla", self.drink]
        self.kwargs = {"what":"that", "howmany":3, "price":2.10, "drink":self.drink}
        self.message = MethodCallMessage("myservice", "myaction", self.pargs, self.kwargs)
        self.message2 = MethodCallMessage("myservice", "myaction", self.pargs, self.kwargs)
        self.message2.id = self.message.id

    def test_equality(self):
        """
        Test whether the equality operators work as expected.
        """
        self.assertTrue(self.message == self.message2)
        self.assertFalse(self.message != self.message2)

    def test_create_and_parse(self):
        """
        Test whether a message can be correctly serialised and deserialised again.
        """
        string = create_message_string(self.message)
        self.assertIsNotNone(string)
        self.assertGreater(len(string), 0)

        result = parse_message_string(string)
        self.assertEqual(self.message, result)

if __name__ == "__main__":
    unittest.main()
