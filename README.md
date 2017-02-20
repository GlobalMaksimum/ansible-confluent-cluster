It is funny to see that majority of the available material on the web on Kafka installation is based on single instance Zookeeper & Kafka Broker installation.
Few Multi-broker guidelines are about installing brokers on the same host with different broker ports.

## What does this installation do ?
* Given that you have 3+ nodes already configured and up (virtual or physical) this installer automatically configures HA Zookeeper and Kafka brokers on servers.
* Deployment is Ansible based
* It is not Apache Kafka but Confluent distro.

## Installation
For basic installation what you need to do is to set `hosts` file (`-i` option) and provide `-l` option to further specify that group of servers, given that your `hosts` file includes more than one group of hosts.

```
ansible-playbook -i environment/digitalocean/hosts -l kafka -u root playbook.yml
```

There a few variables in our configuration which you may want to change:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `create`  | `false` | set to true if creating a new logical volume (do not set extend or resize to true)            |
| `config_lvm`         |  `false`        |   must be set to true in order to execute any tasks in play (failsafe option :)- )           |
| `kafka_user`        |  `kafka`       |             |
| `kafka_group`       | `kafka`        |             |
| `jdk_version`       | `1.8.0`        |             |
| `new_disk`          |  `'/dev/sdb'`       |  set to new disk being added to volume group           |
| `new_mntp`          |   `'/home/kafka'`      | set to the desired mount point to be used as zookeeper and kafka file system             |
| `create_lvname`          |   `'kafka_lv'`      |   set to logical volume name to create          |
| `create_vgname`          |    `'kafka_vg'`     |   set to volume group name to create          |
| `create_lvsize`          |   `'10G'`      |    set to logical volume size to create. Only when `create: true`         |
| `filesystem`          |  `'ext4'`       |   would create new lvm with 10Gigabytes.        |
| `confluent_version`          |  `'2.0.1'`       |   Confluent distro version. Currently `2.0.1` and `3.1.1` supported        |
| `confluent_enterprise`          |  `false`       |   Whether to install Confluent Enterprise or Confluent Open Source        |

`create` and `config_lvm` parameters are usually relevant for large scale production deployments in which you use a separate disk spindle for Kafka and Zookeeper. So you will need a dedicated mount point.

### Confluent Version vs. Kafka Version
Confluent version and Kafka version are obviously two different things. If you have a restriction on Kafka version supported please note the following compatibility matrix:


| Confluent Version | Kafka Version |
|-------------------|---------------|
| `2.0.0`           | `0.9.0.0`     |
| `2.0.1`           | `0.9.0.1`     |
| `3.1.1`           | `0.10.1.0`    |


## Start Zookeeper and Kafka
Start Zookeeper and Kafka with `nohup` on each server.

```
nohup zookeeper-server-start /etc/kafka/zookeeper.properties > zookeeper.log 2>&1 &
```

```
nohup kafka-server-start /etc/kafka/server.properties > kafka.log 2>&1 &
```
## Create a Sample Topic
Create a topic (`topicn`) with `3` partitions (or more) and replication factor of `3`.

```
kafka-topics --create --zookeeper 138.68.108.100:2181,138.68.106.52:2181,138.68.110.33:2181  --topic topicn --replication-factor 3 --partitions 3
```

See that topic partitions are uniformly distributed across available brokers.

```
kafka-topics --describe --zookeeper 138.68.108.100:2181,138.68.106.52:2181,138.68.110.33:2181 --topic topicn
```

```
Topic:topicn	PartitionCount:3	ReplicationFactor:3	Configs:
	Topic: topicn	Partition: 0	Leader: 2	Replicas: 2,0,1	Isr: 0,2,1
	Topic: topicn	Partition: 1	Leader: 0	Replicas: 0,1,2	Isr: 0,2,1
	Topic: topicn	Partition: 2	Leader: 1	Replicas: 1,2,0	Isr: 0,2,1
```

## Produce Messages

Use `kafka-veriable-producer` to generate some messages in topic.

```
kafka-verifiable-producer --broker-list 138.68.108.100:9092,138.68.106.52:9092,138.68.110.33:9092 --topic topicn --max-messages 1000
```

## Consume Messages
It is trivial to come across high-level Kafka consumer clients on the web which may not be suitable for some applications guaranting **exactly once** semantics by using a transactional behaviour at consumer site. Such as, reletional databases.

So we have bundled a simple Python consumer script (based on `pykafka` module).

Ensure that you properly changed following variables in file before you execute it

* `_max_messages_to_consume` is the maximum number of messages you want to consume from the topic. Note that current implementation is a blocking consumer. If the number of messages available in topic is less than `_max_messages_to_consume`, `consumer.consume()` call wil be blocked till you interrupt the client or more messages are available in the topic.
* `_bootstrap_servers` is a comma separated list of Kafka broker `host:port` pairs
* `_topic` is the name of the topic.


```
python simple_python_client.py
```

```
Simple Kafka Consumer
  Bootstrap Servers: 138.68.110.33:9092,138.68.106.52:9092,138.68.108.100:9092
  Topic: b'topicn'
  Maximum Messages: 10

Msg b'0', Partition: 0, Offset: 1
Msg b'3', Partition: 1, Offset: 1
Msg b'6', Partition: 2, Offset: 1
Msg b'9', Partition: 3, Offset: 1
Msg b'12', Partition: 4, Offset: 1
Msg b'15', Partition: 5, Offset: 1
Msg b'18', Partition: 6, Offset: 1
Msg b'21', Partition: 7, Offset: 1
Msg b'24', Partition: 8, Offset: 1
Msg b'27', Partition: 9, Offset: 1
```

## Performance
This is obviously not a detailed kafka performance test and figures are given only to provide a baseline.

Performance values obtained on a 3 node `2GB` digitalocean cluster (`CentOS 6.8`)


### Producer Performance

```
kafka-producer-perf-test --topic topic --num-records 10000000 --record-size 1000 --throughput 10000 --producer-props bootstrap.servers=138.68.110.33:9092,138.68.106.52:9092,138.68.108.100:9092
```

```
49961 records sent, 9988.2 records/sec (9.53 MB/sec), 178.0 ms avg latency, 712.0 max latency.
50094 records sent, 10018.8 records/sec (9.55 MB/sec), 10.5 ms avg latency, 89.0 max latency.
49922 records sent, 9984.4 records/sec (9.52 MB/sec), 13.3 ms avg latency, 409.0 max latency.
50176 records sent, 10033.2 records/sec (9.57 MB/sec), 23.5 ms avg latency, 604.0 max latency.
50046 records sent, 10007.2 records/sec (9.54 MB/sec), 113.4 ms avg latency, 1073.0 max latency.
````

### Consumer Performance

```
kafka-consumer-perf-test --topic topicn  --zookeeper 138.68.110.33:2181,138.68.106.52:2181,138.68.108.100:2181 --messages 1000000
```

```
start.time, end.time, data.consumed.in.MB, MB.sec, data.consumed.in.nMsg, nMsg.sec
2017-02-19 16:14:55:207, 2017-02-19 16:15:06:281, 1129.4211, 101.9885, 1185281, 107032.7795
```
