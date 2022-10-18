# WORKING

from array import array
from telnetlib import STATUS
from tkinter import *
import struct
from digi.xbee.devices import XBeeDevice
from threading import Thread
import datetime
import time
from pygments import highlight
import math

# Port where local module is connected to.
PORT = "/dev/tty.usbserial-DN03133I"
# Baud rate of local module.
BAUD_RATE = 230400
DATA_TO_SEND = None
CLASS = 0x0
SIZE = 0
REMOTE_NODE_ID = "ROUTER"
# 0013A20041064451 for router
# 0013A20041064456 coordinator

device = XBeeDevice(PORT, BAUD_RATE)
remote_device = None

log = False
win = Tk()
popup = Button()
t_entry = br_entry = s_entry = tm1_entry = tm2_entry = None
manual_mode = 0

exit = False

# Servo motor ranges
raw_rnge_s = [7994, 4032]
rnge_s = raw_rnge_s[1] - raw_rnge_s[0]
neg_ends_s = [4032, 5814]
pos_ends_s = [6214, 7996]
center_s = raw_rnge_s[0] + raw_rnge_s[1] / 2
deadzone_s = [5814, 6214]
neg_rnge_s = neg_ends_s[1] - neg_ends_s[0]
pos_rnge_s = pos_ends_s[1] - pos_ends_s[0]

raw_rnge_b = [4992,7360]
rnge_b = raw_rnge_b[1] - raw_rnge_b[0]
center_b = raw_rnge_b[0] + raw_rnge_b[1] / 2


def init_Xbee():
    global device, remote_device
    try:
        # Obtain the remote XBee device from the XBee network.
        device.open()
        xbee_network = device.get_network()
        remote_device = xbee_network.discover_device(REMOTE_NODE_ID)
        if remote_device is None:
            print("Could not find the remote device")
            exit(1)
    except:
        print("Could not open port to Xbee")

def servo_s_conversion(percentage):
    global neg_rnge_s, pos_rnge_s, neg_ends_s, pos_ends_s
    if percentage < 0:
        return (int) (((percentage+100)/99 * neg_rnge_s) + neg_ends_s[0]) 
    return (int) (((percentage)/101 * pos_rnge_s) + pos_ends_s[0])


def servo_b_conversion(percentage):
    global rnge_b
    return (int)(((percentage+100)/200 * rnge_b) + 4992)

def tm1_conversion(percentage):
    return percentage

def tm2_conversion(percentage):
    return percentage

def send_data(BITS_TO_SEND):
    device.send_data(remote_device, BITS_TO_SEND)

def send_header():
    global CLASS, SIZE
    HEADER = struct.pack('B', (CLASS<<4) + SIZE)
    send_data(HEADER)
    print(HEADER)

def sys_mode(m):
    global DATA_TO_SEND, CLASS, SIZE, manual_mode
    CLASS = 0x0000
    SIZE = 1
    # select mode based on button text
    mode_dict = {
        "Manual Mode": 0,
        "Auto Mode": 1,
        "Control Mode": 2,
        "Rest Mode": 3
    }

    mode_num = mode_dict[m]
    DATA_TO_SEND  = mode_num
    manual_mode = mode_num

    send_header()
    
    BITS_TO_SEND = struct.pack('B', DATA_TO_SEND)
    send_data(BITS_TO_SEND)

    if m in ["Manual Mode", "Control Mode"]:
        CLASS = 0x0001
        SIZE = 4
        send_header()
    

def sys_mode_change(b):
    if "Manual" in b['text']:
        b.configure(text="Auto Mode")
    elif "Auto" in b['text']:
        b.configure(text="Control Mode")
    elif "Control" in b['text']:
        b.configure(text="Resting Mode")
    elif "Rest" in b['text']:
        b.configure(text="Manual Mode")

def sys_mode_and_change(b, t_entry, br_entry, s_entry, tm1_entry, tm2_entry):
    global DATA_TO_SEND, CLASS, SIZE
    CLASS = 0x0000
    SIZE = 1
    
    BITS_TO_SEND = struct.pack('fffff',-10000,-10000,-10000,-10000,-10000)
    send_data(BITS_TO_SEND)
    time.sleep(0.1)
    send_header()

    DATA_TO_SEND = 0b11
    BITS_TO_SEND = struct.pack('B', DATA_TO_SEND)
    send_data(BITS_TO_SEND)

    t_entry.set(0)
    br_entry.set(0)
    s_entry.set(0)
    tm1_entry.set(0)
    tm2_entry.set(0)
    b.configure(text="Resting Mode")
    manual_mode = 3
    
    
def act_comms(AC, t, s, br, tm1, tm2):
    global CLASS, SIZE
    
    CLASS = 0x0001
    SIZE = 4
    t_val = t.get()
    s_val = -s.get()    
    br_val = br.get()
    tm1_val = tm1.get()
    tm2_val = tm2.get()
    
    if manual_mode != 1:
        BITS_TO_SEND = struct.pack('fffff', servo_s_conversion(t_val),
            servo_s_conversion(s_val), servo_b_conversion(br_val),
            tm1_conversion(tm1_val), tm2_conversion(tm2_val))
        send_data(BITS_TO_SEND)
        print(servo_s_conversion(t_val), servo_s_conversion(s_val), 
        servo_b_conversion(br_val), tm1_conversion(tm1_val), tm2_conversion(tm2_val))
    else:
        missing_warning(AC)
        
    
def missing_warning(w):
    popup = Button(w, text = "Enable manual/control mode! Click to remove warning", command=lambda:popup.destroy(), font=("Courier", 18), highlightbackground="orange", bg="orange")
    popup.grid(row=2,column=2)
            
def kill(b):
    global CLASS, SIZE
    CLASS = 0x0002
    SIZE = 0
    send_header()
    
def revive(b):
    global CLASS, SIZE
    CLASS = 0x0003
    SIZE = 0
    send_header()

def logging(b):
    global log, CLASS, SIZE
    SIZE = 0
    if not log:  
        CLASS = 0x0004
        b.configure(text = "Stop Logging", highlightbackground="#0c9e0f")
        log= not log
    elif log:
        CLASS = 0x0005
        b.configure(text = "Log Data", highlightbackground="#4AF924")
        log= not log
    send_header()

def heartbeat(b):
    global CLASS
    CLASS = 0x0006

def cl_comms(b):
    global CLASS
    CLASS = 0x0007

def usr_thread():
    global win, t_entry, tm1_entry, s_entry, br_entry, tm2_entry

    init_Xbee()

    win.geometry("1080x560")
    win.title("DIMA Controller")
    win.configure(highlightbackground="#D3D3D3", bg="#D3D3D3")
    label = Label(win, text = "     DIMA CONTROLLER DASHBOARD", font=("Courier", 50), highlightbackground="#D3D3D3", bg="#D3D3D3")
    label.grid(row=0, columnspan=4)
    
    #create & pack system mode frame
    SM_frame = Frame(win, bg="#ff928b")
    SM_frame.grid(row=2, column=0)
    act_label = Label(win, text = "Select Actuator Configuration", font=("Courier", 22), bg="#ff928b")
    act_label.grid(row=1, column=0, padx=(50,50), pady=(30,0))
    mode_button = Button(SM_frame, height = 3, width = 12, command=lambda:sys_mode_change(mode_button), text="Manual Mode")
    act_ok = Button(SM_frame, height = 2, width = 15, command=lambda:sys_mode(mode_button['text']), text="Apply Mode")
    mode_button.pack(padx=(50,50), pady=(30,20))
    act_ok.pack(pady=(0,30))
    
    #sys_mode(throttle, steering, aux1, aux2)
    
    #create & pack actuator command frame
    AC_frame = Frame(win, height=3, width=20, highlightbackground="#ffac81", bg="#ffac81")
    AC_frame.grid(row=2, column=2)
    act2_label = Label(AC_frame, text = "Select Actuator Level (-100 to 100%)", font=("Courier", 22), bg="#ffac81")
    act2_label.grid(row=0, columnspan=3, padx=(10,10), pady=(5,10))
    AC_frame.columnconfigure(0, weight=1)
    AC_frame.columnconfigure(1, weight=1)
    AC_frame.columnconfigure(2, weight=1)
    AC_frame.rowconfigure(0, weight=1)
    AC_frame.rowconfigure(1, weight=1)
    AC_frame.rowconfigure(2, weight=1)
    AC_frame.rowconfigure(3, weight=1)
    AC_frame.rowconfigure(4, weight=1)
    AC_frame.rowconfigure(5, weight=1)
    AC_frame.rowconfigure(6, weight=1)
    t_label = Label(AC_frame, text = "Throttle Level", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    t_label.grid(row=1, column=0, sticky=W, padx=(100,0))
    s_label = Label(AC_frame, text = "Steering Level", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    s_label.grid(row=2, column=0, sticky=W, padx=(100,0))
    br_label = Label(AC_frame, text = "Break Level", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    br_label.grid(row=3, column=0, sticky=W, padx=(100,0))
    tm1_label = Label(AC_frame, text = "Tail Motor 1 Level", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    tm1_label.grid(row=4, column=0, sticky=W, padx=(100,0))
    tm2_label = Label(AC_frame, text = "Tail Motor 2 Level", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    tm2_label.grid(row=5, column=0, sticky=W, padx=(100,0))
    t_entry = Scale(AC_frame, from_=-100, to=100, orient=HORIZONTAL, length=200, highlightthickness=1, bg="#ffac81")
    t_entry.grid(row=1, column=1)
    s_entry = Scale(AC_frame, from_=-100, to=100, orient=HORIZONTAL, length=200, highlightthickness=1, bg="#ffac81")
    s_entry.grid(row=2, column=1)
    br_entry = Scale(AC_frame, from_=-100, to=100, orient=HORIZONTAL, length=200, highlightthickness=1, bg="#ffac81")
    br_entry.grid(row=3, column=1)
    tm1_entry = Scale(AC_frame, from_=-100, to=100, orient=HORIZONTAL, length=200, highlightthickness=1, bg="#ffac81")
    tm1_entry.grid(row=4, column=1)
    tm2_entry = Scale(AC_frame, from_=-100, to=100, orient=HORIZONTAL, length=200, highlightthickness=1, bg="#ffac81")
    tm2_entry.grid(row=5, column=1)
    # percentage labels for each actuator
    percent1 = Label(AC_frame, text = "%", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    percent1.grid(row=1, column=2, sticky=W)
    percent2 = Label(AC_frame, text = "%", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    percent2.grid(row=2, column=2, sticky=W)
    percent3 = Label(AC_frame, text = "%", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    percent3.grid(row=3, column=2, sticky=W)
    percent4 = Label(AC_frame, text = "%", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    percent4.grid(row=4, column=2, sticky=W)
    percent5 = Label(AC_frame, text = "%", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    percent5 .grid(row=5, column=2, sticky=W)
    act2_ok = Button(AC_frame, height = 2, width = 18, command=lambda:sys_mode_and_change(mode_button, t_entry, br_entry, s_entry, tm1_entry, tm2_entry), text="Safely Enter Rest Mode", highlightbackground="red")
    act2_ok.grid(row=6, column=0, columnspan=3)
    
    STATUS_frame = Frame(win)
    STATUS_frame.grid(row=3, column = 0)
    STATUS_frame.configure(highlightbackground="#D3D3D3", bg="#D3D3D3")
    k = Button(STATUS_frame, height=3, width=12, text="Kill", command=lambda:kill(k), highlightbackground="red")
    k.grid(row=3, column = 0, padx=(0,20), pady=(50,50))
    r = Button(STATUS_frame, height=3, width=12, text="Revive", command=lambda:revive(r), highlightbackground="yellow")
    r.grid(row=3, column = 1, padx=(0,20), pady=(50,50))
    
    l = Button(win, height=3, width=20, text="Log Data", command=lambda:logging(l), highlightbackground="#4AF924")
    l.grid(row=3, column = 2, pady=(50,50))
    h = Button(win, height=3, width=20, text="Heartbeat", command=lambda:heartbeat(h), highlightbackground="#ff928b")
    c = Label(win, height=3, width=20, text="Control Loop Commands")
    
    win.mainloop()
    
def jtsn_thread():
    global exit
    while(not exit):
        #do something
        time.sleep(1)

def slider_thread():
    global t_entry, tm1_entry, s_entry, br_entry, tm2_entry
    t, tm1, s, br, tm2 = 0,0,0,0,0
    while (t_entry == None):
        pass
    while (not exit):
        try:
            if (t_entry.get() != t or tm1_entry.get() != tm1 or s_entry.get() != s or br_entry.get() != br or tm2_entry.get() != tm2):
                t = t_entry.get()
                br = br_entry.get()
                tm1 = tm1_entry.get()
                s = s_entry.get()
                tm2 = tm2_entry.get()
                act_comms(win, t_entry, s_entry, br_entry, tm1_entry, tm2_entry)
            time.sleep(0.1)
        except Exception as e:
            print(e)
            
        
def main():
    global exit
    jtsn = Thread(target=jtsn_thread)
    sldr = Thread(target=slider_thread)
    jtsn.start()
    sldr.start()
    usr_thread()
    exit = True
    sldr.join()
    jtsn.join()
    sys.exit("Safely Closed")
    
if __name__ == "__main__":
    main()