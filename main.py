import time
import random
import signal
import sys
from threading import Thread
from threading import Lock


NUMBER_OF_WARLOCKS = 3
NUMBER_OF_SORCERERS = 3
NUMBER_OF_ALCHEMISTS = 3
FACTORY_CAPACITY = 2
PRODUCTION_WAIT = 0.5
WARLOCK_WAIT = 1
SORCERER_WAIT = 0.5
FACTORIES_WORK = True
GUILDS_BANK = {
    'A': 0,
    'B': 0,
    'C': 0,
    'D': 0,
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
    # Czeka na lead, mercury, sulfur
    # Jak zdobedzie wszystkie 3 to losuje jedna z czterech gildii
    # I uwalnia lock dla alchemisty z tej wylosowanej gildii

    ## Nieefektywne budzenie jezeli jest duzo takich co nie moga byc
    ## Tysiac alchemistow A i jeden alchemista B

    ## Losowanie jeden z czterech gildii,
    ## sprawdzenie dla wylosowanej gildii dostepnosci jej resourcow
    ##

    ## nie potrzebuje locka na kazdy tym alchemisty
    ## wystarczy lock na 'alchemist' bo i tak obsluguje go one at a time :)

    ## jak sie nic nie wydarzylo to nie ma powodu zeby sprawdzac
    ## czyli wyslij z fabryki wiadomosc ze moze juz byc uzyta
    def __init__(self, alchemists_locks, factories, alchemists):
        self.alchemists_locks = alchemists_locks
        self.factories = factories
        self.alchemists = alchemists

    def run(self):
        random.shuffle(self.alchemists)
        alchemists_iterator = iter(self.alchemists)
        while True:
            try:
                next_alchemist = next(alchemists_iterator)
                resources_locks, resources_factories, \
                    alchemist_lock, alchemist_thread = self.alchemist_preparation(next_alchemist)
            except StopIteration:
                break
            try:
                for lock in resources_locks:
                    lock.acquire()
                print('All locks acqured')
                factories_current_stock = [len(f.resources) for f in resources_factories]
                if all(value > 0 for value in factories_current_stock):
                    alchemist_lock.release()
                    ## Manager will release, and all alchemists will begin
                    ## reacquiring the lock. I dont want this. I want one
                    ## release from manager, one acquire from one alchemist.
                    ## Then alchemists cannot reacquire unless manager acquires
                    ## and releases it once again.
                    alchemist_thread.join()
                    alchemist_lock.acquire()
                    print('Ok alchemist has finished reading')
                    ## free another alchemist
            finally:
                for lock in resources_locks:
                    lock.release()

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

            print("Factory {} has now {} resources".format(
                self.factories[0].rtype, len(self.factories[0].resources)))
            print("Factory {} has now {} resources".format(
                self.factories[1].rtype, len(self.factories[1].resources)))
        global GUILDS_BANK
        GUILDS_BANK[self.guild] += 1
        print('Guild {} has {} gold'.format(self.guild, GUILDS_BANK[self.guild]))
        print('Alchemist {} disappears'.format(id(self)))


class Warlock(MyThread):
    def __init__(self, factories, locks):
        self.factories = factories
        self.locks = locks

    def run(self):
        random_factory = random.choice(self.factories)
        while True:
            curse_lock = self.locks[random_factory.rtype]['curse']
            curse_lock.acquire()
            try:
                self.cast_curse(random_factory)
            finally:
                random_factory = random.choice(self.factories)
                curse_lock.release()
                time.sleep(WARLOCK_WAIT)

    def cast_curse(self, factory):
        print("Warlock {} casts curse on {} factory".format(id(self), factory.rtype))
        time.sleep(WARLOCK_WAIT)
        factory.curses += 1


class Sorcerer(MyThread):
    def __init__(self, factories, locks):
        self.factories = factories
        self.locks = locks

    def run(self):
        random_factory = random.choice(self.factories)
        while True:
            curse_lock = self.locks[random_factory.rtype]['curse']
            curse_lock.acquire()
            try:
                if random_factory.curses > 0:
                    self.remove_curse(random_factory)
                    ## jesli to jest ostatnia klatwa na tej fabryce to uwolnij lock dla tej fabryki ktory jej powie ze
                    ## moze juz pracowac
            finally:
                random_factory = random.choice(self.factories)
                curse_lock.release()
                time.sleep(SORCERER_WAIT)

    def remove_curse(self, factory):
        print("Sorcerer {} removes curse on {} factory".format(id(self), factory.rtype))
        time.sleep(SORCERER_WAIT)
        factory.curses -= 1


class Factory(MyThread):
    ## Semafor z informacja o tym ze jest pusty kontener i klatwy (czekanie na mozliwosc produkcji)
    ## jednym albo dwoma

    def __init__(self, resources, curses, rtype, c_lock, r_lock):
        self.resources = resources
        self.curses = curses
        self.rtype = rtype
        self.c_lock = c_lock
        self.r_lock = r_lock

    def run(self):
        while FACTORIES_WORK:
            self.c_lock.acquire()
            self.r_lock.acquire()
            try:
                self.start_production()
            finally:
                self.c_lock.release()
                self.r_lock.release()
                time.sleep(PRODUCTION_WAIT)

    def start_production(self):
        print("Factory {} has now {} resources [{} curses]".format(
            self.rtype, len(self.resources), self.curses))
        while len(self.resources) < FACTORY_CAPACITY and self.curses == 0:
            time.sleep(PRODUCTION_WAIT)
            self.resources.append(Resource(rtype=self.rtype))
        print("Factory {} has now {} resources [{} curses]".format(
            self.rtype, len(self.resources), self.curses))


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
    return [
        Alchemist(
            resources=GUILD_A['resources'],
            lock=alchemists_locks['alchemist-A'],
            factories=guild_factories['a-factories'],
            guild='A',
        ),
        Alchemist(
            resources=GUILD_A['resources'],
            lock=alchemists_locks['alchemist-A'],
            factories=guild_factories['a-factories'],
            guild='A'
        ),
        Alchemist(
            resources=GUILD_A['resources'],
            lock=alchemists_locks['alchemist-A'],
            factories=guild_factories['a-factories'],
            guild='A'
        ),
        Alchemist(
            resources=GUILD_B['resources'],
            lock=alchemists_locks['alchemist-B'],
            factories=guild_factories['b-factories'],
            guild='B'
        ),
        Alchemist(
            resources=GUILD_C['resources'],
            lock=alchemists_locks['alchemist-C'],
            factories=guild_factories['c-factories'],
            guild='C'
        ),
        Alchemist(
            resources=GUILD_C['resources'],
            lock=alchemists_locks['alchemist-C'],
            factories=guild_factories['c-factories'],
            guild='C'
        ),
    ]


def spawn_wizards(factories, wizard_locks):
    wizards = []
    for i in range(0, NUMBER_OF_WARLOCKS):
        wizards.append(Warlock(factories, wizard_locks))
    for i in range(0, NUMBER_OF_SORCERERS):
        wizards.append(Sorcerer(factories, wizard_locks))
    return wizards


def spawn_factories(wizard_locks, alchemists_locks):
    return [
        Factory(resources=[], curses=0, rtype=Resource.TYPES['lead'],
                c_lock=wizard_locks['lead']['curse'],
                r_lock=alchemists_locks['lead']['resource']),
        Factory(resources=[], curses=0, rtype=Resource.TYPES['sulfur'],
                c_lock=wizard_locks['sulfur']['curse'],
                r_lock=alchemists_locks['sulfur']['resource']),
        Factory(resources=[], curses=0, rtype=Resource.TYPES['mercury'],
                c_lock=wizard_locks['mercury']['curse'],
                r_lock=alchemists_locks['mercury']['resource'])
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
    alchemists_locks = {
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
    }
    factories = spawn_factories(wizard_locks, alchemists_locks)
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
    wizards = spawn_wizards(factories, wizard_locks)
    alchemists = spawn_alchemists(alchemists_locks, guild_factories)

    return factories + wizards


if __name__ == "__main__":
    threads = []
    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        for obj in setup_wizard_world():
            t = obj.get_thread()
            threads.append(t)
            t.start()
    except KeyboardInterrupt:
        print('Ok! End for today! Everybody goes home!')
        global FACTORIES_WORK
        FACTORIES_WORK = False
        print("!")
        for t in threads:
            t.join()
        print('Guild A: {} gold', GUILDS_BANK['A'])
        print('Guild B: {} gold', GUILDS_BANK['B'])
        print('Guild C: {} gold', GUILDS_BANK['C'])
        print('Guild D: {} gold', GUILDS_BANK['D'])
        print('Exitting ...')
        sys.exit()




# PROPER SOLUTION:
# each process should be treated equally
# it should be independent on the speed of processes
# the conflicts should be solved in finite time
# the parts of processes, which are outside the critical section, should be independent
