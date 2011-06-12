"""
Definition of messages used to communicate between the Quartjes server and its
clients.
"""

__author__="Rob van der Most"
__date__ ="$Jun 3, 2011 8:52:26 PM$"

import uuid
from quartjes.util.classtools import QuartjesBaseClass
import quartjes.connector.serializer as serializer
import xml.etree.ElementTree as et

class Message(QuartjesBaseClass):
    """
    Base class all messages are derived from.
    """

    def __init__(self, id=None):
        QuartjesBaseClass.__init__(self, id)


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

class ServerResponseMessage(Message):
    """
    Message used to respond to server request messages.
    """

    __serialize__ = ["resultCode"]

    def __init__(self, id=None, resultCode = 0):
        Message.__init__(self, id)

        self.resultCode = resultCode

class ServerMotdMessage(Message):
    """
    MOTD message received from the server upon connection.
    """

    __serialize__ = ["motd", "clientId"]

    def __init__(self, id=None, motd="Hello there!", clientId=None):
        Message.__init__(self, id)

        self.motd = motd
        self.clientId = clientId
        

def parseMessageString(string):
    """
    Parse a string for an xml message an return an instance of the contained
    message type.
    """

    node = et.fromstring(string)
    return serializer.deserialize(node)


def createMessageString(msg):
    root = serializer.serialize(msg, parent=None, tagName="message")
    return et.tostring(root)



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
