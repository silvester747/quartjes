"""
Definition of messages used to communicate between the Quartjes server and its
clients.
"""

__author__ = "Rob van der Most"
__docformat__ = "restructuredtext en"

from quartjes.util.classtools import QuartjesBaseClass
import quartjes.connector.serializer as serializer
from quartjes.connector.serializer import et

class Message(QuartjesBaseClass):
    """
    Base class all messages are derived from.
    
    Parameters
    ----------
    id : UUID
        Optional unique identifier for the message.
    """

    def __init__(self, id=None):
        super(Message, self).__init__(id)


class MethodCallMessage(Message):
    """
    Message type used to call methods on the server.
    
    Parameters
    ----------
    service_name : string
        Name of the service to call a method on.
    method_name : string
        Name of the method to call.
    pargs : iterable
        Positional arguments to use in the method call.
    kwargs : iterable
        Keyword argumetns to use in the method call.
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
    
    Parameters
    ----------
    result_code : int
        Code determining the outcome of the request. 
        See :class:`quartjes.connector.exceptions.MessageHandleError`.
    result
        Result of the request. Can be a return value or None.
    response_to : UUID
        Unique ID of the message this is a response to.
    """

    def __init__(self, result_code = 0, result=None, response_to=None):
        super(ResponseMessage, self).__init__()

        self.result_code = result_code
        self.result = result
        self.response_to = response_to

class SubscribeMessage(Message):
    """
    Message used to subscribe to events.
    
    Parameters
    ----------
    service_name : string
        Name of the service containing the event.
    event_name : string
        Name of the event to subscribe to.
    """

    def __init__(self, service_name=None, event_name=None):
        super(SubscribeMessage, self).__init__()

        self.service_name = service_name
        self.event_name = event_name

class EventMessage(Message):
    """
    Message used to send updates on events. Triggers a callback on the clientside.
    
    Parameters
    ----------
    service_name : string
        Name of the service containing the event.
    event_name : string
        Name of the event that was triggered.
    pargs : iterable
        Positional arguments passed to the event.
    kwargs : dict
        Keyword arguments passed to the event.
    """

    def __init__(self, service_name=None, event_name=None, pargs=None, kwargs=None):
        super(EventMessage, self).__init__()

        self.service_name = service_name
        self.event_name = event_name
        self.pargs = pargs
        self.kwargs = kwargs

class ServerMotdMessage(Message):
    """
    MOTD message received from the server upon connection. Part of the initial handshake.
    
    Parameters
    ----------
    motd : string
        Message of the day. Short message from the server for new clients.
    client_id : UUID
        Unique identifier of the client at the server side.
    """

    def __init__(self, motd="Hello there!", client_id=None):
        super(ServerMotdMessage, self).__init__()

        self.motd = motd
        self.client_id = client_id
        

def parse_message_string(string):
    """
    Parse a string for an XML message an return an instance of the contained
    message type.
    
    Parameters
    ----------
    string : string
        A string containing an XML message to be parsed.
        
    Returns
    -------
    node
        An XML node containing the XML from the input string.
    """

    node = et.fromstring(string)
    return serializer.deserialize(node)


def create_message_string(msg):
    """
    Create an xml string to represent the given message.
    
    Parameters
    ----------
    msg : :class:`quartjes.connector.messages.Message`
        Message object to create XML for.
        
    Returns
    -------
    xml : string
        The XML for the input object.
        
    """
    root = serializer.serialize(msg, parent=None, tag_name="message")
    return et.tostring(root)

