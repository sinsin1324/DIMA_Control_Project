import time
import serial

ser = serial.Serial('/dev/hidraw1', 115200, timeout=0.050)
ser.write('1;0;0;0;0;0;0;2;0;0;0;0;0;0')
ser.write('1;1;0;0;0;0;0;2;1;0;0;0;0;0')
ser.close()
