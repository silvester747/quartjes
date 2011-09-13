"""
Test cases for the quartjes.connector.serializer module.

This file ends with tests instead of test to make sure NetBeans does not use its built in
test runner which does not support the new load_tests protocol.
"""

import unittest
import quartjes.connector.serializer as serializer
from quartjes.connector.serializer import *
import uuid
from quartjes.util.classtools import QuartjesBaseClass

class ValueSerializerTestCase(unittest.TestCase):
    """
    Test the value serializer system part of the serializer.
    """

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
        self.assertEqual(type, None)

    def test_unknown(self):

        class Unknown:
            pass

        u = Unknown()

        (value, type) = get_serialized_value(u)
        self.assertEqual(value, None)
        self.assertEqual(type, None)

class SerializerTestCase(unittest.TestCase):

    def __init__(self, name, input, output,):
        super(SerializerTestCase, self).__init__(methodName="run_test")
        self.input = input
        self.output = output
        self.name = name

    def run_test(self):
        node = serialize(self.input, tag_name="test")
        self.assertIsNotNone(node, "Output should contain an object")

        string = serializer.et.tostring(node)
        self.assertRegexpMatches(string, self.output, "Incorrect output\nExpected:\n%s\nGot:\n%s\n" % (self.output, string))

        node = serializer.et.fromstring(string)
        val = deserialize(node)
        self.assertEquals(val, self.input, "Deserialized value should equal original object.")

    def shortDescription(self):
        return self.name

class TestKlassOld():
    def __init__(self):
        self.i = 43432
        self.f = 454343.1233
        self.s = "teststring"
        self.l = [23, 543, "sds"]
        self.t = (23, 543, "sds")

    def __eq__(self, other):
        return (self.i == other.i and self.f == other.f and self.s == other.s
                and self.l == other.l and self.t == other.t)

class TestKlassNew(object):
    def __init__(self):
        self.i = 43432
        self.f = 454343.1233
        self.s = "teststring"
        self.l = [23, 543, "sds"]
        self.t = (23, 543, "sds")

    def __eq__(self, other):
        return (self.i == other.i and self.f == other.f and self.s == other.s
                and self.l == other.l and self.t == other.t)

class TestQuartjesKlass(QuartjesBaseClass):
    def __init__(self):
        super(TestQuartjesKlass, self).__init__()
        self.i = 43432
        self.f = 454343.1233
        self.s = "teststring"
        self.l = [23, 543, "sds"]
        self.t = (23, 543, "sds")

class TestKlassOverride(object):

    __serialize__ = ["i", "l"]
    
    def __init__(self):
        self.i = 43432
        self.f = 454343.1233
        self.s = "teststring"
        self.l = [23, 543, "sds"]
        self.t = (23, 543, "sds")

    def __eq__(self, other):
        return (self.i == other.i and self.l == other.l)

serializer_test_cases = [SerializerTestCase(
                             name="int",
                             input=12,
                             output="<test type=\"int\">12</test>"
                             ),
                         SerializerTestCase(
                             name="float",
                             input=1234.23,
                             output="<test type=\"float\">1234.23</test>"
                             ),
                         SerializerTestCase(
                             name="string",
                             input="testsdfda@#nfasnalsk32",
                             output="<test type=\"str\">testsdfda@#nfasnalsk32</test>"
                             ),
                         SerializerTestCase(
                             name="uuid",
                             input=uuid.UUID('urn:uuid:3f22b1ff-424d-468c-aa47-b399a6fd1795'),
                             output="<test type=\"uuid\">urn:uuid:3f22b1ff-424d-468c-aa47-b399a6fd1795</test>"
                             ),
                         SerializerTestCase(
                             name="list",
                             input=[12, 1234.23, "bladfsd"],
                             output="<test type=\"list\"><value type=\"int\">12</value><value type=\"float\">1234.23</value><value type=\"str\">bladfsd</value></test>"
                             ),
                         SerializerTestCase(
                             name="tuple",
                             input=(12, 1234.23, "bladfsd"),
                             output="<test type=\"tuple\"><value type=\"int\">12</value><value type=\"float\">1234.23</value><value type=\"str\">bladfsd</value></test>"
                             ),
                         SerializerTestCase(
                             name="old style class",
                             input=TestKlassOld(),
                             output="<test class=\"__main__.TestKlassOld\" id=\"urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\" type=\"instance\"><f type=\"float\">454343.1233</f><i type=\"int\">43432</i><l type=\"list\"><value type=\"int\">23</value><value type=\"int\">543</value><value type=\"str\">sds</value></l><s type=\"str\">teststring</s><t type=\"tuple\"><value type=\"int\">23</value><value type=\"int\">543</value><value type=\"str\">sds</value></t></test>"
                             ),
                         SerializerTestCase(
                             name="new style class",
                             input=TestKlassNew(),
                             output="<test class=\"__main__.TestKlassNew\" id=\"urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\" type=\"instance\"><f type=\"float\">454343.1233</f><i type=\"int\">43432</i><l type=\"list\"><value type=\"int\">23</value><value type=\"int\">543</value><value type=\"str\">sds</value></l><s type=\"str\">teststring</s><t type=\"tuple\"><value type=\"int\">23</value><value type=\"int\">543</value><value type=\"str\">sds</value></t></test>"
                             ),
                         SerializerTestCase(
                             name="quartjes class",
                             input=TestQuartjesKlass(),
                             output="<test class=\"__main__.TestQuartjesKlass\" id=\"urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\" type=\"instance\"><f type=\"float\">454343.1233</f><i type=\"int\">43432</i><l type=\"list\"><value type=\"int\">23</value><value type=\"int\">543</value><value type=\"str\">sds</value></l><s type=\"str\">teststring</s><t type=\"tuple\"><value type=\"int\">23</value><value type=\"int\">543</value><value type=\"str\">sds</value></t></test>"
                             ),
                         SerializerTestCase(
                             name="class with override",
                             input=TestKlassOverride(),
                             output="<test class=\"__main__.TestKlassOverride\" id=\"urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\" type=\"instance\"><i type=\"int\">43432</i><l type=\"list\"><value type=\"int\">23</value><value type=\"int\">543</value><value type=\"str\">sds</value></l></test>"
                             ),
                         SerializerTestCase(
                             name="None",
                             input=None,
                             output="<test />"
                             )
                        ]


def load_tests(loader, tests, pattern):
    """
    Load the test cases in this module.
    Some test cases are added a little different than usual.
    """
    
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(ValueSerializerTestCase))
    suite.addTests(serializer_test_cases)
    return suite

if __name__ == '__main__':
    unittest.main(verbosity=2)

