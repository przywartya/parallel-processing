import json
import pika
import time


class Musician:
    def __init__(self, index, position, priority):
        self.index = index
        self.position = position
        self.priority = priority
        self.channel, self.channel_name = self.establish_connection()
        self.neighbors = []
        self.status = None
        self.finished_initialization = False
        self.initial_neighborhood_priorities = []
        self.number_of_winners_in_neighborhood = 0
        self.losers_neighborhood_priorities = []

    def establish_connection(self):
        # RABBIT_MQ SPECIFIC CONFIGURATION
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
        result = channel.queue_declare(exclusive=False)
        channel_name = result.method.queue
        channel.queue_bind(exchange='direct_logs',
                           queue=channel_name,
                           routing_key=str(self.index))
        return channel, channel_name

    def run(self):
        print("[Musician {}:{}] Started".format(self.index, self.priority))
        # SEND INITIALIZATION MESSAGE TO ALL NEIGHBORS
        self.broadcast_message_to_neighbors('initialization')
        # START LISTENING ON OWN CHANNEL
        self.channel.basic_consume(self.callback, queue=self.channel_name, no_ack=True)
        self.channel.start_consuming()

    def broadcast_message_to_neighbors(self, message_type):
        for neighbor in self.neighbors:
            self.send_message(neighbor, message_type)

    def send_message(self, address, message_type):
        message = json.dumps({
            'neighbor_id': str(self.index),
            'neighbor_priority': str(self.priority),
            'type': message_type
        })
        self.channel.basic_publish(exchange='direct_logs', routing_key=str(address), body=message)

    def callback(self, ch, method, properties, body):
        message = json.loads(body)
        neighbor_id = int(message['neighbor_id'])
        neighbor_priority = int(message['neighbor_priority'])
        message_type = message['type']

        if message_type == 'initialization':
            # ADD NEIGHBOR INFORMATION TO self.initial_neighborhood_priorities
            if neighbor_priority not in self.initial_neighborhood_priorities:
                self.initial_neighborhood_priorities.append(neighbor_priority)
            # IF ALL INFORMATION WAS GATHERED AND IM NOT A LOSER THEN TRY TO SING
            if len(self.initial_neighborhood_priorities) == len(self.neighbors):
                self.finished_initialization = True
                if self.status != 'loser':
                    if self.try_to_sing(self.initial_neighborhood_priorities):
                        ch.basic_cancel(method.consumer_tag)
        
        if message_type == 'winner_established':
            # I INCREASE AMOUNT OF WINNERS IN NEIGHBORHOOD AND SET MYSELF TO LOSER
            self.status = 'loser'
            self.number_of_winners_in_neighborhood += 1
            print("[{}] [{}] LOSER, neighbors {}".format(self.index, self.priority, self.neighbors))
            self.broadcast_message_to_neighbors('loser_established')
        
        if message_type == 'winner_finished_singing' and self.status == 'loser':
            # I DECREASE AMOUNT OF WINNERS IN NEIGHBORHOOD, BUT
            # I STILL AM A LOSER BECAUSE I DONT KNOW IF ALL WINNERS HAVE STOPPED SINGING
            self.number_of_winners_in_neighborhood -= 1
            # REMOVE WINNER WHO STOPPED SINGING FROM MY NEIGHBORHOOD
            self.neighbors.remove(neighbor_id)
            self.initial_neighborhood_priorities.remove(neighbor_priority)
            print("[{}] [{}] winner finished singing, neighbors {}".format(self.index, self.priority, self.neighbors))
            # IF I DONT HAVE ANY NEIGHBORS THEN I CAN SING
            if not self.neighbors:
                self.start_singing()
                ch.basic_cancel(method.consumer_tag)
                return
            # IF I STILL HAVE NEIGHBORS, BUT NO WINNER ESTABLISHED THEN I TRY TO SING
            if self.number_of_winners_in_neighborhood == 0:
                self.status = None
                if self.try_to_sing(self.initial_neighborhood_priorities):
                    ch.basic_cancel(method.consumer_tag)
                    return
        
        if message_type == 'loser_established' and self.status != 'loser' and self.finished_initialization:
            # IF I AM NOT A LOSER AND I GOT A MESSAGE FROM A LOSER
            # THEN I TRY TO SING WITHOUT TAKING INTO ACCOUNT THE LOSER(S)
            # FROM MY NEIGHBORHOOD
            print("[{}] [{}], neighbors {} -> got message from loser [{}]".format(
                self.index, self.priority, self.neighbors, neighbor_id
            ))
            self.losers_neighborhood_priorities.append(neighbor_priority)
            relevant_neighborhood = [
                n for n in self.initial_neighborhood_priorities 
                if n not in self.losers_neighborhood_priorities
            ]
            if self.try_to_sing(relevant_neighborhood):
                ch.basic_cancel(method.consumer_tag)
                return

    def try_to_sing(self, relevant_neighborhood):
        # IF MY PRIORITY IS BIGGER THAN ANY OF MY INITIAL NEIGHBORS
        if all([self.priority > neigh_priority for neigh_priority in relevant_neighborhood]):
            print("[{}] [{}] WINNER, neighbors {}".format(self.index, self.priority, self.neighbors))
            # BROADCAST TO ALL NEIGHBORS THAT THEY ARE LOSERS
            self.broadcast_message_to_neighbors('winner_established')
            self.start_singing()
            self.broadcast_message_to_neighbors('winner_finished_singing')
            return True
        else:
            return False

    def start_singing(self):
        print("[{}] [{}] SINGING! la la la ...".format(self.index, self.priority))
        time.sleep(2)
        print("[{}] [{}] BECOMING INACTIVE".format(self.index, self.priority))

    def __str__(self):
        return "Musician idx: {} position: {} priority: {}".format(
            self.index, self.position, self.priority)
