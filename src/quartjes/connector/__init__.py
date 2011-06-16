"""
Quartjes Connector

Allows connections between the Quartjes server and its clients.


Server components

A server must start the ServerConnector in quartjes.connector.server
For each component you want to be accessible through the connector implement
a subclass of quartjes.connector.services.Service and register it with the
ServerConnector

Client components

To connect to the server create a ClientConnector from quartjes.connector.client
and start it. On the ClientConnector call get_service_interface to get an interface
to call methods on a specific service on the server.

"""

__author__="Rob van der Most"
__date__ ="$May 27, 2011 8:52:57 PM$"