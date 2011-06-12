# To change this template, choose Tools | Templates
# and open the template in the editor.

from quartjes.connector.protocol import QuartjesClientFactory
from twisted.internet import reactor, threads
from multiprocessing import Process

__author__="rob"
__date__ ="$Jun 12, 2011 9:37:38 PM$"

class Client(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.factory = QuartjesClientFactory()

    def start(self):
        reactor.callWhenRunning(self._connect)
        self._reactorProcess = Process(target=self._reactorLoop())
        self._reactorProcess.start()

    def _connect(self):
        print("Connecting...")
        reactor.connectTCP(self.host, self.port, self.factory)

    def _reactorLoop(self):
        print("Starting reactor")
        reactor.run()
        print("Reactor stopped")

    def stop(self):
        threads.blockingCallFromThread(reactor, reactor.stop)
        

if __name__ == "__main__":
    cl = Client("localhost", 1234)
    cl.start()
    
