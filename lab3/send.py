#!/usr/bin/env python
import pika


def send_to(idx, message="Hello World!"):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='direct_logs',
                             exchange_type='direct')
    channel.basic_publish(exchange='direct_logs',
                          routing_key=str(idx),
                          body=message)
    # print(" [x] Sent %r:%r" % (idx, message))
    connection.close()

# send_to(2)