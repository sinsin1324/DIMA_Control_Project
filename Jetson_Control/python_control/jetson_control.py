import subprocess
from digi.xbee.devices import XBeeDevice
import time
import struct
import threading
from threading import Thread
import maestro
import serial
from datetime import datetime
# from pyspectator.temperature_reader import TemperatureReader

# Ports
XBEE_PORT = "/dev/ttyUSB0"
TEENSY_PORT = "/dev/ttyACM0"

# Baud Rates
XBEE_BAUD_RATE = 230400
TEENSY_BAUD_RATE = 115200

# Initialize XBee and Teensy
xbee_device = XBeeDevice(XBEE_PORT, XBEE_BAUD_RATE)
#teensy = serial.Serial(TEENSY_PORT, TEENSY_BAUD_RATE, timeout=1)

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
logging_status = False
selected_mode_handler = None


def servo_s_conversion(percentage):
    return ((percentage+100)/200 * rnge_s) + 4032

def servo_b_conversion(percentage):
    return ((percentage+100)/200 * rnge_b) + 4992

# sends two motor positions as a serial message to the teensy
def send_serial(tail1, tail2):
    global teensy
    #write to teensy
    

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
    send_serial(tail1, tail2)
    
# Read control commands from file and execute them accordingly    
def auto_control():
    global servo, target, rnge_s, rnge_b
    with open("../data/commands.txt") as f:
        lines = f.readlines()
    for line in lines:
        data = line.split(",")
        header = data[0]
        # header table
        # 0x0: set motor position with [motor_id, position]
        # 0x1: set motor speed with [motor_id, speed]
        # 0x2: sleep for [time] seconds
        # 0x3: kill robot
        # 0x4: revive robot
        # 0x5: toggle logging#
            
        for x in range(2):
            data[x] = servo_s_conversion(data[x])
        data[2] = servo_b_conversion(data[2])
        
        steering, thrust, brk, tail1, tail2  = [int(x) for x in data]
        servos = [steering, thrust, brk]
        for x in range(3):
            servo.setTarget(channel+x, servos[x])
        send_serial(tail1, tail2)
        time.sleep(0.1)
    
    

def control_loop_control(data):
    global servo, target, rnge_s, rnge_b
    print(data)
    data = list(data)
    for x in range(2):
        data[x] = servo_s_conversion(data[x])
    data[2] = servo_b_conversion(data[2])
    
    steering, thrust, brk = [int(x) for x in data[:3]]
    servos = [steering, thrust, brk]
    for x in range(3):
        servo.setTarget(channel+x, servos[x])
    
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

def get_tail_data():
    #Decode tail data from teensy serial data
    return ""

def logger_thread():
    global logging_status
    log_frequency = 15
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile = open("../data/logs/" + current_datetime + ".csv", "w")
    while logging_status:
        # get linux cpu temperature
        cpu_temp = subprocess.check_output(
            "cat /sys/class/thermal/thermal_zone0/temp", shell=True)
        logfile.write(datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + ",")
        for y in range(log_frequency):
            for x in range(3):
                logfile.write(str(servo.getPosition(channel+x)) + ",")
            logfile.write(get_tail_data() + "\n")
    logfile.close()

def toggle_logging(placeholder):
    global logging_status
    if not logging_status:
        logging_status = True
        logger = Thread(target=logger_thread)
        logger.start()
    else:
        logging_status = False

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

class_dict = {0x0:operating_mode,
              0x4:toggle_logging,
              0x5:toggle_logging,}

def main():
    global channel, servo, xbee_device
    print(" +-----------------------------------------+")
    print(" |        Jetson Receive Data Sample       |")
    print(" +-----------------------------------------+\n")

    # Enter teensy motor control mode
    # teensy.write(b'c')
    
    # Initialise servo variables
    servo.setAccel(channel, 4)  # set servo 0 acceleration to 4
    servo.setSpeed(channel, 0)  # set speed of servo 0

    try:
        xbee_device.open()
        xbee_device.add_data_received_callback(data_receive_callback)
        while (True):
            if (len(command_q) > 0):
                # changed command_q[-1][0] to [0][0] NB
                print("Class: " + str(command_q[0][0]))
                print(command_q[0][1])
                cls, data = command_q.pop(0)
                class_dict[cls](data)

    finally:
        if xbee_device is not None and xbee_device.is_open():
            xbee_device.close()
        # exit teensy motor control mode
        # teensy.write(b'e')
        teensy.close()
        servo.close()
        print("\nSafely closed")

if __name__ == '__main__':
    main()
