# import subprocess
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
# teensy = serial.Serial(TEENSY_PORT, TEENSY_BAUD_RATE)            !!!!!!!!!!!!!!!!!!!

# Maestro Initialisation
servo = maestro.Controller()
target = 0
min_pos = 800*4
max_pos = 2000*4
channel0 = 0
rnge_s = 7996-4032
rnge_b = 7360-4992

i = 0
header = False
CLASS = 0x0000 # Note these are not constants
SIZE = 0 # Read above comment

# Queue Variables
command_q = []
q_pos = -1
q_lock = threading.Lock()

# For Manual Mode
manual_data = 0

# Logging
logging_status = False

selected_mode_handler = None

# Motor Positions
thrust_pos = 0
steer_pos = 0
break_pos = 0
tail1_pos = 0
tail2_pos = 0

# Motor ID; Motor State; Command Position; Command Velocity; Command Kp;
# Command Kd; Command Current; ...(repeat for motor 2); Logbit
# 1;0;0;0;0;0;0;2;0;0;0;0;0;0;0 - Exit Motor Control
# 1;1;0;0;0;0;0;2;1;0;0;0;0;0;0 - Enter Motor Control
# 1;2;0;0;0;0;0;2;2;0;0;0;0;0;0 - Set Origin Position
# 1;3;0;0;3;2;0;2;3;0;0;3;2;0;0 - Simple Impediance Control
# 1;3;1;0;1;0;0;2;3;1;0;1;0;0;0 - Simple Position Control
# 1;3;0;1;0;1;0;2;3;0;1;0;1;0;0 - Simple Velocity Control
EXIT_MOTOR_CONTROL = "1;0;0;0;0;0;0;2;0;0;0;0;0;0;0|"
ENTER_MOTOR_CONTROL = "1;1;0;0;0;0;0;2;1;0;0;0;0;0;0|"
SET_ORIGIN_POSITION = "1;2;0;0;0;0;0;2;2;0;0;0;0;0;0|"

tail_command = [1, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0]

# def init_teensy():                                                !!!!!!!!!!!!!!!!!!!
    # global teensy
    # teensy.write(EXIT_MOTOR_CONTROL)
    # teensy.write(ENTER_MOTOR_CONTROL)
    # teensy.write(SET_ORIGIN_POSITION)

def servo_s_conversion(percentage):
    return ((percentage+100)/200 * rnge_s) + 4032

def servo_b_conversion(percentage):
    return ((percentage+100)/200 * rnge_b) + 4992

# sends two motor positions as a serial message to the teensy       !!!!!!!!!!!!!!!!!!
# def send_to_teensy():
#     global teensy, tail_command
#     msg = ""
#     for c in 13:
#         msg += str(tail_command[c]) + ";"
#     msg += str(tail_command[13]) + "|"
#     teensy.write(msg)

def data_receive_callback(xbee_message):
    global header, CLASS, SIZE, manual_data
    var = None
    message = xbee_message.data
    if not header:
        var = struct.unpack('B', message)
        CLASS = var[0] >> 4
        SIZE = var[0] & 0x0F
        header=True
        if SIZE == 0:
            if CLASS == 0x2:
                q_lock.acquire()
                command_q.append([CLASS, 'k'])
                q_lock.release()
                print("Robot Killed")
            elif CLASS == 0X3:
                q_lock.acquire()
                command_q.append([CLASS, 'r'])
                q_lock.release()
                print("Robot Revived")
            elif CLASS == 0X4:
                q_lock.acquire()
                command_q.append([CLASS, 'l'])
                q_lock.release()
                print("Logging Enabled")
            elif CLASS == 0X5:
                q_lock.acquire()
                command_q.append([CLASS, 'n'])
                q_lock.release()
                print("Logging Disabled")
            header=False
    else:
        if CLASS == 0x0:
            var = struct.unpack('B', message)
            q_lock.acquire()
            command_q.append([CLASS, var[0]])
            q_lock.release()
            header=False
            print(bin(var[0]))
        elif CLASS == 0x1:
            var = struct.unpack('fffff', message)
            if (var[0] != -10000):
                selected_mode_handler(var)
            else:
                header = False

# Command Handler
def manual_control(data):
    global servo, target, steer_pos, \
    thrust_pos, break_pos, tail1_pos, tail2_pos
    data = list(int (x) for x in data)
    servos = [data[0], data[1], data[2]]
    for x in range(3):
        servo.setTarget(channel0+x, servos[x])
    tail_command[2] = data[3]
    tail_command[9] = data[4]
    # send_to_teensy()                                              !!!!!!!!!!!!!!!!!!!
    steer_pos, thrust_pos, break_pos, tail1_pos, tail2_pos = data
    print(data)
    
# Read control commands from file and execute them accordingly    
def auto_control():
    global servo, target, steer_pos, \
    thrust_pos, break_pos, tail1_pos, tail2_pos
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
        # 0x5: toggle logging
        
        servos = [data[0], data[1], data[2]]

        for x in range(3):
            servo.setTarget(channel0+x, servos[x])
        tail_command[2] = data[3]
        tail_command[9] = data[4]
        # send_to_teensy()                                     !!!!!!!!!!!!!!!!!!!
        time.sleep(0.1)
    
    

def control_loop_control(data):
    global servo, target, steer_pos, \
    thrust_pos, break_pos, tail1_pos, tail2_pos

    data = list(data)
    servos = [data[0], data[1], data[2]]
    for x in range(3):
        servo.setTarget(channel0+x, servos[x])
    
    steer_pos, thrust_pos, break_pos, tail1_pos, tail2_pos = data
    print(data)
    
def rest_control(placeholder):
    global servo, target, steer_pos, \
    thrust_pos, break_pos, tail1_pos, tail2_pos
    data = [0,0,0,0,0]
    for x in range(3):
        servo.setSpeed(channel0+x, 5)
    for x in range(3):
        servo.setTarget(channel0+x, data[x])
    tail_command[2] = data[3]
    tail_command[9] = data[4]
    # send_to_teensy()                                          !!!!!!!!!!!!!!!!!!!
    time.sleep(2)
    for x in range(3):
        servo.setSpeed(channel0+x, 0)
    steer_pos, thrust_pos, break_pos, tail1_pos, tail2_pos = data
    
        
def kill():
    pass

def revive():
    pass

def get_tail_data():
    #Decode tail data from teensy serial data
    return ""

def logger_thread():
    global logging_status, steer_pos, \
    thrust_pos, break_pos, tail1_pos, tail2_pos
    log_frequency = 20
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile = open("../data/logs/" + current_datetime + ".csv", "w")
    while logging_status:
        # get linux cpu temperature
        # cpu_temp = subprocess.check_output(
        #     "cat /sys/class/thermal/thermal_zone0/temp", shell=True)
        logfile.write(datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + ",")
        for y in range(log_frequency):
            logfile.write(str(steer_pos) + "," + str(thrust_pos) + "," + 
            str(break_pos) + "," + str(tail1_pos) + "," + str(tail2_pos))
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
    global channel0, servo, xbee_device # , teensy                  !!!!!!!!!!!!!!!!!!!
    print(" +-----------------------------------------+")
    print(" |        Jetson Receive Data Sample       |")
    print(" +-----------------------------------------+\n")
    
    # Initialise servo variables
    servo.setAccel(channel0, 4)  # set servo 0 acceleration to 4
    servo.setSpeed(channel0, 0)  # set speed of servo 0

    # Initialise tail motors
    # init_teensy()                                                 !!!!!!!!!!!!!!!!!!!

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
        # teensy.close()                                            !!!!!!!!!!!!!!!!!!!
        servo.close()
        print("\nSafely closed")

if __name__ == '__main__':
    main()
