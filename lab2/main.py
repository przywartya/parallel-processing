import sys
from threading import Thread
sys.path.append('../')
from lab2.monitors.rostrum import Rostrum
from lab2.monitors.knight import Knight
from lab2.monitors.waiter import Waiter
from lab2.monitors.drinking_bout import DrinkingBout
from lab2.monitors.config import NUMBER_OF_KNIGTHS


def main():
    rostrum = Rostrum()
    drinking_bout = DrinkingBout()

    knights = initialize_knights(rostrum, drinking_bout)
    rostrum.register_knights(knights)
    k_threads, w_threads = start_party(knights, drinking_bout)
    stop_party(k_threads, w_threads)


def initialize_knights(rostrum, drinking_bout):
    knights = []
    knights.append(Knight(0, 1, NUMBER_OF_KNIGTHS-1, rostrum, drinking_bout))
    for i in range(1, NUMBER_OF_KNIGTHS-1):
        knights.append(Knight(i, i+1, i-1, rostrum, drinking_bout))
    knights.append(Knight(NUMBER_OF_KNIGTHS-1, 0, NUMBER_OF_KNIGTHS-2, rostrum, drinking_bout))
    return knights


def start_party(knights, drinking_bout):
    k_threads = start_knights_tittle_tattle(knights)
    w_threads = serve_cucumbers_and_nonalcoholic_wine(drinking_bout)
    return k_threads, w_threads


def stop_party(k_threads, w_threads):
    for t in k_threads:
        t.join()
    for t in w_threads:
        t.join()
    print("Party finished. Everyone has fallen asleep.")


def start_knights_tittle_tattle(knights):
    threads = map(
        lambda knight: Thread(target=(lambda: knight.revel())),
        knights
    )
    map(
        lambda k_thread: k_thread.start(),
        threads
    )
    return threads


def serve_cucumbers_and_nonalcoholic_wine(drinking_bout):
    waiter_one = Waiter(drinking_bout, ['nonalcoholicwine'])
    waiter_two = Waiter(drinking_bout, ['cucumber'])
    waiter_one_thread = Thread(target=(lambda: waiter_one.serve()))
    waiter_two_thread = Thread(target=(lambda: waiter_two.serve()))
    waiter_one_thread.start()
    waiter_two_thread.start()
    return [waiter_one_thread, waiter_two_thread]


if __name__ == "__main__":
    main()
