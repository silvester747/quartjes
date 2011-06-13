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
    Base class to be implemented by services at the server side using the protocol.
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

class ServiceInterface(object):
    """
    Client side interface to interact with services defined as Service objects
    at the server side.
    Returns undefined attributes as methods that will send a request to the service
    using the attribute name as action and keyword arguments as parameters.
    Override this class and add your own methods to allow positional arguments
    and different names.
    """
    def __init__(self, client, service_name):
        self.client = client
        self.service_name = service_name

    def __getattr__(self, name):
        """
        Return a special callable object as a proxy to the action on the service.
        """
        return ServiceInterfaceMethod(self.client, self.service_name, name)

class ServiceInterfaceMethod(object):
    """
    Callable object that will result in calling the action on the service and
    returning the result asif it is a normal method.
    """
    def __init__(self, client, service_name, action):
        self.client = client
        self.service_name = service_name
        self.action = action

    def __call__(self, *pargs, **kargs):
        if len(pargs) > 0:
            raise TypeError("Positional arguments not allowed by automatic ServiceInterface methods.")
        return self.client.send_request(self.service_name, self.action, kargs)

class TestService(Service):
    """
    Simple test service. Only implements the test action which will return the
    contents of the argument text.
    """

    def __init__(self):
        Service.__init__(self, "test")

    def action_test(self, text):
        return text

