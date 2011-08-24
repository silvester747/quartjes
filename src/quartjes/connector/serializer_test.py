"""
Test cases for the quartjes.connector.serializer module.
"""

from quartjes.connector.serializer import get_serialized_value
import unittest
import quartjes.connector.serializer as serializer
from quartjes.connector.serializer import *
import uuid

class ValueSerializerTestCase(unittest.TestCase):

    def setUp(self):

        u = uuid.uuid4()

        self.test_cases = [("int", 12, "12"),
                           ("str", "abcdefg234%$#$%sdfsadsa\n", "abcdefg234%$#$%sdfsadsa\n"),
                           ("float", -12312.3424, "-12312.3424"),
                           ("uuid", u, u.urn)]

    def test_serializing(self):
        for (type, input, output) in self.test_cases:
            result = get_serialized_value(input)
            self.assertEqual(result, (output, type), "Type %s failed serializing." % type)

    def test_deserializing(self):
        for (type, input, output) in self.test_cases:
            (string, t) = get_serialized_value(input)
            ser = serializer.value_serializers_by_klass_name[type]
            result = ser.deserialize(string)
            self.assertEqual(input, result, "Type %s failed deserializing." % type)

    def test_none(self):
        (value, type) = get_serialized_value(None)
        self.assertEqual(value, None)
        self.assertEqual(type, "NoneType")

    def test_unknown(self):

        class Unknown:
            pass

        u = Unknown()

        (value, type) = get_serialized_value(u)
        self.assertEqual(value, None)
        self.assertEqual(type, "NoneType")

class SerializerTestCase(unittest.TestCase):

    def setUp(self):
        self.simple_test_cases = [(12, "<test type=\"int\">12</test>"),
                                  (1234.23, "<test type=\"float\">1234.23</test>"),
                                  ("testsdfda@#$nfasnalsk32", "<test type=\"str\">testsdfda@#$nfasnalsk32</test>")]

    def test_simple(self):

        for (input, output) in self.simple_test_cases:
            node = serialize(input, tag_name="test")
            self.assertIsNotNone(node, "Output should contain an object")

            string = serializer.et.tostring(node)
            self.assertEquals(string, output, "Incorrect output\nExpected:\n%s\nGot:\n%s\n" % (output, string))

            node = serializer.et.fromstring(string)
            val = deserialize(node)
            self.assertEquals(val, input)

if __name__ == '__main__':
    unittest.main()

