"""
Client component of the Quartjes connector. Use the ClientConnector to create
a connection to the Quartjes server.

Usage
-----
Create an instance of this object with the host and port to connect to.
Call the start() method to establish the connection.
Now the database and the stock_exchange variable can be used to communicate
with the server.

If you do not wish to connect to a server, but run a local server instead,
create the object without any arguments.

Example
-------
>>> conn = ClientConnector("192.168.1.1")
>>> conn.start()
>>> conn.database.get_drinks()

Available server methods
------------------------

Currently two server objects are made available upon connection. Please see the
documentation for the server object for available methods and events:

* database: :class:`quartjes.controllers.database.Database`
* stock_exchange: :class:`quartjes.controllers.stock_exchange.StockExchange`

Advanced
--------

Use the method get_service_interface to retrieve additional interfaces to a server side
service.

As long as the connector is running, it will keep trying to reconnect any
lost connections using an exponential back-off.

ClientConnector class
---------------------

"""
from quartjes.connector.protocol import QuartjesClientFactory
from twisted.internet import reactor, threads
from threading import Thread
from quartjes.connector.services import ServiceInterface
import quartjes.controllers.database
import quartjes.controllers.stock_exchange
from quartjes.connector.exceptions import TimeoutError

class ClientConnector(object):
    """
    Client side endpoint of the Quartjes connector.
    
    Parameters
    ----------
    host : string
        Host to connect to. If no host is specified, a local server is started.
    port : int
        Port to connect to.
        
    Attributes
    ----------
    host
    port
    factory
    database
    stock_exchange
    
    
    """

    def __init__(self, host=None, port=1234):
        self._host = host
        self._port = port
        self._factory = QuartjesClientFactory()
        self._database = None
        self._stock_exchange = None

    @property
    def host(self):
        """
        Hostname to connect to.
        Can only be changed when there is no active connection.
        """
        return self._host
    
    @host.setter
    def host(self, value):
        assert not self.is_connected(), "Host should not be changed will connected."
        self._host = value

    @property
    def port(self):
        """
        Port to connect to.
        Can only be changed when there is no active connection.
        """
        return self._port
    
    @port.setter
    def port(self, value):
        assert not self.is_connected(), "Port should not be changed will connected."
        self._port = value
        
    @property
    def factory(self):
        """
        The protocol factory used by the client to connect to the server.
        You normally should not need to access this. It is for advanced options.
        """
        return self._factory
    
    @property
    def database(self):
        """
        Reference to the currently running database. This can be a proxy to the
        database on the server or a local database.
        """
        return self._database
    
    @property
    def stock_exchange(self):
        """
        Reference to the currently running stock exchange. This can be a proxy
        to the stock exchange on the server or a local stock exchange.
        """
        return self._stock_exchange
    
    def start(self):
        """
        Start the connector and create a connection to the server. Starts a
        reactor loop in a separate thread.
        """
        if not self._host:
            print("No host selected, starting local instance.")
            self._database = quartjes.controllers.database.database
            self._stock_exchange = quartjes.controllers.stock_exchange.StockExchange()
        else:
            reactor.callLater(0, self._connect) #@UndefinedVariable
            if not reactor.running:             #@UndefinedVariable
                self._reactor_thread = ClientConnector._ReactorThread()
                self._reactor_thread.start()
            self._factory.wait_for_connection()

            self._database = self.get_service_interface("database")
            self._stock_exchange = self.get_service_interface("stock_exchange")

    def stop(self):
        """
        Stop the connector, closing the connection.
        The Reactor loop remains active as the reactor cannot be restarted.
        """
        if self._host:
            threads.blockingCallFromThread(reactor, self._factory.stopTrying)
        else:
            self._database = None
            self._stock_exchange.stop()
            self._stock_exchange = None

    def get_service_interface(self, service_name):
        """
        Construct a service interface for the service with the given name. Use
        the service interface to send requests to the corresponding service
        on the Quartjes server.
        
        Parameters
        ----------
        service_name : string
            Name of the service on the server to which you want a remote
            interface.
        
        Returns
        -------
        service_interface : :class:`quartjes.connector.services.ServiceInterface`
            An interface to the service.
            Please note that the existence of the service on the server is not
            verified until an actual method call has been done.
        """
        return ServiceInterface(self._factory, service_name)

    def is_connected(self):
        """
        Determine whether the connection to the server is active.
        A local service is also considered connected.
        
        Returns
        -------
        connected : boolean
            True if connected, False if not.
        """
        if not self._host:
            if self._database:
                return True
            else:
                return False
        else:
            return self._factory.is_connected()

    def _connect(self):
        """
        Internal method called from the reactor to start a new connection.
        """
        #print("Connecting...")
        reactor.connectTCP(self.host, self.port, self.factory)  #@UndefinedVariable

    class _ReactorThread(Thread):
        """
        Thread for running the reactor loop. This thread runs as a daemon, so
        if the main thread and any non daemon threads end, the reactor also
        stops running allowing the application to exit.
        """
        def __init__(self):
            Thread.__init__(self, name="ReactorThread")
            self.daemon = True

        def run(self):
            reactor.run(installSignalHandlers=0)       #@UndefinedVariable
        
def self_test():
    """
    Perform a self test of this module.
    
    Requires that the test from :mod:`quartjes.connector.server` is running.
    """
    import time

    def callback(text):
        print("Received event: " + text)

    cl = ClientConnector("localhost", 1234)
    cl.start()

    testService = cl.get_service_interface("test")

    time.sleep(1)
    print("Sending message")
    result = testService.test(text="Spam")
    print(result)
    result = testService.test("Spam")
    print(result)

    time.sleep(1)
    print("Subscribe to topic")
    testService.subscribe("on_trigger", callback)

    time.sleep(1)
    print("Trigger topic")
    testService.trigger(text="Eggs")
    testService.trigger2("Ham")
    
    print("Trigger timeout")
    try:
        testService.test_timeout(10)
    except TimeoutError:
        print("Timeout OK")
    else:
        assert False, "This should have triggered a timeout!"
        

    time.sleep(10)
    print("Stopping client")
    cl.stop()

    time.sleep(10)

    cl.start()

    time.sleep(1)
    print("Sending message")
    result = testService.test(text="Spam")
    print(result)

    cl.stop()

    time.sleep(1)
    
if __name__ == "__main__":
    self_test()