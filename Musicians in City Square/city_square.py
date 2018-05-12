from random import randint
from threading import Thread

from .musician import Musician
from .position import Position


def read_musicians_from_file(file_name):
    with open(file_name) as f:
        content = f.readlines()
    content = [line.strip() for line in content]
    number_of_musicians = int(content[0])
    some_big_number = number_of_musicians ** 4
    musicians_definitions = content[1:]
    return [
        Musician(i, Position(int(l[0]), int(l[2])), randint(1, some_big_number))
        for i, l in enumerate(musicians_definitions)
    ]


def set_musicians_neighbourhood(musicians):
    for mi in musicians:
        mi.neighbors = [
            mj.index 
            for mj in musicians 
            if mi is not mj and mi.position.distance(mj.position) <= 3
        ]
        print(mi)
        for n in mi.neighbors:
            print(n)
        print("\n")


def start_musicians_threads(musicians):
    print("CONCERTO!")
    threads = map(lambda musician: Thread(target=(lambda: musician.run())), musicians)
    map(lambda t: t.start(), threads)
    map(lambda t: t.join(), threads)


musicians = read_musicians_from_file("luby_mis/example.txt")
set_musicians_neighbourhood(musicians)
start_musicians_threads(musicians)