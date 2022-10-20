import serial
from time import sleep

with serial.Serial('/dev/gps2', baudrate=9600, timeout=1) as ser:
    while True:
        sleep(0.1)

        line = ser.readline()   # read a '\n' terminated line
        print(line)
        line = line.decode()
        while 'GNVTG' not in line:
            pass

        line = line.split(',')

        print(line[6])
        print(line[8])

