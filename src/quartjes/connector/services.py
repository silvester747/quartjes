"""
Base definitions of services.
The quartjes server is capable of offering multiple services. Each service
is identified by its service name.
"""
import traceback
from quartjes.connector.exceptions import MessageHandleError
from axel import Event

def remote_service(C):
    """
    Decorator for classes that should expose methods as a remote service.
    """
    C._remote_service = True
    
    methods = []
    events = []
    
    for name in dir(C):
        attr = getattr(C, name)
        if getattr(attr, "_remote_method", False):
            methods.append(name)
        if getattr(attr, "_remote_event", False):
            events.append(name)
    
    C._remote_methods = methods
    C._remote_events = events        
    
    return C

def remote_method(F):
    """
    Decorator for methods that should expose them selves through a remote service.
    Also requires the class to be decorated as 'remote_service'.
    """
    F._remote_method = True
    return F

def remote_event(*args, **kwargs):
    """
    Generate an event that should be exposed through a remote service.
    Also requires the class to be decorated as 'remote_service'.
    Warning: this is _not_ a decorator.
    """
    E = Event(*args, **kwargs)
    E._remote_event = True
    return E

def prepare_remote_service(service):
    """
    Prepare a remote service class to be used as a remote service.
    """
    if not hasattr(service, "_remote_event_registry"):
        service._remote_event_registry = RemoteEventRegistry(service)

def execute_remote_method_call(service, method_name, *pargs, **kwargs):
    """
    Call a method on a class allowing remote service calls.
    Checks whether the method can be called and then performs the call.
    The result of the method call is returned.
    """
    
    assert service._remote_service, "Services must be decorated as remote_service"
    
    if not method_name in service._remote_methods:
        raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_METHOD)
    
    meth = getattr(service, method_name, None)
    if meth == None:
        raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_METHOD)

    try:
        return meth(*pargs, **kwargs)
    except TypeError as err:
        raise MessageHandleError(MessageHandleError.RESULT_INVALID_PARAMS, error_details=err.message)
    except Exception as err:
        traceback.print_exc()
        raise MessageHandleError(MessageHandleError.RESULT_EXCEPTION_RAISED, error_details=str(err))

def subscribe_to_remote_event(service, service_name, event_name, listener, factory):
    print("subscribing to event")
    service._remote_event_registry.subscribe(service_name, event_name, listener, factory)
    print("subscribing to event done")

class RemoteEventRegistry(object):
    """
    Registry for keeping track of remote subscribers to an event.
    """
    
    def __init__(self, service):
        self._events = {}
        self._service = service
        
    def subscribe(self, service_name, event_name, listener, factory):
        """
        Subscribe the listener to an event.
        """
        if not event_name in self._events:
            self._add_event(event_name)
            
        self._events[event_name].append((service_name, listener, factory))
        
        
    def unsubscribe(self, service_name, event_name, listener, factory):
        """
        Unsubscribe the listener from an event.
        """
        
    def _add_event(self, event_name):
        """
        Add an event to the list of registered events and make sure it is being
        listened to.
        """
        print("adding event: %s" % event_name)
        if not event_name in self._service._remote_events:
            print("error 1")
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_EVENT)    
        
        self._events[event_name] = []
        
        event = getattr(self._service, event_name, None)
        if event == None:
            print("error 2")
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_EVENT)    

        print("registering event listener")
        event += self._create_event_listener(event_name)
        print("adding event done")
        
    def _event_triggered(self, event_name, *pargs, **kwargs):
        """
        Catch a triggered event.
        """
        for (service_name, listener, factory) in self._events[event_name]:
            factory.send_event(service_name, event_name, listener, *pargs, **kwargs)
        
    def _create_event_listener(self, event_name):
        """
        Create a special method for listening to an event and then forwarding it
        to the clients.
        """
        def listener(*pargs, **kwargs):
            self._event_triggered(event_name, *pargs, **kwargs)
        return listener


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
    def __init__(self, client_factory, service_name):
        """
        Construct a new service interface.

        Only to be called by the ClientConnector. To get a service interface use
        ClientConnector.get_service_interface
        """
        self._client_factory = client_factory
        self._service_name = service_name

    def __getattr__(self, name):
        """
        Return a special callable object as a proxy to the action on the service for
        each attribute that does not exist.
        """
        return ServiceInterfaceAttribute(self._client_factory, self._service_name, name)

    def subscribe(self, event_name, callback):
        """
        Subscribe to receive updates on the given event_name. The callback is called
        each time an update is received. The callback should only accept keyword
        arguments matching the keywords send by the service.
        """
        self._client_factory.subscribe(self._service_name, event_name, callback)

class ServiceInterfaceAttribute(object):
    """
    Special proxy object that acts as either a callable method or an event.
    Calling this object will result in the corresponding server side method
    to be called. Adding or removing a callback results in the callback
    being (un)registered to the server event.
    """
    def __init__(self, client_factory, service_name, name):
        """
        Set all required parameters.
        """
        self._client_factory = client_factory
        self._service_name = service_name
        self._name = name

    def __call__(self, *pargs, **kwargs):
        """
        Act as a proxy to a server method.
        """
        try:
            return self._client_factory.send_method_call(self._service_name, self._name, *pargs, **kwargs)
        except MessageHandleError as err:
            if err.error_code == MessageHandleError.RESULT_UNKNOWN_METHOD:
                raise AttributeError("Method %s does not exist in service %s." % (self._name, self._service_name))
            elif err.error_code == err.RESULT_INVALID_PARAMS:
                raise TypeError(err.error_details)
            else:
                raise
    
    def __iadd__(self, handler):
        """
        Act as a server side event. Add the handler to the list of callbacks.
        """
        self._client_factory.subscribe(self._service_name, self._name, handler)
    
    def __isub__(self, handler):
        """
        Act as a server side event. Remove the handler from the list of callbacks.
        """
        # Not supported yet


@remote_service
class TestRemoteService(object):
    
    @remote_method
    def test(self, text):
        return text
    
    @remote_method
    def trigger(self, text):
        self.on_trigger(text="Callback: %s" % text)
        return text
    @remote_method
    def trigger2(self, text):
        self.on_trigger("Callback2: %s" % text)
        return text
    
    def not_remote_method(self):
        return "This should not happen!"
    
    on_trigger = remote_event()
    
