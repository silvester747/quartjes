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
        output = self.ts.call("test", {"text":input})
        self.assertEqual(input, output)

    def test_incorrect_action(self):
        from quartjes.connector.protocol import MessageHandleError

        with self.assertRaises(MessageHandleError):
            self.ts.call("bla", {})

    def test_incorrect_params(self):
        from quartjes.connector.protocol import MessageHandleError

        with self.assertRaises(MessageHandleError):
            self.ts.call("test", {})

class SerializerTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_serialize_int(self):
        self.base_serialize_test(12)

    def test_serialize_float(self):
        self.base_serialize_test(12.654)

    def test_serialize_str(self):
        self.base_serialize_test("nicetest")

    def test_serialize_uuid(self):
        import uuid
        self.base_serialize_test(uuid.uuid4())

    def test_serialize_list(self):
        import uuid
        self.base_serialize_test(["test", 12, 13.543, uuid.uuid4()])

    def test_serialize_dict(self):
        import uuid
        self.base_serialize_test({"a":"test", "b":12, "c":13.543, "d":uuid.uuid4()})

    def test_serialize_instance(self):
        from quartjes.drink import Drink
        d = Drink("Cola")
        d.alc_perc = 12.0
        d.color = [255,255,0,0]
        d.price_factor = 0.234
        d.realprice = 12.1
        self.base_serialize_test(d)

    def test_serialize_same_instances(self):
        from quartjes.drink import Drink
        d = Drink("Cola")
        d.alc_perc = 12.0
        d.color = [255,255,0,0]
        d.price_factor = 0.234
        d.realprice = 12.1
        self.base_serialize_test([d, d])

    def base_serialize_test(self, value):
        import quartjes.connector.serializer as serializer
        import xml.etree.ElementTree as et

        input = value
        xml = serializer.serialize(input)
        output = serializer.deserialize(xml)
        self.assertEqual(input, output)

        xml = serializer.serialize(input)
        string = et.tostring(xml)
        xml = et.fromstring(string)
        output = serializer.deserialize(xml)
        self.assertEqual(input, output)


if __name__ == '__main__':
    unittest.main(verbosity=2)

