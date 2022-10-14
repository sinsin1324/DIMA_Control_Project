import serial
from time import sleep

ser = serial.Serial('/dev/ttyACM0', 11500)

while True:
    user_input = input("Enter a command: ")
    ser.write(user_input.encode())
    sleep(1)
    print(ser.readline().strip().decode())

