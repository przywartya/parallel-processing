import sys
from threading import Thread

sys.path.append('../')

from lab2.monitors.rostrum import Rostrum
from lab2.monitors.knight import Knight
from lab2.monitors.config import NUMBER_OF_KNIGTHS

def main():
    rostrum = Rostrum()
    knights = initialize_knights(rostrum)
    rostrum.register_knights(knights)
    k_threads = start_party(knights)
    stop_party(k_threads)


def initialize_knights(rostrum):
    knights = []
    knights.append(Knight(0, 1, NUMBER_OF_KNIGTHS-1, rostrum))
    for i in range(1, NUMBER_OF_KNIGTHS-1):
        knights.append(Knight(i, i+1, i-1, rostrum))
    knights.append(Knight(NUMBER_OF_KNIGTHS-1, 0, NUMBER_OF_KNIGTHS-2, rostrum))
    return knights


def start_party(knights):
    k_threads = start_knights_tittle_tattle(knights)
    return k_threads


def stop_party(k_threads):
    for t in k_threads:
        t.join()
    print("Party finished. Everyone has fallen asleep.")


def start_knights_tittle_tattle(knights):
    k_threads = []
    for i in range(0, NUMBER_OF_KNIGTHS):
        k_threads.append(Thread(
            target=(
                lambda: knights[i].revel()
            )
        ))
        k_threads[i].start()
    return k_threads




if __name__ == "__main__":
    main()