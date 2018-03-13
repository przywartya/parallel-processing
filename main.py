import time
import random
from threading import Thread
from threading import Lock, Semaphore


NUMBER_OF_WARLOCKS = 3
NUMBER_OF_SORCERERS = 3
NUMBER_OF_ALCHEMISTS_A = 3
NUMBER_OF_ALCHEMISTS_B = 3
NUMBER_OF_ALCHEMISTS_C = 3
NUMBER_OF_ALCHEMISTS_D = 3
FACTORY_CAPACITY = 2
PRODUCTION_WAIT = 0.5
WARLOCK_WAIT = 1
SORCERER_WAIT = 1.5
WORK = True
GUILDS_BANK = {
    'A': 0,
    'B': 0,
    'C': 0,
    'D': 0,
}
LOCK_BANK = {
    'curse_locks': {
        'lead': {
            'no_curses': Lock(),
            'curse': Lock()
        },
        'mercury': {
            'no_curses': Lock(),
            'curse': Lock()
        },
        'sulfur': {
            'no_curses': Lock(),
            'curse': Lock()
        },
    },
    'resource_locks': {
        'lead': {
            'resource': Lock(),
            'test': Semaphore(value=0)
        },
        'mercury': {
            'resource': Lock(),
            'test': Semaphore(value=0)
        },
        'sulfur': {
            'resource': Lock(),
            'test': Semaphore(value=0)
        },
    },
    'A': Semaphore(value=0),
    'B': Semaphore(value=0),
    'C': Semaphore(value=0),
    'D': Semaphore(value=0),
    'M': Semaphore(value=0)
}


class Resource:
    TYPES = {
        'lead': 'lead',
        'sulfur': 'sulfur',
        'mercury': 'mercury'
    }

    def __init__(self, rtype):
        self.rtype = rtype


class MyThread:
    def get_thread(self):
        return Thread(target=self.run)

    def run(self):
        raise NotImplementedError


class WorkerThread(MyThread):
    def __init__(self, factories, alchemists):
        self.factories = factories
        self.alchemists = alchemists

    def run(self):
        mercury_lock = LOCK_BANK['resource_locks']['mercury']['resource']
        lead_lock = LOCK_BANK['resource_locks']['lead']['resource']
        sulfur_lock = LOCK_BANK['resource_locks']['sulfur']['resource']
        while len(self.alchemists) and WORK:
            chosen_guild = []
            while not chosen_guild:
                letter = random.choice(['A', 'B', 'C', 'D'])
                chosen_guild = [alchemist for alchemist in self.alchemists if alchemist.guild == letter]
            chosen_alchemist = random.choice(chosen_guild)
            mercury_lock.acquire()
            lead_lock.acquire()
            sulfur_lock.acquire()
            if all(value > 0 for value in [len(f.resources) for f in self.factories]):
                print('(manager-action) [Alchemist {}] starts.'.format(chosen_alchemist.guild))
                LOCK_BANK[chosen_alchemist.guild].release()
                LOCK_BANK['M'].acquire()
                self.alchemists.remove(chosen_alchemist)
                print('(manager-action) [Alchemist {}] has finished.'.format(chosen_alchemist.guild))
            mercury_lock.release()
            lead_lock.release()
            sulfur_lock.release()


class Alchemist(MyThread):
    def __init__(self, resources, factories, guild):
        self.resources = resources
        self.factories = factories
        self.guild = guild

    def run(self):
        print('(alchemist-action) Alchemist {} [guild {}] started'.format(id(self), self.guild))
        LOCK_BANK[self.guild].acquire()
        for f in self.factories:
            if len(f.resources) == 2:
                LOCK_BANK['resource_locks'][f.rtype]['test'].release()
            f.resources.pop()
            print("(alchemist-action) [Factory {}] {} resources".format(f.rtype, len(f.resources)))
        global GUILDS_BANK
        GUILDS_BANK[self.guild] += 1
        print('(alchemist-action) [Guild {}] {} gold'.format(self.guild, GUILDS_BANK[self.guild]))
        LOCK_BANK['M'].release()


class Warlock(MyThread):
    def __init__(self, factories):
        self.factories = factories

    def run(self):
        while WORK:
            time.sleep(WARLOCK_WAIT)
            random_factory = random.choice(self.factories)
            with LOCK_BANK['curse_locks'][random_factory.rtype]['curse']:
                self.cast_curse(random_factory)

    def cast_curse(self, factory):
        if factory.curses == 0:
            LOCK_BANK['curse_locks'][factory.rtype]['no_curses'].acquire()
        factory.curses += 1
        print("(warlock-action) [Warlock {}] {} factory [{} curses]".format(id(self), factory.rtype, factory.curses))


class Sorcerer(MyThread):
    def __init__(self, factories):
        self.factories = factories

    def run(self):
        while WORK:
            time.sleep(SORCERER_WAIT)
            for factory in self.factories:
                with LOCK_BANK['curse_locks'][factory.rtype]['curse']:
                    if factory.curses > 0:
                        self.remove_curse(factory)

    def remove_curse(self, factory):
        if factory.curses == 1:
            LOCK_BANK['curse_locks'][factory.rtype]['no_curses'].release()
        factory.curses -= 1
        print("(sorcerer-action) [Sorc {}] {} factory [{} curses]".format(id(self), factory.rtype, factory.curses))


class Factory(MyThread):
    def __init__(self, resources, curses, rtype, c_lock, r_lock, c_empty):
        self.resources = resources
        self.curses = curses
        self.rtype = rtype
        self.c_lock = c_lock
        self.r_lock = r_lock
        self.c_empty = c_empty

    def run(self):
        while WORK:
            time.sleep(PRODUCTION_WAIT)
            self.start_production()

    def start_production(self):
        if len(self.resources) == 2:
            LOCK_BANK['resource_locks'][self.rtype]['test'].acquire()
        else:
            with self.c_empty:
                with self.r_lock:
                    self.resources.append(Resource(rtype=self.rtype))
            print("(factory-action) [Factory {}] {} resources [{} curses]".format(self.rtype, len(self.resources),
                                                                                  self.curses))


def spawn_alchemists(guild_factories):
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
    alchemists = []
    for i in range(0, NUMBER_OF_ALCHEMISTS_A):
        alchemists.append(Alchemist(
            resources=GUILD_A['resources'],
            factories=guild_factories['a-factories'],
            guild='A',
        ))
    for i in range(0, NUMBER_OF_ALCHEMISTS_B):
        alchemists.append(Alchemist(
            resources=GUILD_B['resources'],
            factories=guild_factories['b-factories'],
            guild='B'
        ))
    for i in range(0, NUMBER_OF_ALCHEMISTS_C):
        alchemists.append(Alchemist(
            resources=GUILD_C['resources'],
            factories=guild_factories['c-factories'],
            guild='C'
        ))
    for i in range(0, NUMBER_OF_ALCHEMISTS_D):
        alchemists.append(Alchemist(
            resources=GUILD_D['resources'],
            factories=guild_factories['d-factories'],
            guild='D',
        ))
    return alchemists


def spawn_wizards(factories):
    wizards = []
    for i in range(0, NUMBER_OF_WARLOCKS):
        wizards.append(Warlock(factories))
    for i in range(0, NUMBER_OF_SORCERERS):
        wizards.append(Sorcerer(factories))
    return wizards


def spawn_factories():
    return [
        Factory(resources=[], curses=0, rtype=Resource.TYPES['lead'],
                c_lock=LOCK_BANK['curse_locks']['lead']['curse'],
                r_lock=LOCK_BANK['resource_locks']['lead']['resource'],
                c_empty=LOCK_BANK['curse_locks']['lead']['no_curses']),
        Factory(resources=[], curses=0, rtype=Resource.TYPES['sulfur'],
                c_lock=LOCK_BANK['curse_locks']['sulfur']['curse'],
                r_lock=LOCK_BANK['resource_locks']['sulfur']['resource'],
                c_empty=LOCK_BANK['curse_locks']['sulfur']['no_curses']),
        Factory(resources=[], curses=0, rtype=Resource.TYPES['mercury'],
                c_lock=LOCK_BANK['curse_locks']['mercury']['curse'],
                r_lock=LOCK_BANK['resource_locks']['mercury']['resource'],
                c_empty=LOCK_BANK['curse_locks']['mercury']['no_curses'])
    ]


def setup_wizard_world():
    factories = spawn_factories()
    a_factories, b_factories, c_factories, d_factories = [], [], [], []
    guild_factories = {
        'a-factories': a_factories,
        'b-factories': b_factories,
        'c-factories': c_factories,
        'd-factories': d_factories,
    }
    for factory in factories:
        if factory.rtype == 'lead' or factory.rtype == 'mercury':
            a_factories.append(factory)
        if factory.rtype == 'sulfur' or factory.rtype == 'mercury':
            b_factories.append(factory)
        if factory.rtype == 'lead' or factory.rtype == 'sulfur':
            c_factories.append(factory)
        d_factories.append(factory)
    wizards = spawn_wizards(factories)
    alchemists = spawn_alchemists(guild_factories)
    return factories + wizards + alchemists + [WorkerThread(factories, alchemists)]


if __name__ == "__main__":
    for obj in setup_wizard_world():
        t = obj.get_thread()
        t.start()