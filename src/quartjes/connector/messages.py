"""
Definition of messages used to communicate between the Quartjes server and its
clients.
"""

__author__="Rob van der Most"
__date__ ="$Jun 3, 2011 8:52:26 PM$"

from quartjes.util.classtools import QuartjesBaseClass
import quartjes.connector.serializer as serializer
from quartjes.connector.serializer import et

class Message(QuartjesBaseClass):
    """
    Base class all messages are derived from.
    """

    def __init__(self, id=None):
        super(Message, self).__init__(id)


class ActionRequestMessage(Message):
    """
    Message type used to send requests from clients to the server.
    """

    def __init__(self, service_name=None, action=None, pargs=None, kwargs=None):
        super(ActionRequestMessage, self).__init__()
        
        self.service_name = service_name
        self.action = action
        self.pargs = pargs
        self.kwargs = kwargs

class ResponseMessage(Message):
    """
    Message used to respond to server request messages.
    """

    def __init__(self, result_code = 0, result=None, response_to=None):
        super(ResponseMessage, self).__init__()

        self.result_code = result_code
        self.result = result
        self.response_to = response_to

class SubscribeMessage(Message):
    """
    Message used to subscribe to update feeds
    """

    def __init__(self, service_name=None, topic=None):
        super(SubscribeMessage, self).__init__()

        self.service_name = service_name
        self.topic = topic

class TopicUpdateMessage(Message):
    """
    Message used to send updates on topics
    """

    def __init__(self, service_name=None, topic=None, pargs=None, kwargs=None):
        super(TopicUpdateMessage, self).__init__()

        self.service_name = service_name
        self.topic = topic
        self.pargs = pargs
        self.kwargs = kwargs

class ServerMotdMessage(Message):
    """
    MOTD message received from the server upon connection.
    """

    def __init__(self, motd="Hello there!", client_id=None):
        super(ServerMotdMessage, self).__init__()

        self.motd = motd
        self.client_id = client_id
        

def parse_message_string(string):
    """
    Parse a string for an xml message an return an instance of the contained
    message type.
    """

    node = et.fromstring(string)
    return serializer.deserialize(node)


def create_message_string(msg):
    root = serializer.serialize(msg, parent=None, tag_name="message")
    return et.tostring(root)



def self_test():

    from quartjes.drink import Drink

    params = {"what":"that", "howmany":3, "price":2.10, "drink":Drink("Cola")}

    msg = ActionRequestMessage("myservice", "myaction", params)
    assert msg == msg
    assert not msg != msg
    print(msg)

    string = create_message_string(msg)
    print(string)

    msg2 = parse_message_string(string)
    print(msg2)
    assert msg == msg2

if __name__ == "__main__":
    self_test()
