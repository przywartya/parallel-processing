import time
import random
from threading import Thread
from threading import Lock

NUMBER_OF_WARLOCKS = 3
NUMBER_OF_SORCERERS = 3
FACTORY_CAPACITY = 2
PRODUCTION_WAIT = 0.5
WARLOCK_WAIT = 1
SORCERER_WAIT = 0.5
FACTORIES_WORK = True
A_GOLD = 0
B_GOLD = 0
C_GOLD = 0
D_GOLD = 0


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

    def __init__(self, alchemists_locks, factories, alchemists):
        self.alchemists_locks = alchemists_locks
        self.factories = factories
        self.alchemists = alchemists

    def run(self):
        l_lock = self.alchemists_locks['lead']['resource']
        s_lock = self.alchemists_locks['sulfur']['resource']
        m_lock = self.alchemists_locks['mercury']['resource']
        alchemist_a_lock = self.alchemists_locks['alchemist-A']
        print('Acquiring alchemist A lock.')
        alchemist_a_lock.acquire()
        self.free_alchemists()
        while True:
            l_factory = None
            m_factory = None
            for f in self.factories:
                if f.rtype == 'lead':
                    l_factory = f
                if f.rtype == 'mercury':
                    m_factory = f

            l_lock.acquire()
            m_lock.acquire()
            try:
                if l_factory.resources > 0 and m_factory.resources > 0:
                    print('Now i can get some lead and mercury')
                    alchemist_a_lock.release()
                    time.sleep(1)
                    alchemist_a_lock.acquire()
                    print('Ok alchemist has finished reading')
            finally:
                l_lock.release()
                m_lock.release()
                time.sleep(.5)

    def free_alchemists(self):
        a_threads = []
        for i in self.alchemists:
            th = i.get_thread()
            a_threads.append(th)
            th.start()


class Alchemist(MyThread):
    def __init__(self, resources, lock, factories):
        self.resources = resources
        self.lock = lock
        self.factories = factories

    def run(self):
        print('Alchemist ({}+{}) runs'.format(self.resources[0].rtype, self.resources[1].rtype))
        with self.lock:
            print('I know that my resources are available!')
            for f in self.factories:
                f.resources.pop()

            print("Factory {} has now {} resources".format(
                self.factories[0].rtype, len(self.factories[0].resources)))
            print("Factory {} has now {} resources".format(
                self.factories[1].rtype, len(self.factories[1].resources)))
        global A_GOLD
        A_GOLD += 1
        print('Guild A has {} gold'.format(A_GOLD))
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
            finally:
                random_factory = random.choice(self.factories)
                curse_lock.release()
                time.sleep(SORCERER_WAIT)

    def remove_curse(self, factory):
        print("Sorcerer {} removes curse on {} factory".format(id(self), factory.rtype))
        time.sleep(SORCERER_WAIT)
        factory.curses -= 1


class Factory(MyThread):
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
            factories=guild_factories['a-factories']
        )
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

    return factories + wizards + [WorkerThread(alchemists_locks, factories, alchemists)]


if __name__ == "__main__":
    threads = []
    for obj in setup_wizard_world():
        t = obj.get_thread()
        threads.append(t)
        t.start()
    # time.sleep(10)
    # FACTORIES_WORK = False
    # print(threads)
    # for t in threads:
    #     t.join()


# PROPER SOLUTION:
# each process should be treated equally
# it should be independent on the speed of processes
# the conflicts should be solved in finite time
# the parts of processes, which are outside the critical section, should be independent
