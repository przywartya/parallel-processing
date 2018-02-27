import time

NUMBER_OF_WARLOCKS = 3
NUMBER_OF_SORCERERS = 3
FACTORY_CAPACITY = 2
PRODUCTION_WAIT = 0.5
WARLOCK_WAIT = 1
SORCERER_WAIT = 0.7


class Alchemist:
    def __init__(self, resources, gold):
        self.gold = gold
        self.resources = resources


class Warlock:
    def run(self, factory):
        while True:
            self.cast_curse(factory)

    @staticmethod
    def cast_curse(factory):
        time.sleep(WARLOCK_WAIT)
        factory.curses += 1


class Sorcerer:
    def run(self, factory):
        while True:
            self.remove_curse(factory)

    @staticmethod
    def remove_curse(factory):
        time.sleep(SORCERER_WAIT)
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
    GUILD_A = {
        'resources': [lead, mercury],
        'alchemists': []
    }
    GUILD_B = {
        'resources': [mercury, sulfur],
        'alchemists': []
    }
    GUILD_C = {
        'resources': [lead, sulfur],
        'alchemists': []
    }
    GUILD_D = {
        'resources': [mercury, sulfur, lead],
        'alchemists': []
    }
    Factory(resources=[lead], curses=0)
    Factory(resources=[sulfur], curses=0)
    Factory(resources=[mercury], curses=0)
