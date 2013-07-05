"""
Base definitions of services.

A service is an object of which methods and events can be exposed for remote
invocation. Quartjesavond uses services to let clients communicate with
objects on the server.

To define a service first create a class containing the functionality to be
used by remote clients. Decorate this class with :meth:`remote_service`. Then decorate
each method that should be available remotely with :meth:`remote_method`. 
If the class contains any axel events, these can also be exposed. Define the
event using :meth:`remote_event` instead of Event.

The service can now be registered with the :class:`ServerConnector 
<quartjes.connector.server.ServerConnector>`. 
During registration a service name is given, which remote clients must use to gain access to
the service.

For an example, please see :class:`TestRemoteService`.

FIXME: Need to make proper support for multiple listeners for an event. For now consider
only one instance of each service interface.
"""

__author__ = "Rob van der Most"
__docformat__ = "restructuredtext en"

import traceback
from quartjes.connector.exceptions import MessageHandleError
from axel import Event

def remote_service(C):
    """
    Decorator for classes that should expose methods as a remote service.
    
    Parameters
    ----------
    C : class
        The class to decorate as a remote service.
    
    Returns
    -------
    C : class
        The decorated class.
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
    Also requires the class to be decorated as :func:`remote_service`.
    
    Parameters
    ----------
    F : method
        Method to decorate as a remote method.
    
    Returns
    -------
    F : method
        The decorated method.
    """
    F._remote_method = True
    return F

def remote_event(*args, **kwargs):
    """
    Generate an event that should be exposed through a remote service.
    Also requires the class to be decorated as :func:`remote_service`.
    Warning: this is _not_ a decorator.
    
    Parameters
    ----------
    *args
        Positional arguments to pass to the Event constructor.
    **kwargs
        Keyword arguments to pass to the Event constructor.
        
    Returns
    -------
    E : Event
        Event with remote access enabled.
    """
    E = Event(*args, **kwargs)
    E._remote_event = True
    return E

def prepare_remote_service(service):
    """
    Prepare a remote service class to be used as a remote service.
    
    Adds the remote event registry required to allow remote clients to receive
    event notifications.
    
    Parameters
    ----------
    service : class decorated as remote_service
        The service to prepare for remote access.
    """
    if not hasattr(service, "_remote_event_registry"):
        service._remote_event_registry = RemoteEventRegistry(service)

def execute_remote_method_call(service, method_name, *pargs, **kwargs):
    """
    Call a method on a class allowing remote service calls.
    Checks whether the method can be called and then performs the call.
    
    Parameters
    ----------
    service : class decorated as remote service
        Service to call a method on.
    method_name : string
        Name of the method to call.
    *pargs
        Positional arguments to pass to the method.
    **kwargs
        Keyword arguments to pass to the method.
    
    Returns
    -------
    result
        Result returned by the method call.
    
    Raises
    ------
    MessageHandleError
        An error occurred trying to handle the message.
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
        raise MessageHandleError(MessageHandleError.RESULT_EXCEPTION_RAISED, error_details=err)

def subscribe_to_remote_event(service, service_name, event_name, listener, factory):
    """
    Subscribe a client to an event on a service.
    
    Parameters
    ----------
    service : class decorated as remote service
        Service containing the event to subscribe to.
    service_name : string
        Name the service is registered under.
    event_name : string
        Name of the event to subscribe to.
    listener : :class:`quartjes.connector.protocol.QuartjesProtocol`
        Client requesting the subscription.
    factory : :class:`quartjes.connector.protocol.QuartjesServerFactory`
        Factory handling the connections.
    """
    service._remote_event_registry.subscribe(service_name, event_name, listener, factory)

class RemoteEventRegistry(object):
    """
    Registry for keeping track of remote subscribers to an event. Server side implementation.
    
    Parameters
    ----------
    service : class decorated as remote service
        Service this registry tracks the events for.
    """
    
    def __init__(self, service):
        self._events = {}
        self._service = service
        
    def subscribe(self, service_name, event_name, listener, factory):
        """
        Subscribe the listener to an event.
        
        Parameters
        ----------
        service_name : string
            Name the service is registered under.
        event_name : string
            Name of the event.
        listener : :class:`quartjes.connector.protocol.QuartjesProtocol`
            Client subscribing to the event.
        factory : :class:`quartjes.connector.protocol.QuartjesServerFactory`
            Factory handling client requests.
        """
        if not event_name in self._events:
            self._add_event(event_name)
            
        self._events[event_name].append((service_name, listener, factory))
        
        
    def unsubscribe(self, service_name, event_name, listener, factory):
        """
        Unsubscribe the listener from an event.
        
        Parameters
        ----------
        service_name : string
            Name the service is registered under.
        event_name : string
            Name of the event.
        listener : :class:`quartjes.connector.protocol.QuartjesProtocol`
            Client subscribing to the event.
        factory : :class:`quartjes.connector.protocol.QuartjesServerFactory`
            Factory handling client requests.
        """
        
    def _add_event(self, event_name):
        """
        Add an event to the list of registered events and make sure it is being
        listened to.
        
        Parameters
        ----------
        event_name : string
            Name of the event.
        """
        if not event_name in self._service._remote_events:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_EVENT)    
        
        self._events[event_name] = []
        
        event = getattr(self._service, event_name, None)
        if event == None:
            raise MessageHandleError(MessageHandleError.RESULT_UNKNOWN_EVENT)    

        event += self._create_event_listener(event_name)
        
    def _event_triggered(self, event_name, *pargs, **kwargs):
        """
        Catch a triggered event. This method is assigned to events to catch
        the subscribed events.
        
        Parameters
        ----------
        event_name : string
            Name of the event that has been triggered.
        *pargs
            Positional arguments for the event.
        **kwargs
            Keyword arguments for the event.
        """
        for (service_name, listener, factory) in self._events[event_name]:
            factory.send_event(service_name, event_name, listener, *pargs, **kwargs)
        
    def _create_event_listener(self, event_name):
        """
        Create a special method for listening to an event and then forwarding it
        to the clients.
        
        Parameters
        ----------
        event_name : string
            Name of the event.
        
        Returns
        -------
        listener : method
            The listener that can be assigned to the event.
        """
        def listener(*pargs, **kwargs):
            self._event_triggered(event_name, *pargs, **kwargs)
        return listener


class ServiceInterface(object):
    """
    Client side interface to interact with services defined as Service objects
    at the server side.
    
    For each attribute a special proxy object is returned that will act as both
    a callable method and an event. Based on the way it is used, the correct
    actions are triggered on the server.

    Always be ready to receive a MessageHandleError or ConnectionError when calling
    methods on a ServiceInterface.

    Parameters
    ----------
    client_factory : :class:`quartjes.connector.protocol.QuartjesClientFactory`
        Factory handling connections to the server.
    service_name : string
        Name of the service to provide an interface to.
    
    """
    
    __slots__ = ["_client_factory", "_service_name", "_events"]
    
    def __init__(self, client_factory, service_name):
        """
        Construct a new service interface.

        Only to be called by the ClientConnector. To get a service interface use
        ClientConnector.get_service_interface
        """
        self._client_factory = client_factory
        self._service_name = service_name
        self._events = {}

    def __getattr__(self, name):
        """
        Return a special callable object as a proxy to the action on the service for
        each attribute that does not exist.
        """
        return ServiceInterfaceAttribute(self, name)
    
    def _do_remote_call(self, name, *pargs, **kwargs):
        """
        Perform the remote method call
        
        Parameters
        ----------
        name
            Name of the remote method to call.
        *pargs
            Positional arguments for the method.
        **kwargs
            Keyword arguments for the method.
        
        Returns
        -------
        result
            Result returned from the server method.
            
        Raises
        ------
        AttributeError
            The method does not exist on the server.
        TypeError
            The method on the server expects different arguments.
        MessageHandleError
            An error occurred handling the message.
        ConnectionError
            An error occurred in the connection to the server.
        TimeoutError
            A timeout occurred in the request to the server.
        """
        try:
            return self._client_factory.send_method_call(self._service_name, name, *pargs, **kwargs)
        except MessageHandleError as err:
            if err.error_code == MessageHandleError.RESULT_UNKNOWN_METHOD:
                raise AttributeError("Method %s does not exist in service %s." % (name, self._service_name))
            elif err.error_code == err.RESULT_INVALID_PARAMS:
                raise TypeError(err.error_details)
            elif err.error_code == err.RESULT_EXCEPTION_RAISED:
                raise err.error_details
            else:
                raise

    def _do_subscribe(self, name, handler):
        """
        Act as a server side event. Add the handler to the list of callbacks.
        
        Parameters
        ----------
        name : string
            Name of the event to subscribe to.
        handler : method
            Method that handles event notifications.

        Raises
        ------
        MessageHandleError
            An error occurred handling the message.
        ConnectionError
            An error occurred in the connection to the server.
        TimeoutError
            A timeout occurred in the request to the server.
        """
        
        #FIXME: This approach does not work if there is more than one instance
        # of the service interface. Then one will lose updates
        event_list = self._events.get(name, None)
        if event_list is None:
            event_list = Event()
            self._events[name] = event_list
            self._client_factory.subscribe(self._service_name, name, event_list)
        event_list += handler

    def operator_handler(name): #@NoSelf
        def handler(self, *pargs, **kwargs):
            return self._do_remote_call(name, *pargs, **kwargs)
        return handler
    
    __bool__ = operator_handler("__bool__")
    __call__ = operator_handler("__call__")
    __lt__ = operator_handler("__lt__")
    __le__ = operator_handler("__le__")
    __eq__ = operator_handler("__eq__")
    __ne__ = operator_handler("__ne__")
    __gt__ = operator_handler("__gt__")
    __ge__ = operator_handler("__ge__")
    __len__ = operator_handler("__len__")
    __contains__ = operator_handler("__contains__")
    __getitem__ = operator_handler("__getitem__")
    __setitem__ = operator_handler("__setitem__")
    __delitem__ = operator_handler("__delitem__")
    
    del operator_handler

class ServiceInterfaceAttribute(object):
    """
    Special proxy object that acts as either a callable method or an event.
    Calling this object will result in the corresponding server side method
    to be called. Adding or removing a callback results in the callback
    being (un)registered to the server event.
    
    Parameters
    ----------
    client_factory : :class:`quartjes.connector.protocol.QuartjesClientFactory`
        Factory handling connections to the server.
    service_name : string
        Name of the service to communicate with.
    name : string
        Name of the event or method.
    """
    def __init__(self, interface, name):
        """
        Set all required parameters.
        """
        self._interface = interface
        self._name = name

    def __call__(self, *pargs, **kwargs):
        """
        Act as a proxy to a server method.
        
        Parameters
        ----------
        *pargs
            Positional arguments for the method.
        **kwargs
            Keyword arguments for the method.
        
        Returns
        -------
        result
            Result returned from the server method.
            
        Raises
        ------
        AttributeError
            The method does not exist on the server.
        TypeError
            The method on the server expects different arguments.
        MessageHandleError
            An error occurred handling the message.
        ConnectionError
            An error occurred in the connection to the server.
        TimeoutError
            A timeout occurred in the request to the server.
        """
        return self._interface._do_remote_call(self._name, *pargs, **kwargs)
    
    def __iadd__(self, handler):
        """
        Act as a server side event. Add the handler to the list of callbacks.
        
        Parameters
        ----------
        handler : method
            Method that handles event notifications.

        Raises
        ------
        MessageHandleError
            An error occurred handling the message.
        ConnectionError
            An error occurred in the connection to the server.
        TimeoutError
            A timeout occurred in the request to the server.
        """
        self._interface._do_subscribe(self._name, handler)
    
    def __isub__(self, handler):
        """
        Act as a server side event. Remove the handler from the list of callbacks.

        Parameters
        ----------
        handler : method
            Method that handles event notifications.
        """
        # Not supported yet


@remote_service
class TestRemoteService(object):
    """
    Special class to test the remote service functionality.
    """
    @remote_method
    def test(self, text):
        return text
    
    @remote_method
    def test_timeout(self, timeout):
        import time
        time.sleep(timeout)

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
    
