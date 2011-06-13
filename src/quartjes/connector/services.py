"""
Base definitions of services.
The quartjes server is capable of offering multiple services. Each service
is identified by its service name.
"""
__author__="rob"
__date__ ="$Jun 13, 2011 12:14:15 PM$"

from quartjes.connector.protocol import MessageHandleError

class Service(object):
    """
    Base class to be implemented by services using the protocol.
    In derived implementations create actions as function definitions with format:
    action_<action name>. The parameters are passed by keyword
    """

    def __init__(self, name="Unnamed"):
        self.name = name

    def call(self, action, params):
        meth = getattr(self, "action_%s" % action, None)
        if meth == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_ACTION)

        try:
            return meth(**params)
        except TypeError:
            raise MessageHandleError(MessageHandleError.RESULT_INVALID_PARAMS)

class TestService(Service):
    """
    Simple test service. Only implements the test action which will return the
    contents of the argument text.
    """

    def __init__(self):
        Service.__init__(self, "test")

    def action_test(self, text):
        return text


if __name__ == "__main__":

    ts = TestService()
    input = "test input"
    output = ts.call("test", {"text":input})
    assert input == output
