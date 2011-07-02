# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="rob"
__date__ ="$Jul 2, 2011 6:19:25 PM$"

from quartjes.connector.server import ServerConnector
from quartjes.controllers.stock_exchange import StockExchange
from quartjes.controllers.database import database

server = ServerConnector(1234)
exchange = StockExchange()
server.register_service(exchange.get_service())
server.register_service(database.get_service())
server.start()
