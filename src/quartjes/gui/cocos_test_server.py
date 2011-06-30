import time
import threading
import random
import quartjes.connector.services
from quartjes.controllers.database import Database


__author__="rob"
__date__ ="$Jun 30, 2011 5:40:49 PM$"


class CocosTestService(quartjes.connector.services.Service):

    def __init__(self):
        super(CocosTestService, self).__init__(name="cocos_test")

        db = Database()
        self.drinks = db.drinks

        thread = CocosTestService.UpdateThread(self.drinks, self)
        thread.start()

    def action_get_drinks(self):
        return self.drinks


    class UpdateThread(threading.Thread):
        def __init__(self, drinks, service):
            super(CocosTestService.UpdateThread, self).__init__()
            self.drinks = drinks
            self.service = service

        def _randomize_history(self):
            for drink in self.drinks:
                drink.history = zip(range(1, 8), [random.randint(6, 15) for x in range(1,8)])

        def run(self):
            while True:
                time.sleep(30)
                self._randomize_history()
                print("Sending update")
                self.service.send_topic_update("drinks", drinks=self.drinks)

if __name__ == "__main__":
    from quartjes.connector.server import ServerConnector

    server = ServerConnector(1234)
    server.register_service(CocosTestService())
    server.start()
