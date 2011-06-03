__author__="Rob van der MOst"
__date__ ="$Jun 3, 2011 8:52:26 PM$"


class Message():
    """
    Base class all messages are derived from.
    """

class ServerRequestMessage(Message):
    """
    Message type used to send requests from clients to the server.
    """

    def __init__(self, id=None, module=None, action=None, params=None):
        self.id = id
        self.module = module
        self.action = action
        self.params = params

if __name__ == "__main__":
    print "Hello World"
