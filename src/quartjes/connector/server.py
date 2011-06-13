# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="rob"
__date__ ="$May 27, 2011 9:24:25 PM$"

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from quartjes.connector.protocol import QuartjesServerFactory, TestService

factory = QuartjesServerFactory()
factory.register_service(TestService())

endpoint = TCP4ServerEndpoint(reactor, 1234)
endpoint.listen(factory)
reactor.run()

