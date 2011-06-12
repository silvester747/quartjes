"""
Definition of messages used to communicate between the Quartjes server and its
clients.
"""

__author__="Rob van der Most"
__date__ ="$Jun 3, 2011 8:52:26 PM$"

import uuid
from quartjes.util.classtools import AttrDisplay
import quartjes.connector.serializer as serializer
import xml.etree.ElementTree as et

class Message(AttrDisplay):
    """
    Base class all messages are derived from.
    """

    def __init__(self, id=None):
        if id == None:
            self.id = uuid.uuid4()
        else:
            self.id = id

class ServerRequestMessage(Message):
    """
    Message type used to send requests from clients to the server.
    """

    __serialize__ = ["serviceName", "action", "params"]

    def __init__(self, id=None, serviceName=None, action=None, params=None):
        Message.__init__(self, id)
        
        self.serviceName = serviceName
        self.action = action
        self.params = params

    def __eq__(self, other):
        return other != None and self.id == other.id and self.serviceName == other.serviceName and self.action == other.action and self.params == other.params

    def __ne__(self, other):
        return other == None or self.id != other.id or self.serviceName != other.serviceName or self.action != other.action or self.params != other.params


def parseMessageString(string):
    """
    Parse a string for an xml message an return an instance of the contained
    message type.
    """

    node = et.fromstring(string)
    return serializer.deserialize(node)


def createMessageString(msg):
    root = msg.createXml()
    return et.tostring(root)



class MessageHandleError(Exception):

    RESULT_OK = 0
    RESULT_XML_PARSE_FAILED = 1
    RESULT_XML_INVALID = 2
    RESULT_UNKNOWN_MESSAGE = 3
    RESULT_UNEXPECTED_MESSAGE = 4
    RESULT_UNKNOWN_SERVICE = 5
    RESULT_UNKNOWN_ERROR = 99

    def __init__(self, errorCode=RESULT_UNKNOWN_ERROR):
        self.errorCode = errorCode

def selfTest():

    from quartjes.drink import Drink

    params = {"what":"that", "howmany":3, "price":2.10, "drink":Drink("Cola")}

    msg = ServerRequestMessage(uuid.uuid4(), "myservice", "myaction", params)
    assert msg == msg
    assert not msg != msg
    print(msg)

    string = createMessageString(msg)
    print(string)

    msg2 = parseMessageString(string)
    print(msg2)
    assert msg == msg2

if __name__ == "__main__":
    selfTest()
