import re
from datetime import datetime, timezone


def get_serial(ser):
    value = ser.readline()
    if not value:
        return None

    value_in_string = str(value, "UTF-8").strip()
    temperature_match = re.search(r"-?\d+(?:\.\d+)?", value_in_string)

    if not temperature_match:
        return None

    temperature = float(temperature_match.group(0))
    if not -50.0 <= temperature <= 100.0:
        return None

    return {
        "temperature": temperature,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    import serial

    ser = serial.Serial(port="/dev/ttyACM0", baudrate=9600, timeout=1)

    try:
        while True:
            data = get_serial(ser)
            if data:
                print(data)
    except KeyboardInterrupt:
        print("Stopped serial reader.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()