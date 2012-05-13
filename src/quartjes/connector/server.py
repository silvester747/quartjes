"""
Connector components used to run a Quartjes server.

To run a Quartjes server, create an instance of :class:`ServerConnector`. Then
register services to expose to the clients using :meth:`ServerConnector.register_service`.
For defining services see :mod:`quartjes.connector.services`.
"""
__author__ = "Rob van der Most"
__docformat__ = "restructuredtext en"

from twisted.internet import reactor, threads
from twisted.internet.endpoints import TCP4ServerEndpoint
from quartjes.connector.protocol import QuartjesServerFactory
from threading import Thread

class ServerConnector(object):
    """
    Server side endpoint of the quartjes connector.

    A server needs at exactly one ServerConnector to be able to accept incoming
    connections. The reactor used by the ServerConnector runs in its own thread
    so you do not need to worry about blocking it.

    Register Service instances with the ServerConnector to allow clients to
    access the services.
    
    Parameters
    ----------
    port : int
        Port number to listen for connections on.
    """
    def __init__(self, port=1234):
        self.port = port
        self.factory = QuartjesServerFactory()

    def start(self):
        """
        Start accepting incoming connections. Starts the reactor in a separate thread.
        """
        self._endpoint = TCP4ServerEndpoint(reactor, self.port)
        self._endpoint.listen(self.factory)
        if not reactor.running: #@UndefinedVariable
            self._reactor_thread = ServerConnector.ReactorThread()
            self._reactor_thread.start()

    def stop(self):
        """
        Stop accepting incoming connections. Stops the reactor.
        """
        threads.blockingCallFromThread(reactor, reactor.stop) #@UndefinedVariable

    def register_service(self, service, name):
        """
        Register a new Service instance to be accessible from clients.
        
        Parameters
        ----------
        service
            Service instance to register. It will be available for remote clients.
        name : string
            Name the service will be registered under. Clients must use this to 
            access the service.
        """
        self.factory.register_service(service, name)


    class ReactorThread(Thread):
        """
        Thread for running the reactor loop. Does not run as a daemon, so you
        need to manually stop it when closing the server application.
        """
        def __init__(self):
            Thread.__init__(self, name="ReactorThread")
            self.daemon = False

        def run(self):
            #print("Starting reactor")
            reactor.run(installSignalHandlers=0) #@UndefinedVariable
            #print("Reactor stopped")

if __name__ == "__main__":
    from quartjes.connector.services import TestRemoteService

    server = ServerConnector(1234)
    server.register_service(TestRemoteService(), "test")
    server.start()

