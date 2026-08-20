from datetime import datetime
import re
import serial

def get_serial(ser):
    value = ser.readline()
    valueInString = str(value, 'UTF-8').strip()   # .strip() removes \r\n

    temperature = re.findall(r'\d+\.\d+', valueInString)
    if temperature:
        return {
            "temperature": float(temperature[0]),
            "timestamp": datetime.now().isoformat()  # ← now it is a string
        }
    return None   # explicit is better


def main():
    ser = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=1)

    while True:
        data = get_serial(ser)
        if data:
            print(data)


if __name__ == "__main__":
    main()