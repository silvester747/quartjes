"""
Client component of the Quartjes connector. Use the ClientConnector to create
a connection to the Quartjes server.
"""
from quartjes.connector.protocol import QuartjesClientFactory
from twisted.internet import reactor, threads
from threading import Thread
from quartjes.connector.services import ServiceInterface
import quartjes.controllers.database
import quartjes.controllers.stock_exchange

__author__="rob"
__date__ ="$Jun 12, 2011 9:37:38 PM$"

class ClientConnector(object):
    """
    Client side endpoint of the Quartjes connector.

    =Usage=
    Create an instance of this object with the host and port to connect to.
    Call the start() method to establish the connection.
    Now the database and the stock_exchange variable can be used to communicate
    with the server.

    If you do not wish to connect to a server, but run a local server instead,
    create the object without any arguments.

    =Example=
    conn = ClientConnector("192.168.1.1")
    conn.start()
    conn.database.get_drinks()

    =Available server methods=

    ==database==
    get_drinks()
    update_drink(drink)
    add_drink(drink)
    remove_drink(drink)

    get_mixes()
    update_mix(mix)
    add_mix(mix)
    remove_mix(mix)

    add(obj)
    remove(obj)
    update(obj)

    ==stock_exchange==
    sell(drink, amount)

    =Advanced=

    Use the method get_service_interface to retrieve additional interfaces to a server side
    service.

    As long as the connector is running, it will keep trying to reconnect any
    lost connections using an exponential back-off.
    """

    def __init__(self, host=None, port=1234):
        """
        Construct a new ClientConnector to connect to the given host and port number.
        If no host is given a local server is started.
        """
        self.host = host
        self.port = port
        self.factory = QuartjesClientFactory()
        self.database = None
        self.stock_exchange = None

    def start(self):
        """
        Start the connector and create a connection to the server. Starts a
        reactor loop in a separate thread.
        """
        if not self.host:
            print("No host selected, starting local instance.")
            self.database = quartjes.controllers.database.database
            self.stock_exchange = quartjes.controllers.stock_exchange.StockExchange()
        else:
            reactor.callLater(0, self._connect)
            if not reactor.running:
                self._reactor_thread = ClientConnector.ReactorThread()
                self._reactor_thread.start()
            self.factory.wait_for_connection()

            self.database = self.get_service_interface("database")
            self.stock_exchange = self.get_service_interface("stock_exchange")

    def _connect(self):
        """
        Internal method called from the reactor to start a new connection.
        """
        #print("Connecting...")
        reactor.connectTCP(self.host, self.port, self.factory)

    def stop(self):
        """
        Stop the connector, closing the connection. Stops the reactor loop.
        """
        if self.host:
            threads.blockingCallFromThread(reactor, self.factory.stopTrying)
            threads.blockingCallFromThread(reactor, reactor.stop)
        else:
            self.database = None
            self.stock_exchange.stop()
            self.stock_exchange = None

    def send_action_request(self, service_name, action, *pargs, **kwargs):
        """
        Send an action request to the server and wait for the response.
        This method is usually called from a service interface.
        """
        return self.factory.send_action_request(service_name, action, *pargs, **kwargs)

    def subscribe(self, service_name, topic, callback):
        """
        Subscribe to a topic to receive updates from the server.
        This method is usually called from a service interface.
        """
        self.factory.subscribe(service_name, topic, callback)

    def get_service_interface(self, service_name):
        """
        Construct a service interface for the service with the given name. Use
        the service interface to send requests to the corresponding service
        on the Quartjes server.
        """
        return ServiceInterface(self, service_name)

    def is_connected(self):
        """
        Determine whether a connection is active.
        """
        if not self.host:
            if self.database:
                return True
            else:
                return False
        else:
            return self.factory.is_connected()

    class ReactorThread(Thread):
        """
        Thread for running the reactor loop. This thread runs as a daemon, so
        if the main thread and any non daemon threads end, the reactor also
        stops running allowing the application to exit.
        """
        def __init__(self):
            Thread.__init__(self, name="ReactorThread")
            self.daemon = True

        def run(self):
            #print("Starting reactor")
            reactor.run()
            #print("Reactor stopped")
        

if __name__ == "__main__":
    import time

    def callback(text):
        print(text)

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
    testService.subscribe("testtopic", callback)

    time.sleep(1)
    print("Trigger topic")
    testService.callback(text="Eggs")
    testService.callback2("Ham")

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
    
