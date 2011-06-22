"""
Connector components used to run a Quartjes server.
"""
__author__="Rob van der Most"
__date__ ="$May 27, 2011 9:24:25 PM$"

from twisted.internet import reactor, threads
from twisted.internet.endpoints import TCP4ServerEndpoint
from quartjes.connector.protocol import QuartjesServerFactory
from threading import Thread

class ServerConnector(object):
    """
    Server side endpoint of the quartjes connector.

    A server needs at least one ServerConnector to be able to accept incoming
    connections. The reactor used by the ServerConnector runs in its own thread
    so you do not need to worry about blocking it.

    Register Service instances with the ServerConnector to allow clients to
    access the services.
    """
    def __init__(self, port=1234):
        """
        Construct a new ServerConnector for the given port number. The new
        connector is not running yet!
        """
        self.port = port
        self.factory = QuartjesServerFactory()

    def start(self):
        """
        Start accepting incoming connections. Starts the reactor.
        """
        self._endpoint = TCP4ServerEndpoint(reactor, self.port)
        self._endpoint.listen(self.factory)
        if not reactor.running:
            self._reactor_thread = ServerConnector.ReactorThread()
            self._reactor_thread.start()

    def stop(self):
        """
        Stop accepting incoming connections. Stops the reactor.
        """
        threads.blockingCallFromThread(reactor, reactor.stop)

    def register_service(self, service):
        """
        Register a new Service instance to be accessible from clients.
        """
        self.factory.register_service(service)


    class ReactorThread(Thread):
        def __init__(self):
            Thread.__init__(self, name="ReactorThread")
            self.daemon = False

        def run(self):
            print("Starting reactor")
            reactor.run()
            print("Reactor stopped")

if __name__ == "__main__":
    from quartjes.connector.services import TestService

    server = ServerConnector(1234)
    server.register_service(TestService())
    server.start()

