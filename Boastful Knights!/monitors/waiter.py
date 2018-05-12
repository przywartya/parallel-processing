import time
from . import config


class Waiter:
    def __init__(self, drinking_bout, type):
        self.drinking_bout = drinking_bout
        self.type = type
        print('Waiter created', self.type)

    def serve(self):
        service = None
        if 'nonalcoholicwine' in self.type:
            service = self.drinking_bout.fill_cucumber_plates
        elif 'cucumber' in self.type:
            service = self.drinking_bout.fill_bottle

        while not config.PARTY_OVER:
            service()
            time.sleep(5)
