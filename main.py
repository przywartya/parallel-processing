import time
import random
from pprint import pprint
from threading import Thread
from threading import Lock


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
        },
        'mercury': {
            'resource': Lock(),
        },
        'sulfur': {
            'resource': Lock(),
        },
        'alchemist-A': Lock(),
        'alchemist-B': Lock(),
        'alchemist-C': Lock(),
        'alchemist-D': Lock(),
    }
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
    ## nie potrzebuje locka na kazdy tym alchemisty
    ## wystarczy lock na 'alchemist' bo i tak obsluguje go one at a time :)

    ## jak sie nic nie wydarzylo to nie ma powodu zeby sprawdzac
    ## czyli wyslij z fabryki wiadomosc ze moze juz byc uzyta
    def __init__(self, alchemists_locks, factories, alchemists):
        self.alchemists_locks = alchemists_locks
        self.factories = factories
        self.alchemists = alchemists

    def run(self):
        mercury_lock = LOCK_BANK['resource_locks']['mercury']['resource']
        lead_lock = LOCK_BANK['resource_locks']['lead']['resource']
        sulfur_lock = LOCK_BANK['resource_locks']['sulfur']['resource']
        while len(self.alchemists) and WORK:
            time.sleep(PRODUCTION_WAIT)
            mercury_lock.acquire()
            lead_lock.acquire()
            sulfur_lock.acquire()
            factories_current_stock = [len(f.resources) for f in self.factories]
            print(factories_current_stock)
            if all(value > 0 for value in factories_current_stock):
                chosen_guild = []
                while not chosen_guild:
                    letter = random.choice(['A', 'B', 'C', 'D'])
                    chosen_guild = [alchemist for alchemist in self.alchemists if alchemist.guild == letter]
                chosen_alchemist = random.choice(chosen_guild)
                resources_locks, resources_factories, alchemist_lock, alchemist_thread = \
                    self.alchemist_preparation(chosen_alchemist)
                if all(value > 0 for value in factories_current_stock):
                    alchemist_lock.release()
                    alchemist_thread.join()
                    self.alchemists.remove(chosen_alchemist)
                    print('Ok alchemist has finished reading')
            mercury_lock.release()
            lead_lock.release()
            sulfur_lock.release()

    def alchemist_preparation(self, next_alchemist):
        print('Acquiring alchemist {} lock.'.format(next_alchemist.guild))
        alchemist_lock = self.alchemists_locks['alchemist-{}'.format(next_alchemist.guild)]
        alchemist_lock.acquire()
        next_alchemist_resources = [r.rtype for r in next_alchemist.resources]
        resources_locks = []
        for r in next_alchemist_resources:
            resources_locks.append(self.alchemists_locks[r]['resource'])
        resources_factories = []
        for r in next_alchemist_resources:
            for f in self.factories:
                if f.rtype == r:
                    resources_factories.append(f)
        alchemist_thread = self.free_alchemist(next_alchemist)
        return resources_locks, resources_factories, alchemist_lock, alchemist_thread

    def free_alchemist(self, a):
        th = a.get_thread()
        th.start()
        return th


class Alchemist(MyThread):
    def __init__(self, resources, lock, factories, guild):
        self.resources = resources
        self.lock = lock
        self.factories = factories
        self.guild = guild

    def run(self):
        print('Alchemist ({}+{}) runs'.format(self.resources[0].rtype, self.resources[1].rtype))
        with self.lock:
            print('I know that my resources are available! I get one of each :)')
            for f in self.factories:
                f.resources.pop()
                print("Factory {} has now {} resources".format(f.rtype, len(f.resources)))
        global GUILDS_BANK
        GUILDS_BANK[self.guild] += 1
        print('Guild {} has {} gold'.format(self.guild, GUILDS_BANK[self.guild]))
        print('Alchemist {} disappears'.format(id(self)))


class Warlock(MyThread):
    def __init__(self, factories, locks):
        self.factories = factories
        self.locks = locks

    def run(self):
        while WORK:
            time.sleep(WARLOCK_WAIT)
            random_factory = random.choice(self.factories)
            curse_lock = self.locks[random_factory.rtype]['curse']
            no_curses = self.locks[random_factory.rtype]['no_curses']
            with curse_lock:
                self.cast_curse(random_factory, no_curses)

    def cast_curse(self, factory, no_curses):
        if factory.curses == 0:
            no_curses.acquire()
        factory.curses += 1
        print("Warlock {} casts curse on {} factory (has {} curses)".format(id(self), factory.rtype, factory.curses))


class Sorcerer(MyThread):
    def __init__(self, factories, locks):
        self.factories = factories
        self.locks = locks

    def run(self):
        while WORK:
            time.sleep(SORCERER_WAIT)
            for f in self.factories:
                no_curses = self.locks[f.rtype]['no_curses']
                curse_lock = self.locks[f.rtype]['curse']
                with curse_lock:
                    if f.curses > 0:
                        self.remove_curse(f, no_curses)

    def remove_curse(self, factory, no_curses):
        if factory.curses == 1:
            no_curses.release()
        factory.curses -= 1
        print("Sorc {} cleans curse from {} factory (has {} curses)".format(id(self), factory.rtype, factory.curses))


class Factory(MyThread):
    ## Semafor z informacja o tym ze jest pusty kontener i klatwy (czekanie na mozliwosc produkcji)
    ## jednym albo dwoma

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
            with self.r_lock:
                with self.c_empty:
                    self.start_production()

    def start_production(self):
        while len(self.resources) < FACTORY_CAPACITY:
            self.resources.append(Resource(rtype=self.rtype))
        print("Factory {} has now {} resources [{} curses]".format(self.rtype, len(self.resources), self.curses))


def spawn_alchemists(alchemists_locks, guild_factories):
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
            lock=alchemists_locks['alchemist-A'],
            factories=guild_factories['a-factories'],
            guild='A',
        ))
    for i in range(0, NUMBER_OF_ALCHEMISTS_B):
        alchemists.append(Alchemist(
            resources=GUILD_B['resources'],
            lock=alchemists_locks['alchemist-B'],
            factories=guild_factories['b-factories'],
            guild='B'
        ))
    for i in range(0, NUMBER_OF_ALCHEMISTS_C):
        alchemists.append(Alchemist(
            resources=GUILD_C['resources'],
            lock=alchemists_locks['alchemist-C'],
            factories=guild_factories['c-factories'],
            guild='C'
        ))
    for i in range(0, NUMBER_OF_ALCHEMISTS_D):
        alchemists.append(Alchemist(
            resources=GUILD_D['resources'],
            lock=alchemists_locks['alchemist-D'],
            factories=guild_factories['d-factories'],
            guild='D',
        ))
    return alchemists


def spawn_wizards(factories):
    wizards = []
    for i in range(0, NUMBER_OF_WARLOCKS):
        wizards.append(Warlock(factories, LOCK_BANK['curse_locks']))
    for i in range(0, NUMBER_OF_SORCERERS):
        wizards.append(Sorcerer(factories, LOCK_BANK['curse_locks']))
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
    alchemists = spawn_alchemists(LOCK_BANK['resource_locks'], guild_factories)

    return factories + wizards + [WorkerThread(LOCK_BANK['resource_locks'], factories, alchemists)]


if __name__ == "__main__":
    threads = []
    for obj in setup_wizard_world():
        t = obj.get_thread()
        threads.append(t)
    print("\nWizard world emerges!\n")
    start = time.time()
    for t in threads:
        t.start()
    time.sleep(5)
    global WORK
    WORK = False
    for t in threads:
        t.join()
    end = time.time()
    print("Wizard world collapses. It lasted: " + str(end - start) + " seconds. Guild bank state: ")
    pprint(GUILDS_BANK)

## jak zrobie to co powyzej to moge sprobowac zamienic resource lock na jakies
## sygnalizowanie przez alchemsitow (ale to juz jest hardkor)