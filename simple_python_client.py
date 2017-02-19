"""Simple Kafka consumer in python.

Orginal code in  http://activisiongamescience.github.io/2016/06/15/Kafka-Client-Benchmarking/
"""

from __future__ import print_function
from pykafka import KafkaClient

# Modify those parameters based on your needs.
_max_messages_to_consume = 1200
_bootstrap_servers = '138.68.110.33:9092,138.68.106.52:9092,138.68.108.100:9092'
_topic = b'topicn'

client = KafkaClient(hosts=_bootstrap_servers)
topic = client.topics[_topic]
consumer = topic.get_simple_consumer(use_rdkafka=False)

print("Simple Kafka Consumer")
print("  Bootstrap Servers: {}".format(_bootstrap_servers))
print("  Topic: {}".format(_topic))
print("  Maximum Messages: {}".format(_max_messages_to_consume))
print()

msg_consumed_count = 0
while True:
    msg = consumer.consume()

    if msg:
        msg_consumed_count += 1

        print ("Msg {}, Partition: {}, Offset: {}".format(
            msg.value,  msg.partition_id, msg.offset))

    if msg_consumed_count >= _max_messages_to_consume:
        break
