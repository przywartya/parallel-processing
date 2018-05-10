import random
import time
from . import config


class Knight:
    status = ['not_talking']

    def __init__(self, idx, r_idx, l_idx, rostrum, drinking_bout):
        self.idx = idx
        self.r_idx = r_idx
        self.l_idx = l_idx
        self.rostrum = rostrum
        self.drinking_bout = drinking_bout
        print('Knight created', idx, r_idx, l_idx, rostrum, self.status, drinking_bout)

    def revel(self):
        drinking_counter = 0
        # print("LETS GO K{}".format(self.idx))
        while drinking_counter < 10:
            self.rostrum.start_talking(self)
            time.sleep(1)
            self.rostrum.stop_talking(self)
            self.drinking_bout.start_drinking(self)
            time.sleep(1)
            self.drinking_bout.stop_drinking(self)
            drinking_counter += 1
            time.sleep(1)
            # activity = random.choice(['talking', 'drinking', 'sleeping'])
            # if activity == 'talking':
            #     # print("K[{}] talking".format
            #     self.rostrum.start_talking(self)
            #     time.sleep(1)
            #     self.rostrum.stop_talking(self)
            # elif activity == 'drinking':
            #     # print("K[{}] drinking".format(self.idx))
            #     self.drinking_bout.start_drinking(self)
            #     time.sleep(1)
            #     self.drinking_bout.stop_drinking(self)
            #     drinking_counter += 1
            # elif activity == 'sleeping':
            #     # print("K[{}] sleeping".format(self.idx))
            #     time.sleep(1)
        config.FALLEN_KNIGHTS += 1
        if config.FALLEN_KNIGHTS == config.NUMBER_OF_KNIGTHS:
            config.PARTY_OVER = True
        print(config.FALLEN_KNIGHTS, config.NUMBER_OF_KNIGTHS)
        print("{} falling asleep forever".format(self))

    def __str__(self):
        return "K{}".format(self.idx)


