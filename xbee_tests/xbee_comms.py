from digi.xbee.devices import XBeeDevice
import time
import sys
import struct
# Port where local module is connected
PORT = "/dev/ttyUSB0"
# Baud rate of local module.
BAUD_RATE = 230400

i = 0
header = False
CLASS = 0x0000
SIZE = 0

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
                        header=False
                    elif CLASS == 0X0003:
                        print("Robot Revived")
                        header=False
                    elif CLASS == 0X0004:
                        print("Logging Enabled")
                        header=False
                    elif CLASS == 0X0005:
                        print("Logging Disabled")
                        header=False
            else:
                if CLASS == 0x0000:
                    var = struct.unpack('B', message)
                    print(bin(var[0]))
                    header=False
                elif CLASS == 0x0001:
                    for x in var:
                        print(float(x))
                    header=False

def main():
    print(" +-----------------------------------------+")
    print(" |         XBee Receive Data Sample        |")
    print(" +-----------------------------------------+\n")

    device = XBeeDevice(PORT, BAUD_RATE)
    try:
        device.open()

        device.add_data_received_callback(data_receive_callback)
        print("Waiting for data...\n")
        input()
    finally:
        if device is not None and device.is_open():
            device.close()


if __name__ == '__main__':
    main()
