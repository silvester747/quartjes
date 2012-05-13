"""
Quartjes Connector
==================

Allows connections between the Quartjes server and its clients.

Server components
-----------------
To start a Quartjes server create a 
:class:`ServerConnector <quartjes.connector.server.ServerConnector>` and start
it. Then register the services to expose to the client using the
:meth:`register_service <quartjes.connector.server.ServerConnector.register_service>`
method.

To create a service, see the :mod:`quartjes.connector.services` module;. The service
will be exposed to the clients using the name specified in the
:meth:`register_service <quartjes.connector.server.ServerConnector.register_service>`
method.

>>> from quartjes.connector.server import ServerConnector
>>> port = 1234
>>> server = ServerConnector(port)
>>> server.start()
>>> service = MyService()
>>> server.register_service(service, "my_service_name")

Client components
-----------------

To connect to the server create a 
:class:`ClientConnector <quartjes.connector.client.ClientConnector>`
and start it. Then use the 
:meth:`get_service_interface <quartjes.connector.client.ClientConnector.get_service_interface>`
method to get an interface to the service on the server.

On the service interface the methods and events tagged using
:func:`remote_method <quartjes.connector.services.remote_method>` or
:func:`remote_event <quartjes.connector.services.remote_event>`
in the service can
be directly called as if it was a local method. However keep in mind that the
following exceptions can be raised:

* :class:`MessageHandleError <quartjes.connector.exceptions.MessageHandleError>`
* :class:`TimeoutError <quartjes.connector.exceptions.TimeoutError>`
* :class:`ConnectionError <quartjes.connector.exceptions.ConnectionError>`

By default the following services are automatically added to the 
:class:`ClientConnector <quartjes.connector.client.ClientConnector>` upon connection:

* :attr:`database <quartjes.connector.client.ClientConnector.database>`
* :attr:`stock_exchange <quartjes.connector.client.ClientConnector.stock_exchange>`

>>> from quartjes.connector.client import ClientConnector
>>> host = "10.1.2.3"
>>> port = 1234
>>> client = ClientConnector(host, port)
>>> client.start()
>>> service = client.get_service_interface("my_service_name")
>>> result = service.my_method("a", 1, 3)
>>> service.my_event += my_callback
"""

__author__="Rob van der Most"
__docformat__ = "restructuredtext en"
