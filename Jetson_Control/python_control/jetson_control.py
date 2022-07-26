from click import command
from digi.xbee.devices import XBeeDevice
import time
import sys
import struct
import threading

# Port where local module is connected
# PORT = "/dev/ttyUSB0"
PORT = "/dev/tty.usbserial-DN02SSJ0"
# Baud rate of local module.
BAUD_RATE = 230400

i = 0
header = False
CLASS = 0x0000
SIZE = 0
command_q = []
curr_command = []
q_pos = -1
q_lock = threading.Lock()
curr_lock = threading.Lock()

def data_receive_callback(xbee_message):
            global header, CLASS, SIZE
            var = None
            message = xbee_message.data
            if not header:
                var = struct.unpack('HH', message)
                CLASS = var[0]
                SIZE = var[1]
                header=True
                if SIZE == 0:
                    if CLASS == 0x0002:
                        print("Robot Killed")
                        q_lock.acquire()
                        command_q.append([CLASS, 'k'])
                        q_lock.release()
                    elif CLASS == 0X0003:
                        print("Robot Revived")
                        q_lock.acquire()
                        command_q.append([CLASS, 'r'])
                        q_lock.release()
                    elif CLASS == 0X0004:
                        print("Logging Enabled")
                        q_lock.acquire()
                        command_q.append([CLASS, 'l'])
                        q_lock.release()
                    elif CLASS == 0X0005:
                        print("Logging Disabled")
                        q_lock.acquire()
                        command_q.append([CLASS, 'n'])
                        q_lock.release()
                    header=False
            else:
                if CLASS == 0x0000:
                    var = struct.unpack('B', message)
                    print(bin(var[0]))
                    q_lock.acquire()
                    command_q.append([CLASS, var[0]])
                    q_lock.release()
                    header=False
                elif CLASS == 0x0001:
                    var = struct.unpack('ffff', message)
                    if (var[0] == -200):
                        header=False
                    else:
                        q_lock.acquire()
                        command_q.append([CLASS, var])
                        q_lock.release()
                

def main():
    print(" +-----------------------------------------+")
    print(" |         XBee Receive Data Sample        |")
    print(" +-----------------------------------------+\n")

    device = XBeeDevice(PORT, BAUD_RATE)
    try:
        device.open()
        l = 0
        device.add_data_received_callback(data_receive_callback)
        while (True):
            if (len(command_q) > l):
                l+=1
                print("Class: " + str(command_q[-1][0]))
                print(command_q[-1][1])
    finally:
        if device is not None and device.is_open():
            device.close()


if __name__ == '__main__':
    main()
