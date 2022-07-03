#!/usr/bin/python3
import time
import serial

print("UART Demonstration Program")
print("NVIDIA Jetson Nano Developer Kit")


ser = serial.Serial(
    port="/dev/ttyTHS1",
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)
# Wait a second to let the port initialize
time.sleep(1)

try:
    if(ser.is_open == False):
        ser.open()
        print("Port open")
     #Send a simple header
    ser.write("Initial Message\r\n".encode())
    #time.sleep(5)
    while(1):
        if ser.is_open == False:
            ser.open()
        print(ser.in_waiting)
        if ser.in_waiting>0:
            data = ser.read(19)
            print(data)
            if data == "donee":
                time.sleep(2)
                ser.write("thank you".encode())
                print("thank you")
                break    
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exiting Program")


finally:
    ser.close()
    pass
