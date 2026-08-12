import csv
from datetime import datetime
import re
import serial

ser = serial.Serial(port='/dev/ttyACM0', baudrate=9600)

with open('data.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['temperature', 'date'])
    while True:
        value = ser.readline()
        valueInString = str(value, 'UTF-8')
        temperature = re.findall(r'\d+\.\d+', valueInString)
        if temperature:
            temp = temperature[0]
            writer.writerow([temp, datetime.now()])
            print(f"temperature: {temp} | date: {datetime.now()}")