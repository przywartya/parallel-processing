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
        self.status = None
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
        # print("[M{}] Sent to {}".format(self.index, addres))

    def callback(self, ch, method, properties, body):
        message = json.loads(body)
        message_author = message['author']
        message_type = message['type']
        message_content = message['content']
        # print("[M{}] {}:{}, messages {}".format(self.index, method.routing_key, message_content, self.messages))
        if message_type == 'first' and self.status != 'loser':
            if int(message_content) not in self.first_messages:
                self.first_messages.append(int(message_content))
            # print("[{}]A {} {}".format(self.priority, self.first_messages, len(self.neighbors)))
            if len(self.first_messages) == len(self.neighbors):
                if all([self.priority > neigh_v for neigh_v in self.first_messages]):
                    print("{} WINNER with value {}".format(self.index, self.priority))
                    winner_to_neighs_message = {
                        'author': str(self.index),
                        'type': 'winner_to_neighs',
                        'content': str(self.priority)
                    }
                    message = json.dumps(winner_to_neighs_message)
                    for n in self.neighbors:
                        self.send_message(str(n.index), message)
                    print("{} {} SINGING! la la la ...".format(self.index, self.priority))
                    time.sleep(2)
                    print("{} {} BECOMING INACTIVE".format(self.index, self.priority))
                    # SEND TO NEIGHBORS THAT THEY NOW CAN REROLL
                    refresh_losers = {
                        'author': str(self.index),
                        'type': 'refresh_losers',
                        'content': str(self.priority)
                    }
                    message = json.dumps(refresh_losers)
                    for n in self.neighbors:
                        self.send_message(str(n.index), message)
                    ch.basic_cancel(method.consumer_tag)
                    return
        
        if message_type == 'refresh_losers' and self.status == 'loser':
            self.how_many_winners -= 1
            self.neighbors = [n for n in self.neighbors if n.index != int(message_author)]
            # print("[{}] Refresh losers acquired. How many winers? {}".format(self.priority, self.how_many_winners))
            # print("[{}] Neighbors {}".format(self.priority, self.first_messages))
            if not self.neighbors:
                print("{} {} SINGING! la la la ...".format(self.index, self.priority))
                time.sleep(2)
                print("{} {} BECOMING INACTIVE".format(self.index, self.priority))
                ch.basic_cancel(method.consumer_tag)
                return
            if self.how_many_winners == 0:
                self.status = None
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
            loser_to_neighs_message = {
                'author': str(self.index),
                'type': 'loser_to_neighs',
                'content': str(self.priority)
            }
            message = json.dumps(loser_to_neighs_message)
            for n in self.neighbors:
                self.send_message(str(n.index), message)
            # SEND TO ALL NEIGHBORS BUT THE WINNER
            # THAT YOU ARE A LOSER 
            # AND THEY SHOULD REROLL THE WINNER BETWEEN THEMSELVES
            # (IF THEY ARE NOT LOSERS)

        if message_type == 'loser_to_neighs' and self.status is not 'loser':
            winner_to_neighs_message = {
                'author': str(self.index),
                'type': 'winner_to_neighs',
                'content': str(self.priority)
            }
            message = json.dumps(winner_to_neighs_message)
            for n in self.neighbors:
                self.send_message(str(n.index), message)
            print("{} {} EWENEMENT SINGING! la la la ...".format(self.index, self.priority))
            time.sleep(2)
            print("{} {} BECOMING INACTIVE".format(self.index, self.priority))
            # SEND TO NEIGHBORS THAT THEY NOW CAN REROLL
            refresh_losers = {
                'author': str(self.index),
                'type': 'refresh_losers',
                'content': str(self.priority)
            }
            message = json.dumps(refresh_losers)
            for n in self.neighbors:
                self.send_message(str(n.index), message)
            ch.basic_cancel(method.consumer_tag)
            return

    def run(self):
        print("[M{}] Started".format(self.index))
        find_first_winner_message = {
            'author': str(self.index),
            'type': 'first',
            'content': str(self.priority)
        }
        message = json.dumps(find_first_winner_message)
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
