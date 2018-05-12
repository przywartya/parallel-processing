from threading import Condition, Lock
from . import config


class DrinkingBout:
    monitor_lock = Lock()
    bottle = 0
    # Cups are even, plates are odd.
    crockery_set = [0] * config.NUMBER_OF_KNIGTHS
    # Array of bools indicating whether a cup or plate is used by knight.
    crockery_set_usage = [False] * config.NUMBER_OF_KNIGTHS
    knights_can_eat_cvs = [Condition(monitor_lock) for _ in range(config.NUMBER_OF_KNIGTHS)]
    waiting_knights = [False] * config.NUMBER_OF_KNIGTHS

    def fill_bottle(self):
        with self.monitor_lock:
            print("Waiter fills bottle.")
            self.bottle = config.BOTTLE_CAPACITY
            self.try_satisfy_some_knights()

    def fill_cucumber_plates(self):
        with self.monitor_lock:
            print("Waiter fills plates with cucumbers.")
            for i in range(len(self.crockery_set)):
                self.crockery_set[i] = config.PLATE_CAPACITY
            self.try_satisfy_some_knights()

    def try_satisfy_some_knights(self):
        for i in range(len(self.waiting_knights)):
            if self.wants_eat(i) and self.can_eat(i):
                self.wake_up_knight_if_necessary(i)
                i += 1

    def start_drinking(self, knight):
        with self.monitor_lock:
            print("{}. Attempts drinking".format(knight))
            i = knight.idx
            while not self.can_eat(i):
                print("{}. Can't eat. Waiting.".format(knight))
                self.waiting_knights[i] = True
                self.knights_can_eat_cvs[i].wait()
                self.waiting_knights[i] = False
                print("{}. Signalized.".format(knight))
            print("{}. Drinking.".format(knight))
            self.pour_wine_to_cup(i)
            self.eat_cucumber(i)

    def stop_drinking(self, knight):
        with self.monitor_lock:
            print("{}. Stops drinking".format(knight))
            self.release_drinking_accessories(knight.idx)
            #  When Knight stops drinking he checks if his
            #  neighbours are able and want to drink.
            self.wake_up_knight_if_necessary(knight.l_idx)
            self.wake_up_knight_if_necessary(knight.r_idx)

    def wake_up_knight_if_necessary(self, i):
        if self.wants_eat(i) and self.can_eat(i):
            print("Signal[K{}]".format(i))
            self.knights_can_eat_cvs[i].notify()

    def eat_cucumber(self, i):
        plate_index = self.get_plate_for_knight(i)
        self.crockery_set[plate_index] -= 1
        self.crockery_set_usage[plate_index] = True

    def pour_wine_to_cup(self, i):
        # We don't need to worry about bottle getting < 0.
        # pouring is called only if can_eat is true.
        # can_eat checks if bottle is not empty
        self.bottle -= 1
        cup_index = self.get_cup_for_knight(i)
        self.crockery_set[cup_index] = 1
        self.crockery_set_usage[cup_index] = True

    def get_cup_for_knight(self, i):
        # If knight has odd index then cup is on his left.
        if i % 2 == 1:
            return i - 1
        # else cup is on his right
        return i

    def get_plate_for_knight(self, i):
        # If knight is King(zero index) then his plate is at index(NUMBER_OF_KNIGTHS - 1).
        if i == 0:
            return config.NUMBER_OF_KNIGTHS - 1
        # If knight has odd index then plate is on his right (next index).
        if i % 2 == 1:
            return i
        # And otherwise - if knight has even index then plate is on his left side.
        return i - 1

    def can_eat(self, i):
        if self.bottle_is_empty():
            return False

        plate = self.get_plate_for_knight(i)
        cup = self.get_cup_for_knight(i)

        if self.plate_is_used(plate) or self.cup_is_used(cup):
            return False

        if self.plate_has_cucumbers(plate):
            return True

        return False

    def wants_eat(self, i):
        wants_eat = self.waiting_knights[i]
        if wants_eat:
            print("Knight {}. Wants to eat.".format(i))
        return wants_eat

    def bottle_is_empty(self):
        is_empty = self.bottle == 0
        if is_empty:
            print("Bottle is empty")
        return is_empty

    def cup_has_wine(self, cup):
        has_wine = self.crockery_set[cup] > 0
        if not has_wine:
            print("No wine in cup {}".format(cup))
        return has_wine

    def plate_has_cucumbers(self, plate):
        has_cucumbers = self.crockery_set[plate] > 0
        if not has_cucumbers:
            print("No cucumbers on plate {}".format(plate))
        return has_cucumbers

    def cup_is_used(self, cup):
        is_used = self.crockery_set_usage[cup]
        if is_used:
            print("Cup {} is used.".format(cup))
        return is_used

    def plate_is_used(self, plate):
        is_used = self.crockery_set_usage[plate]
        if is_used:
            print("Plate {} is being used.".format(plate))
        return is_used

    def release_drinking_accessories(self, i):
        plate = self.get_plate_for_knight(i)
        cup = self.get_cup_for_knight(i)
        self.crockery_set_usage[plate] = False
        self.crockery_set_usage[cup] = False
