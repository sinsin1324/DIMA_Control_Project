from digi.xbee.devices import XBeeDevice

# Port where local module is connected
PORT = "/dev/ttyUSB0"
# Baud rate of local module.
BAUD_RATE = 230400

i = 0


def main():
    print(" +-----------------------------------------+")
    print(" |         XBee Receive Data Sample        |")
    print(" +-----------------------------------------+\n")

    device = XBeeDevice(PORT, BAUD_RATE)
    global i
    i = 0
    try:
        device.open()

        def data_receive_callback(xbee_message):
            print("From %s >> %s" % (xbee_message.remote_device.get_64bit_addr(),
                                     xbee_message.data.decode()))
            global i
            i += 1
            if i > 49:
                print("Success")

        device.add_data_received_callback(data_receive_callback)

        print("Waiting for data...\n")
        input()

    finally:
        if device is not None and device.is_open():
            device.close()


if __name__ == '__main__':
    main()
