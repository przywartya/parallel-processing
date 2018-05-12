import math


class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def distance(self, other_position):
        return math.sqrt((math.pow(math.fabs(self.x - other_position.x), 2)) + math.pow(math.fabs(self.y - other_position.y), 2))

    def __str__(self):
        return "({}, {})".format(self.x, self.y)