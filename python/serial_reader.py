from datetime import datetime
import re
import serial

def main():
    ser = serial.Serial(port='/dev/ttyACM0', baudrate=9600)
    get_serial(ser)

def get_serial(ser):
    while True:
        value = ser.readline()
        valueInString = str(value, 'UTF-8')
        temperature = re.findall(r'\d+\.\d+', valueInString)
        if temperature:
            temp = temperature[0]
            data = {
                "temperature": temp,
                "timestamp": datetime.now()
            }
            return data


if __name__ == "__main__":
    main()
