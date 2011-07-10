"""
Base definitions of services.
The quartjes server is capable of offering multiple services. Each service
is identified by its service name.
"""
import traceback
__author__="rob"
__date__ ="$Jun 13, 2011 12:14:15 PM$"

from quartjes.connector.protocol import MessageHandleError

class Service(object):
    """
    Base class to be implemented by services at the server side using the protocol.

    In derived implementations create actions as function definitions with format:
    action_<action name>. Calling a method called <action name> on the corresponding
    service interface at the client side will result in action_<action name> to
    be called on the server. The parameters are only passed by keyword.

    Services are not active until registered with a ServerConnector.
    """

    def __init__(self, name="Unnamed"):
        self.name = name
        self.factory = None

    def call(self, action, *pargs, **kwargs):
        meth = getattr(self, "action_%s" % action, None)
        if meth == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_ACTION)

        try:
            return meth(*pargs, **kwargs)
        except TypeError as err:
            raise MessageHandleError(MessageHandleError.RESULT_INVALID_PARAMS, error_details=err.message)
        except Exception as err:
            traceback.print_exc()
            raise MessageHandleError(MessageHandleError.RESULT_EXCEPTION_RAISED, error_details=str(err))

    def send_topic_update(self, topic, *pargs, **kwargs):
        self.factory.send_topic_update_from_thread(self.name, topic, *pargs, **kwargs)


class ServiceInterface(object):
    """
    Client side interface to interact with services defined as Service objects
    at the server side.

    Returns undefined attributes as methods that will send a request to the service
    using the attribute name as action and keyword arguments as parameters.
    Override this class and add your own methods to allow positional arguments
    and different names.

    The subscribe method is used to register a callback method that is called when
    the service publishes an update on the selected topic.

    Always be ready to receive a MessageHandleError or ConnectionError when calling
    methods on a ServiceInterface.
    """
    def __init__(self, client_connector, service_name):
        """
        Construct a new service interface.

        Only to be called by the ClientConnector. To get a service interface use
        ClientConnector.get_service_interface
        """
        self.client_connector = client_connector
        self.service_name = service_name

    def __getattr__(self, name):
        """
        Return a special callable object as a proxy to the action on the service for
        each attribute that does not exist.
        """
        return ServiceInterfaceMethod(self.client_connector, self.service_name, name)

    def subscribe(self, topic, callback):
        """
        Subscribe to receive updates on the given topic. The callback is called
        each time an update is received. The callback should only accept keyword
        arguments matching the keywords send by the service.
        """
        self.client_connector.subscribe(self.service_name, topic, callback)

class ServiceInterfaceMethod(object):
    """
    Callable object that will result in calling the action on the service and
    returning the result asif it is a normal method.
    """
    def __init__(self, client_connector, service_name, action):
        self.client_connector = client_connector
        self.service_name = service_name
        self.action = action

    def __call__(self, *pargs, **kwargs):
        try:
            return self.client_connector.send_action_request(self.service_name, self.action, *pargs, **kwargs)
        except MessageHandleError as err:
            if err.error_code == MessageHandleError.RESULT_UNKNOWN_ACTION:
                raise AttributeError("Action %s does not exist in service %s." % (self.action, self.service_name))
            elif err.error_code == err.RESULT_INVALID_PARAMS:
                raise TypeError(err.error_details)
            else:
                raise

class TestService(Service):
    """
    Simple test service. Only implements the test action which will return the
    contents of the argument text.
    """

    def __init__(self):
        Service.__init__(self, "test")

    def action_test(self, text):
        return text

    def action_callback(self, text):
        self.send_topic_update("testtopic", text="Callback: %s" % text)
        return text

    def action_callback2(self, text):
        self.send_topic_update("testtopic", "Callback2: %s" % text)
        return text

