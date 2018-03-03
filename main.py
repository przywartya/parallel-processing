import time
import random
from threading import Thread
from threading import Lock

NUMBER_OF_WARLOCKS = 3
NUMBER_OF_SORCERERS = 3
FACTORY_CAPACITY = 2
PRODUCTION_WAIT = 0.5
WARLOCK_WAIT = 1
SORCERER_WAIT = 0.7
FACTORIES_WORK = True


class Resource:
    TYPES = {
        'lead': 'lead',
        'sulfur': 'sulfur',
        'mercury': 'mercury'
    }

    def __init__(self, rtype):
        self.rtype = rtype


class Alchemist:
    def __init__(self, resources, gold):
        self.gold = gold
        self.resources = resources


class Warlock:
    def __init__(self, factories, locks):
        self.factories = factories
        self.locks = locks

    def get_thread(self):
        return Thread(target=self.run)

    def run(self):
        while True:
            random_factory = random.choice(self.factories)
            curse_lock = self.locks[random_factory.rtype]['curse']
            curse_lock.acquire()
            try:
                self.cast_curse(random_factory)
            finally:
                curse_lock.release()

    def cast_curse(self, factory):
        print("Warlock {} casts curse on {} factory".format(id(self), factory.rtype))
        time.sleep(WARLOCK_WAIT)
        factory.curses += 1


class Sorcerer:
    def __init__(self, factories, locks):
        self.factories = factories
        self.locks = locks

    def get_thread(self):
        return Thread(target=self.run)

    def run(self):
        while True:
            random_factory = random.choice(self.factories)
            curse_lock = self.locks[random_factory.rtype]['curse']
            curse_lock.acquire()
            try:
                if random_factory.curses > 0:
                    self.remove_curse(random_factory)
            finally:
                curse_lock.release()

    def remove_curse(self, factory):
        print("Sorcerer {} removes curse on {} factory".format(id(self), factory.rtype))
        time.sleep(SORCERER_WAIT)
        factory.curses -= 1


class Factory:
    def __init__(self, resources, curses, rtype, c_lock):
        self.resources = resources
        self.curses = curses
        self.rtype = rtype
        self.c_lock = c_lock

    def get_thread(self):
        return Thread(target=self.run)

    def run(self):
        while FACTORIES_WORK:
            self.c_lock.acquire()
            try:
                self.start_production()
            finally:
                self.c_lock.release()

    def start_production(self):
        time.sleep(PRODUCTION_WAIT)
        print("Factory {} has now {} resources [{} curses]".format(
            self.rtype, len(self.resources), self.curses))
        if len(self.resources) < FACTORY_CAPACITY and self.curses == 0:
            time.sleep(PRODUCTION_WAIT)
            self.resources.append(Resource(rtype=self.rtype))


def spawn_alchemists():
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


def spawn_wizards(factories, wizard_locks):
    wizards = []
    for i in range(0, NUMBER_OF_WARLOCKS):
        wizards.append(Warlock(factories, wizard_locks))
    for i in range(0, NUMBER_OF_SORCERERS):
        wizards.append(Sorcerer(factories, wizard_locks))
    return wizards


def spawn_factories(wizard_locks):
    return [
        Factory(resources=[], curses=0, rtype=Resource.TYPES['lead'],
                c_lock=wizard_locks['lead']['curse']),
        Factory(resources=[], curses=0, rtype=Resource.TYPES['sulfur'],
                c_lock=wizard_locks['sulfur']['curse']),
        Factory(resources=[], curses=0, rtype=Resource.TYPES['mercury'],
                c_lock=wizard_locks['mercury']['curse'])
    ]


def setup_wizard_world():
    wizard_locks = {
        'lead': {
            'empty': Lock(),
            'curse': Lock()
        },
        'mercury': {
            'empty': Lock(),
            'curse': Lock()
        },
        'sulfur': {
            'empty': Lock(),
            'curse': Lock()
        },
    }
    factories = spawn_factories(wizard_locks)
    wizards = spawn_wizards(factories, wizard_locks)
    return factories+wizards


if __name__ == "__main__":
    threads = []
    for obj in setup_wizard_world():
        t = obj.get_thread()
        threads.append(t)
        t.start()
    time.sleep(10)
    FACTORIES_WORK = False
    print(threads)
    for t in threads:
        t.join()


# PROPER SOLUTION:
# each process should be treated equally
# it should be independent on the speed of processes
# the conflicts should be solved in finite time
# the parts of processes, which are outside the critical section, should be independent
