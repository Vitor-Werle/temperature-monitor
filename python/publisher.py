import json
import paho.mqtt.client as mqtt
from serial_reader import get_serial as data

broker = "localhost"
port = 1883
topic = "temperature/sensor"

client = mqtt.Client()
client.connect(broker, port)

try:
    while True:
        client.publish(topic, json.dumps(data))
except KeyboardInterrupt:
    client.disconnect()