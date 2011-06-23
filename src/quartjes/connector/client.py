"""
Client component of the Quartjes connector. Use the ClientConnector to create
a connection to the Quartjes server.
"""
from quartjes.connector.protocol import QuartjesClientFactory
from twisted.internet import reactor, threads
from threading import Thread
from quartjes.connector.services import ServiceInterface

__author__="rob"
__date__ ="$Jun 12, 2011 9:37:38 PM$"

class ClientConnector(object):
    """
    Client side endpoint of the Quartjes connector.

    To create a connection to a Quartjes server, create an instance of this object
    and start it. An application can have at most one running ClientConnector.

    Use the method get_service_interface to retrieve an interface to a server side
    service.
    """

    def __init__(self, host, port):
        """
        Construct a new ClientConnector to connect to the given host and port number.
        """
        self.host = host
        self.port = port
        self.factory = QuartjesClientFactory()

    def start(self):
        """
        Start the connector and create a connection to the server. Starts a
        reactor loop in a separate thread.
        """
        reactor.callLater(0, self._connect)
        if not reactor.running:
            self._reactor_thread = ClientConnector.ReactorThread()
            self._reactor_thread.start()

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
        threads.blockingCallFromThread(reactor, reactor.stop)

    def send_action_request(self, service_name, action, params):
        """
        Send an action request to the server and wait for the response.
        This method is usually called from a service interface.
        """
        return self.factory.send_action_request_from_thread(service_name, action, params)

    def subscribe(self, service_name, topic, callback):
        """
        Subscribe to a topic to receive updates from the server.
        This method is usually called from a service interface.
        """
        self.factory.subscribe_from_thread(service_name, topic, callback)

    def get_service_interface(self, service_name):
        """
        Construct a service interface for the service with the given name. Use
        the service interface to send requests to the corresponding service
        on the Quartjes server.
        """
        return ServiceInterface(self, service_name)

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

    time.sleep(1)
    print("Subscribe to topic")
    testService.subscribe("testtopic", callback)

    time.sleep(1)
    print("Trigger topic")
    testService.callback(text="Eggs")

    time.sleep(100)
    print("Stopping client")
    cl.stop()
    
