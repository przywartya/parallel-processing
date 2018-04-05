import random
import time


class Knight:
    status = ['not_talking']

    def __init__(self, idx, r_idx, l_idx, rostrum):
        self.idx = idx
        self.r_idx = r_idx
        self.l_idx = l_idx
        self.rostrum = rostrum
        print('Knight created', idx, r_idx, l_idx, rostrum, self.status)

    def revel(self):
        drinking_counter = 0
        while(True):
            if (drinking_counter >= 10):
                break
            activity = random.choice(['talking', 'drinking', 'sleeping'])
            if activity == 'talking':
                self.perform_speech()
            elif activity == 'drinking':
                pass
            elif activity == 'sleeping':
                self.sleep()

    def perform_speech(self):
        self.rostrum.start_talking(self)
        time.sleep(1)
        self.rostrum.stop_talking(self)

    def sleep(self):
        time.sleep(1)

    def __str__(self):
        return "K{}".format(self.idx)


