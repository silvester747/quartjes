# To change this template, choose Tools | Templates
# and open the template in the editor.

from quartjes.connector.protocol import QuartjesClientFactory
from twisted.internet import reactor, threads
from threading import Thread
from quartjes.connector.services import ServiceInterface

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
            self._reactor_thread = ClientConnector.ReactorThread()
            self._reactor_thread.start()

    def _connect(self):
        print("Connecting...")
        reactor.connectTCP(self.host, self.port, self.factory)

    def stop(self):
        threads.blockingCallFromThread(reactor, reactor.stop)

    def send_action_request(self, service_name, action, params):
        return self.factory.send_action_request_from_thread(service_name, action, params)

    def subscribe(self, service_name, topic, callback):
        self.factory.subscribe_from_thread(service_name, topic, callback)

    def get_service_interface(self, service_name):
        return ServiceInterface(self, service_name)

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
    
