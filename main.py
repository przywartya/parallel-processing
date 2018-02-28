import time
from threading import Thread


NUMBER_OF_WARLOCKS = 3
NUMBER_OF_SORCERERS = 3
FACTORY_CAPACITY = 2
PRODUCTION_WAIT = 0.5
WARLOCK_WAIT = 1
SORCERER_WAIT = 0.7
FACTORIES_WORK = True


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
    def __init__(self, resources, curses, rtype):
        self.resources = resources
        self.curses = curses
        self.rtype = rtype

    def get_thread(self):
        return Thread(target=self.run)

    def run(self):
        while FACTORIES_WORK:
            self.start_production()

    def start_production(self):
        print("Factory {} has now {} resources".format(self.rtype, len(self.resources)))
        if len(self.resources) < FACTORY_CAPACITY and self.curses == 0:
            time.sleep(PRODUCTION_WAIT)
            self.resources.append(Resource(rtype=self.rtype))


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
    factories = [
        Factory(resources=[], curses=0, rtype=Resource.TYPES['lead']),
        Factory(resources=[], curses=0, rtype=Resource.TYPES['sulfur']),
        Factory(resources=[], curses=0, rtype=Resource.TYPES['mercury'])
    ]
    factory_threads = []
    for factory in factories:
        t = factory.get_thread()
        factory_threads.append(t)
        t.start()
    time.sleep(1)
    FACTORIES_WORK = False
    print(factory_threads)
    for t in factory_threads:
        t.join()
    print(factory_threads)


# PROPER SOLUTION:
# each process should be treated equally
# it should be independent on the speed of processes
# the conflicts should be solved in finite time
# the parts of processes, which are outside the critical section, should be independent
