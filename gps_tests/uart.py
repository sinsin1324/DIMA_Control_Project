import serial
from time import sleep

with serial.Serial('/dev/ttyACM0',
                   baudrate=9600, timeout=1) as ser:
    while True:
        line = ser.readline()   # read a '\n' terminated line
        print(line)
        sleep(1)
