"""
Definition of messages used to communicate between the Quartjes server and its
clients.
"""

__author__= " Rob van der Most"

from quartjes.util.classtools import QuartjesBaseClass
import quartjes.connector.serializer as serializer
from quartjes.connector.serializer import et

class Message(QuartjesBaseClass):
    """
    Base class all messages are derived from.
    """

    def __init__(self, id=None):
        super(Message, self).__init__(id)


class MethodCallMessage(Message):
    """
    Message type used to call methods on the server.
    """

    def __init__(self, service_name=None, method_name=None, pargs=None, kwargs=None):
        super(MethodCallMessage, self).__init__()
        
        self.service_name = service_name
        self.method_name = method_name
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
    Message used to subscribe to events
    """

    def __init__(self, service_name=None, event_name=None):
        super(SubscribeMessage, self).__init__()

        self.service_name = service_name
        self.event_name = event_name

class EventMessage(Message):
    """
    Message used to send updates on topics
    """

    def __init__(self, service_name=None, event_name=None, pargs=None, kwargs=None):
        super(EventMessage, self).__init__()

        self.service_name = service_name
        self.event_name = event_name
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
    """
    Create an xml string to represent the given message.
    """
    root = serializer.serialize(msg, parent=None, tag_name="message")
    return et.tostring(root)

