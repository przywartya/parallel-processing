import math
import time
import pika
from random import randint
from threading import Thread


with open("lab3/musicians/positions.txt") as f:
    content = f.readlines()
content = [x.strip() for x in content]
number_of_musicians = int(content[0])
some_big_number = number_of_musicians ** 4


class Musician:
    def __init__(self, index, position, priority):
        self.index = index
        self.position = position
        self.priority = priority
        self.neighbors = []
        self.channel, self.result = self.establish_connection()
        self.channel.queue_bind(exchange='direct_logs',
                                queue=self.result.method.queue,
                                routing_key=str(self.index))
        
    def establish_connection(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
        result = channel.queue_declare(exclusive=False)
        return channel, result

    def send_message(self, addres, message):
        properties = pika.BasicProperties(app_id=str(self.index))
        self.channel.basic_publish(exchange='direct_logs',
                                   properties=properties,
                                   routing_key=addres,
                                   body=message)
        print("[M{}] Sent to {}".format(self.index, addres))

    def run(self):
        print("[M{}] Started".format(self.index))
        # send v to all its neighbors
        for n in self.neighbors:
            self.send_message(str(n.index), str(self.priority))
        queue_name = self.result.method.queue
        messages = []
        wait_for_neighbors = len(self.neighbors)
        while True:
            result, _, message = self.channel.basic_get(queue=queue_name)
            if message:
                messages.append(message)
                wait_for_neighbors -= 1
            if wait_for_neighbors == 0:
                break
        print(str(self.position), str(self.priority), messages)
        return
        # If my priority is bigger than all my neighbors then I am a winner.
        if all([self.priority > int(neigh_v) for neigh_v in messages]):
            # print(self.index, str(self.position), str(self.priority), "WINNER")
            # Send to all my neighbors that they are losers
            for n in self.neighbors:
                n.priorities = ['not_winner']
                self.send_message(str(n.index), "not_winner")
            print("{} WINNER".format(self.index))
        else:
            time.sleep(1)
            result, props, message = self.channel.basic_get(queue=queue_name)
            if result:
                # I have a winner in my neighborhood, so I am a loser :/
                winner_id = int(props.app_id)
                for n in neighbors:
                    if n.index == winner_id:
                        n.priorities = ['winner']
                print("{} LOSER".format(self.index))
            else:
                print("{} Not loser not winner :P".format(self.index))
            # raise ValueError(self.index, result, sth, message)



    def print_neighbors(self):
        for n in self.neighbors:
            print(n)

    def __str__(self):
        return "Musician idx: {} position: {} priority: {}".format(
            self.index, self.position, self.priority)

class Neighbor:
    priorities = ['unknown', 'winner', 'not_winner']
    exchanges = ['unknown', 'rejected', 'accepted']

    def __init__(self, index, position):
        self.index = index
        self.position = position
        self.priority = ['unknown']
        self.exchange = ['unknown']
    
    def __str__(self):
        robust = "Neighbor: {} priority: {} exchange: {}".format(
            self.position, self.priority[0], self.exchange[0])
        simple = "Neighbor: {}".format(self.index)
        return simple

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def distance(self, other_position):
        dist = math.sqrt((math.pow(math.fabs(self.x - other_position.x), 2)) + math.pow(math.fabs(self.y - other_position.y), 2))
        # print("Distance to {} is {}".format(other_position, dist))
        return dist

    def __str__(self):
        return "({}, {})".format(self.x, self.y)

musicians = [Musician(i, Position(int(line[0]), int(line[2])), randint(1, some_big_number)) for i, line in enumerate(content[1:])]

for mi in musicians:
    neighbors = [Neighbor(mj.index, mj.position) for mj in musicians if mi is not mj and mi.position.distance(mj.position) <= 3]
    mi.neighbors = neighbors
    print(mi)
    mi.print_neighbors()
    print("\n")

print("CONCERTO!")
threads = map(lambda musician: Thread(target=(lambda: musician.run())), musicians)
map(lambda t: t.start(), threads)
map(lambda t: t.join(), threads)
