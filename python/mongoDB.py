from pymongo import MongoClient
import paho.mqtt.client as mqtt
import json

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["temperature-monitor"]
collection = db["sensor_data"]

def on_message_store(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    collection.insert_one(data)
    print("Stored in DB:", data)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", 1883)

client.subscribe("temperature/sensor")
client.on_message = on_message_store

print("Storing incoming data to MongoDB... Press Ctrl+C to stop.")
try:
    client.loop_forever()
    print("Stored")
except KeyboardInterrupt:
    print("Stopped DB subscriber.")
    client.disconnect()