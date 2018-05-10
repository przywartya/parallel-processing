#!/usr/bin/env python
import pika

def callback(ch, method, properties, body):
    print(" [x] %r:%r" % (method.routing_key, body))
    ch.basic_cancel(method.consumer_tag)


def start_listening(idx):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='direct_logs',
                             exchange_type='direct')
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='direct_logs',
                       queue=queue_name,
                       routing_key=str(idx))
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)
    return channel
    # channel.start_consuming()

# start_listening(2)
# print("Finished :)")