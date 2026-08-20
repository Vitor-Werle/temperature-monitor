import json
import paho.mqtt.client as mqtt
import serial
from serial_reader import get_serial

broker = "localhost"
port = 1883
topic = "temperature/sensor"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(broker, port)

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

try:
    while True:
        data = get_serial(ser)
        if data:
            client.publish(topic, json.dumps(data))
            print("Published:", data)
except KeyboardInterrupt:
    client.disconnect()
    ser.close()