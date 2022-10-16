import serial
from time import sleep

# Motor ID; Motor State; Command Position; Command Velocity; Command Kp;
# Command Kd; Command Current; ...(repeat for motor 2); Logbit

# 1;0;0;0;0;0;0;2;0;0;0;0;0;0;0 - Exit Motor Control
# 1;1;0;0;0;0;0;2;1;0;0;0;0;0;0 - Enter Motor Control
# 1;2;0;0;0;0;0;2;2;0;0;0;0;0;0 - Set Origin Position
# 1;3;0;0;3;2;0;2;3;0;0;3;2;0;0 - Simple Impediance Control
# 1;3;1;0;1;0;0;2;3;1;0;1;0;0;0 - Simple Position Control
# 1;3;0;1;0;1;0;2;3;0;1;0;1;0;0 - Simple Velocity Control

# ser = serial.Serial('/dev/ttyACM0', 115200)
ser = serial.Serial('/dev/cu.usbmodem96755701', 115200)

while True:
    user_input = input("Enter a command: ")
    ser.write(user_input.encode())
    print(ser.readline().strip().decode())
    
