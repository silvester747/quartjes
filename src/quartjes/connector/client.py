# To change this template, choose Tools | Templates
# and open the template in the editor.

from quartjes.connector.protocol import QuartjesClientFactory
from twisted.internet import reactor, threads
from threading import Thread

__author__="rob"
__date__ ="$Jun 12, 2011 9:37:38 PM$"

class ClientConnector(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.factory = QuartjesClientFactory()

    def start(self):
        reactor.callLater(0, self._connect)
        if not reactor.running:
            self._reactor_thread = ReactorThread()
            self._reactor_thread.start()

    def _connect(self):
        print("Connecting...")
        reactor.connectTCP(self.host, self.port, self.factory)

    def stop(self):
        threads.blockingCallFromThread(reactor, reactor.stop)

class ReactorThread(Thread):
    def __init__(self):
        Thread.__init__(self, name="ReactorThread")
        self.daemon = True

    def run(self):
        print("Starting reactor")
        reactor.run()
        print("Reactor stopped")
        

if __name__ == "__main__":
    import time
    from quartjes.connector.messages import ServerRequestMessage

    cl = ClientConnector("localhost", 1234)
    cl.start()

    time.sleep(5)
    print("Sending message")
    msg = ServerRequestMessage(service_name="test", action="test", params={"text":"Spam"})
    result = cl.factory.send_message_blocking_from_thread(msg)
    print(result)

    time.sleep(5)
    print("Stopping client")
    cl.stop()
    
