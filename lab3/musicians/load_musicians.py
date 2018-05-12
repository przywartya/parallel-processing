import math
import time
import pika
import json
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
        self.first_messages = []
        self.neighbors_weights_wihout_losers = []
        self.status = None
        self.did_gather_initial_info = False
        self.how_many_winners = 0
        
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

    def try_to_sing(self):
        if all([self.priority > neigh_v for neigh_v in self.first_messages]):
            print("{} WINNER with value {}".format(self.index, self.priority))
            message = json.dumps({
                'author': str(self.index),
                'type': 'winner_to_neighs',
                'content': str(self.priority)
            })
            for n in self.neighbors:
                self.send_message(str(n.index), message)
            self.start_singing()
            # SEND TO NEIGHBORS THAT THEY NOW CAN REROLL
            message = json.dumps({
                'author': str(self.index),
                'type': 'refresh_losers',
                'content': str(self.priority)
            })
            for n in self.neighbors:
                self.send_message(str(n.index), message)
            return True
        else:
            return False

    def start_singing(self):
        print("[{}] [{}] SINGING! la la la ...".format(self.index, self.priority))
        time.sleep(2)
        print("[{}] [{}] BECOMING INACTIVE".format(self.index, self.priority))

    def callback(self, ch, method, properties, body):
        message = json.loads(body)
        message_author = message['author']
        message_type = message['type']
        message_content = message['content']
        
        if message_type == 'first' and self.status != 'loser':
            if int(message_content) not in self.first_messages:
                self.first_messages.append(int(message_content))
            # print("[{}]A {} {}".format(self.priority, self.first_messages, len(self.neighbors)))
            # print("{} Wchodzi tu 0!".format(self.priority))
            if len(self.first_messages) == len(self.neighbors):
                self.did_gather_initial_info = True
                # print("{} Wchodzi tu 1 {}".format(self.priority, all([self.priority > neigh_v for neigh_v in self.first_messages])))
                if self.try_to_sing():
                    ch.basic_cancel(method.consumer_tag)
        
        if message_type == 'refresh_losers' and self.status == 'loser':
            self.how_many_winners -= 1
            self.neighbors = [n for n in self.neighbors if n.index != int(message_author)]
            # print("[{}] Refresh losers acquired. How many winers? {}".format(self.priority, self.how_many_winners))
            # print("[{}] Neighbors {}".format(self.priority, self.first_messages))
            if not self.neighbors:
                self.start_singing()
                ch.basic_cancel(method.consumer_tag)
                return
            if self.how_many_winners == 0:
                self.status = None
                if self.try_to_sing():
                    ch.basic_cancel(method.consumer_tag)
                    return
                else:
                    find_first_winner_message = {
                        'author': str(self.index),
                        'type': 'first',
                        'content': str(self.priority)
                    }
                    message = json.dumps(find_first_winner_message)
                    for n in self.neighbors:
                        self.send_message(str(n.index), message)

        if message_type == 'winner_to_neighs':
            self.how_many_winners += 1
            self.status = 'loser'
            winner_index = int(message_content)
            if winner_index in self.first_messages:
                self.first_messages.remove(int(message_content))
            print("{} LOSER with value {}, neighbors {}".format(self.index, self.priority, self.first_messages))
            message = json.dumps({
                'author': str(self.index),
                'type': 'loser_to_neighs',
                'content': str(self.priority)
            })
            for n in self.neighbors:
                self.send_message(str(n.index), message)

        if message_type == 'loser_to_neighs' and self.status != 'loser' and self.did_gather_initial_info:
            self.neighbors_weights_wihout_losers = [n for n in self.first_messages if n != int(message_content)]
            if not self.neighbors_weights_wihout_losers or all([self.priority > neigh_v for neigh_v in self.neighbors_weights_wihout_losers]):
                message = json.dumps({
                    'author': str(self.index),
                    'type': 'winner_to_neighs',
                    'content': str(self.priority)
                })
                for n in self.neighbors:
                    self.send_message(str(n.index), message)
                self.start_singing()
                message = json.dumps({
                    'author': str(self.index),
                    'type': 'refresh_losers',
                    'content': str(self.priority)
                })
                for n in self.neighbors:
                    self.send_message(str(n.index), message)
                ch.basic_cancel(method.consumer_tag)
                return

    def run(self):
        print("[M {}:{}] Started".format(self.index, self.priority))
        message = json.dumps({
            'author': str(self.index),
            'type': 'first',
            'content': str(self.priority)
        })
        for n in self.neighbors:
            self.send_message(str(n.index), message)
        queue_name = self.result.method.queue
        self.channel.basic_consume(self.callback,
                                   queue=queue_name,
                                   no_ack=True)
        self.channel.start_consuming()

    def print_neighbors(self):
        for n in self.neighbors:
            print(n)

    def __str__(self):
        return "Musician idx: {} position: {} priority: {}".format(
            self.index, self.position, self.priority)

class Neighbor:
    def __init__(self, index, position):
        self.index = index
        self.position = position
    
    def __str__(self):
        simple = "Neighbor: {}".format(self.index)
        return simple

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def distance(self, other_position):
        return math.sqrt((math.pow(math.fabs(self.x - other_position.x), 2)) + math.pow(math.fabs(self.y - other_position.y), 2))

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
