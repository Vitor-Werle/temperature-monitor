import json
import os
import signal
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import serial

from serial_reader import get_serial

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "temperature/sensor")
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyACM0")
DEVICE_ID = os.getenv("DEVICE_ID", "sensor-01")
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
USE_TLS = os.getenv("MQTT_TLS", "false").lower() in {"1", "true", "yes"}
MQTT_CA_CERT = os.getenv("MQTT_CA_CERT", "/etc/ssl/certs/ca-certificates.crt")

client = None
ser = None


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("Connected to MQTT broker.")
    else:
        print(f"MQTT connection failed with code {reason_code}.")


def connect_mqtt():
    global client

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"publisher-{DEVICE_ID}")

    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    if USE_TLS:
        client.tls_set(ca_certs=MQTT_CA_CERT)

    client.on_connect = on_connect
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()


def connect_serial():
    global ser
    ser = serial.Serial(SERIAL_PORT, 9600, timeout=1)
    time.sleep(1)


def shutdown(signum, frame):
    raise KeyboardInterrupt


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


try:
    connect_mqtt()
    connect_serial()

    while True:
        try:
            data = get_serial(ser)
            if data:
                payload = {
                    "device_id": DEVICE_ID,
                    "temperature": data["temperature"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                result = client.publish(TOPIC, json.dumps(payload), qos=1)
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    print(f"Publish failed with error code: {result.rc}")
                else:
                    print("Published:", payload)
        except serial.SerialException as exc:
            print(f"Serial error: {exc}. Reconnecting...")
            time.sleep(2)
            try:
                if ser is not None and ser.is_open:
                    ser.close()
                connect_serial()
            except serial.SerialException as retry_exc:
                print(f"Serial reconnect failed: {retry_exc}")
                time.sleep(5)
        except Exception as exc:
            print(f"Unexpected error: {exc}")
            time.sleep(1)

except KeyboardInterrupt:
    print("Shutting down publisher.")
finally:
    if client is not None:
        client.loop_stop()
        client.disconnect()
    if ser is not None and ser.is_open:
        ser.close()