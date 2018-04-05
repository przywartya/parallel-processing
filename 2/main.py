import time
from threading import Thread, Condition, Lock

N = 4

knight_states = {
    'i': 'Idle',
    'w': 'Willing',
    't': 'Talking'
}


class Rastrum:
    def __init__(self):
        self.knight_cvs = []
        self.knight_states = []
        self.monitor_lock = Lock()
        for i in range(1, N+1):
            self.knight_cvs.append(Condition(self.monitor_lock))
            self.knight_states.append(knight_states['i'])

    def start_talking(self, i):
        self.knight_cvs[i % N].acquire()
        print("Started id: {}".format(i))
        self.knight_states[i % N] = knight_states['w']
        print("Knight states: {}".format(self.knight_states))
        left, this, right = (
            self.knight_states[(i-1) % N],
            self.knight_states[i % N],
            self.knight_states[(i+1) % N],
        )
        print("{} :: {}".format(left, right))
        while not (
            self.knight_states[(i - 1) % N] != knight_states['t']
            and self.knight_states[i % N] == knight_states['w']
            and self.knight_states[(i+1) % N] != knight_states['t']
        ):
            self.knight_cvs[i % N].wait()
        print("Started talking (id:{})".format(i))
        self.knight_states[i % N] = knight_states['t']
        self.knight_cvs[i % N].release()

    def stop_talking(self, i):
        self.knight_cvs[i % N].acquire()
        self.knight_states[i % N] = knight_states['i']
        self.knight_cvs[(i-1) % N].notify()
        self.knight_cvs[(i+1) % N].notify()
        print("Stopped id: {}".format(i))
        self.knight_cvs[i % N].release()


def knight_main(i, r):
    r.start_talking(i)
    time.sleep(1)
    r.stop_talking(i)


if __name__ == "__main__":
    rastrum = Rastrum()
    knights = []
    for i in range(1, N+1):
        thread = Thread(target=knight_main, args=(i, rastrum))
        thread.start()
        knights.append(thread)
    for thread in knights:
        thread.join()
