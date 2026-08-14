import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print("Received:", data)


client = mqtt.Client()
client.connect("localhost", 1883)

client.subscribe("temperature/sensor")
client.on_message = on_message

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()