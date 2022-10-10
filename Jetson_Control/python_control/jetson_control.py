from digi.xbee.devices import XBeeDevice
import time
import struct
import threading
import maestro

# Port where local module is connected
# PORT = "/dev/ttyUSB0"
PORT = "/dev/ttyUSB0"
# Baud rate of local module.
BAUD_RATE = 230400

# Maestro Initialisation
servo = maestro.Controller()
target = 0
min_pos = 800*4
max_pos = 2000*4
channel = 0
rnge_s = 7996-4032
rnge_b = 7360-4992

i = 0
header = False
CLASS = 0x0000
SIZE = 0
command_q = []
q_pos = -1
q_lock = threading.Lock()
manual_data = 0
selected_mode_handler = None

def servo_s_conversion(percentage):
    return ((percentage+100)/200 * rnge_s) + 4032

def servo_b_conversion(percentage):
    return ((percentage+100)/200 * rnge_b) + 4992

def data_receive_callback(xbee_message):
    global header, CLASS, SIZE, manual_data
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
            var = struct.unpack('fffff', message)
            if (var[0] == -200):
                header=False
            else:
                # q_lock.acquire()
                # command_q.append([CLASS, var])
                # q_lock.release()
                manual_data = var
                selected_mode_handler(manual_data)

# Command Handler
def manual_control(data):
    global servo, target, rnge_s, rnge_b
    print(data)
    data = list(data)
    for x in range(2):
        data[x] = servo_s_conversion(data[x])
    data[2] = servo_b_conversion(data[2])

    steering, thrust, brk, tail1, tail2 = [int(x) for x in data]
    servos = [steering, thrust, brk]
    for x in range(3):
        servo.setTarget(channel+x, servos[x])

def auto_control(data):
    pass

def control_loop_control(data):
    pass

def rest_control(placeholder):
    global servo, target, rnge_s, rnge_b
    data = [0,0,0,0,0]
    for x in range(2):
        data[x] = servo_s_conversion(data[x])
    data[2] = servo_b_conversion(data[2])
    
    steering, thrust, brk, tail1, tail2 = [int(x) for x in data]
    for x in range(3):
        servo.setSpeed(channel+x, 5)
    servos = [steering, thrust, brk]
    for x in range(3):
        servo.setTarget(channel+x, servos[x])
    time.sleep(4)
    for x in range(3):
        print("Servo " + str(x) + " at " + str(servo.getPosition(channel+x)))
        servo.setSpeed(channel+x, 0)
        
def kill():
    pass

def revive():
    pass

def toggle_logging():
    pass

def operating_mode(data):
    global selected_mode_handler
    mode_map = {
        0x0: manual_control,
        0x1: auto_control,
        0x2: control_loop_control,
        0x3: rest_control
    }
    selected_mode_handler = mode_map[data]
    if data in [1, 3]:
        selected_mode_handler(data)

class_dict = {0x0:operating_mode}

def main():
    global channel, servo
    print(" +-----------------------------------------+")
    print(" |         XBee Receive Data Sample        |")
    print(" +-----------------------------------------+\n")

    # initialise servo
    device = XBeeDevice(PORT, BAUD_RATE)
    servo.setAccel(channel, 4)  # set servo 0 acceleration to 4
    servo.setSpeed(channel, 0)  # set speed of servo 0

    try:
        device.open()
        device.add_data_received_callback(data_receive_callback)
        while (True):
            if (len(command_q) > 0):
                # changed command_q[-1][0] to [0][0] NB
                print("Class: " + str(command_q[0][0]))
                print(command_q[0][1])
                cls, data = command_q.pop(0)
                class_dict[cls](data)

    finally:
        if device is not None and device.is_open():
            device.close()


if __name__ == '__main__':
    main()
