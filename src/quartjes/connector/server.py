__author__="Rob van der Most"
__date__ ="$May 27, 2011 9:24:25 PM$"

from twisted.internet import reactor, threads
from twisted.internet.endpoints import TCP4ServerEndpoint
from quartjes.connector.protocol import QuartjesServerFactory
from threading import Thread

class ServerConnector(object):
    def __init__(self, port):
        self.port = port
        self.factory = QuartjesServerFactory()

    def start(self):
        self._endpoint = TCP4ServerEndpoint(reactor, self.port)
        self._endpoint.listen(self.factory)
        if not reactor.running:
            self._reactor_thread = ServerConnector.ReactorThread()
            self._reactor_thread.start()

    def stop(self):
        threads.blockingCallFromThread(reactor, reactor.stop)

    def register_service(self, service):
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

