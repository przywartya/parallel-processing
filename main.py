import time

NUMBER_OF_WARLOCKS = 3
NUMBER_OF_SORCERERS = 3
FACTORY_CAPACITY = 2
PRODUCTION_WAIT = 0.5


class Alchemist:
    def __init__(self, resources, gold):
        self.gold = gold
        self.resources = resources


class Warlock:
    def cast_curse(self, factory):
        factory.curses += 1


class Sorcerer:
    def remove_curse(self, factory):
        if factory.curses > 0:
            factory.curses -= 1


class Resource:
    TYPES = {
        'lead': 'lead',
        'sulfur': 'sulfur',
        'mercury': 'mercury'
    }

    def __init__(self, rtype):
        self.rtype = rtype


class Factory:
    def __init__(self, resources, curses):
        self.resources = resources
        self.curses = curses

    def run(self):
        while True:
            if self.curses == 0:
                self.start_production()

    def start_production(self):
        if len(self.resources) < FACTORY_CAPACITY:
            time.sleep(PRODUCTION_WAIT)
            self.resources += 1


if __name__ == "__main__":
    lead = Resource(rtype=Resource.TYPES['lead'])
    sulfur = Resource(rtype=Resource.TYPES['sulfur'])
    mercury = Resource(rtype=Resource.TYPES['mercury'])
    Factory(resources=[lead], curses=0)
    Factory(resources=[sulfur], curses=0)
    Factory(resources=[mercury], curses=0)
