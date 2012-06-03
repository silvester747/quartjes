# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="rob"
__date__ ="$Jul 2, 2011 6:19:25 PM$"

from quartjes.connector.server import ServerConnector
from quartjes.controllers.stock_exchange import StockExchange
from quartjes.controllers.database import database

server = ServerConnector(1234)
exchange = StockExchange()
server.register_service(exchange, "stock_exchange")
server.register_service(database, "database")
server.start()
print("Server started on port 1234")
print("Press enter to stop")

raw_input()

print("Stopping server")
server.stop()
exchange.stop()