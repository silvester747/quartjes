import quartjes.controllers.database
import quartjes.connector.services
# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="rob"
__date__ ="$Jul 2, 2011 12:38:26 PM$"

class StockExchange(object):

    def __init__(self):
        self.transactions = []
        self.db = quartjes.controllers.database.database
        self.service = None

    def sell(self, drink, amount):
        local_drink = self.db.get_drink(drink.id)

        if not local_drink:
            return None
        
        total_price = amount * local_drink.sellprice()
        self.transactions.append((local_drink, amount))
        return total_price

    def calculate_factors(self):

        pass

    def get_service(self):
        if not self.service:
            self.service = StockExchangeService(self)
        return self.service

class StockExchangeService(quartjes.connector.services.Service):
    """
    Service to access the stock exchange.

    Service name: stock_exchange
    
    Supported methods
    =================
    
    sell(drink, amount)
    
    
    Supported topics
    ================

    next_round(drinks)

    """

    def __init__(self, exchange=None):
        super(StockExchangeService, self).__init__(name="stock_exchange")
        self.exchange = exchange

    def notify_next_round(self, drinks):
        self.sent_topic_update("next_round", drinks=drinks)

    def action_sell(self, drink, amount):
        return self.exchange.sell(drink, amount)

if __name__ == "__main__":
    from quartjes.connector.server import ServerConnector

    server = ServerConnector(1234)
    exchange = StockExchange()
    server.register_service(exchange.get_service())
    server.register_service(quartjes.controllers.database.database.get_service())
    server.start()