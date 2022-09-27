# WORKING

from array import array
from telnetlib import STATUS
from tkinter import *
import struct
from digi.xbee.devices import XBeeDevice
from threading import Thread
import datetime
import time

from numpy import s_
from pygments import highlight

# Port where local module is connected to.
PORT = "/dev/tty.usbserial-DN03133I"
# Baud rate of local module.
BAUD_RATE = 230400
DATA_TO_SEND = None
CLASS = 0x0000
SIZE = 0
REMOTE_NODE_ID = "ROUTER"
#0013A20041064451 for router
#0013A20041064456 coordinator

device = XBeeDevice(PORT, BAUD_RATE)
remote_device = None

log = False
win = Tk()
popup = Button()
t_entry = tv_entry = s_entry = a_entry = None
manual_mode = False

# Boolean set true to safely end program
exit = False

def array_to_bin(bit_arr):
    binval = 0b0
    i = len(bit_arr)-1
    for bit in bit_arr:
        binval += bit<<(i)
        i-=1
    return binval

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

def send_data(BITS_TO_SEND):
    device.send_data(remote_device, BITS_TO_SEND)

def send_header():
    global CLASS, SIZE
    HEADER = struct.pack('HH', CLASS, SIZE)
    send_data(HEADER)
    print(HEADER)

def sys_mode(t, s, a1, a2):
    global DATA_TO_SEND, CLASS, SIZE, manual_mode
    CLASS = 0x0000
    SIZE = 1
    DATA_TO_SEND = [0b0,0b0,0b0,0b0,0b0,0b0,0b0,0b0]
    buttons = [a2,a1,s,t]
    i=0
    extra_header = False
    for button in buttons:
        if "Manual" in button['text']:
            extra_header = True
        elif "Auto" in button['text']:
            DATA_TO_SEND[i+1] = 0b1
        elif "Control" in button['text']:
            DATA_TO_SEND[i] = 0b1
        else:
            print("Unknown Button Value")
        i+=2
    send_header()
    BITS_TO_SEND = struct.pack('B', array_to_bin(DATA_TO_SEND))
    send_data(BITS_TO_SEND)
    if extra_header:
        manual_mode = True
        CLASS = 0x0001
        SIZE = 4
        send_header()
    else:
        manual_mode = False
    

def sys_mode_change(b):
    if b['text'] == "Throttle Manual":
        b.configure(text="Throttle Auto")
    elif b['text'] == "Throttle Auto":
        b.configure(text="Throttle Control")
    elif b['text'] == "Throttle Control":
        b.configure(text="Throttle Manual")
    
    if b['text'] == "Steering Manual":
        b.configure(text="Steering Auto")
    elif b['text'] == "Steering Auto":
        b.configure(text="Steering Control")
    elif b['text'] == "Steering Control":
        b.configure(text="Steering Manual")

    if b['text'] == "Aux1 Manual":
        b.configure(text="Aux1 Auto")
    elif b['text'] == "Aux1 Auto":
        b.configure(text="Aux1 Control")
    elif b['text'] == "Aux1 Control":
        b.configure(text="Aux1 Manual")

    if b['text'] == "Aux2 Manual":
        b.configure(text="Aux2 Auto")
    elif b['text'] == "Aux2 Auto":
        b.configure(text="Aux2 Control")
    elif b['text'] == "Aux2 Control":
        b.configure(text="Aux2 Manual")

def sys_mode_and_change(t,s,a1,a2):
    global DATA_TO_SEND, CLASS, SIZE
    CLASS = 0x0000
    SIZE = 1
    
    BITS_TO_SEND = struct.pack('ffff', -200,-200,-200,-200)
    send_data(BITS_TO_SEND)
    
    buttons = [t,s,a1,a2]
    for b in buttons:
        if (b['text'] in ["Throttle Manual", "Throttle Control"]):
            b.configure(text="Throttle Auto")
        if (b['text'] in ["Steering Manual", "Steering Control"]):
            b.configure(text="Steering Auto")
        if (b['text'] in ["Aux1 Manual", "Aux1 Control"]):
            b.configure(text="Aux1 Auto")
        if (b['text'] in ["Aux2 Manual", "Aux2 Control"]):
            b.configure(text="Aux2 Auto")
    DATA_TO_SEND = [0b0,0b1,0b0,0b1,0b0,0b1,0b0,0b1]
    
    send_header()
    BITS_TO_SEND = struct.pack('B', array_to_bin(DATA_TO_SEND))
    send_data(BITS_TO_SEND)
    
    
def act_comms(AC, t, s, tv, a):
    global CLASS, SIZE, t_entry, a_entry, s_entry, tv_entry
    
    CLASS = 0x0001
    SIZE = 4
    
    if (float(t.get())>100 or float(s.get())>100 or float(tv.get())>100 or float(a.get())>100 or float(t.get())<-100 or float(s.get())<-100 or float(tv.get())<-100 or float(a.get())<-100):
        popup = Button(AC, text = "Bounds: -100% to 100%. Click to remove warning", command=lambda:popup.destroy(), font=("Courier", 18), highlightbackground="orange", bg="orange")
        popup.grid(row=2,column=2)
    else:
        if manual_mode:
            BITS_TO_SEND = struct.pack('ffff', float(t.get()), float(s.get()), float(tv.get()), float(a.get()))
            send_data(BITS_TO_SEND)
        else:
            missing_warning(AC)
        
    
def missing_warning(w):
    popup = Button(w, text = "Enable manual mode! Click to remove warning", command=lambda:popup.destroy(), font=("Courier", 18), highlightbackground="orange", bg="orange")
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
    global win, t_entry, a_entry, s_entry, tv_entry

    init_Xbee()

    win.geometry("1080x720")
    win.title("DIMA Controller")
    win.configure(highlightbackground="#D3D3D3", bg="#D3D3D3")
    label = Label(win, text = "     DIMA CONTROLLER DASHBOARD", font=("Courier", 50), highlightbackground="#D3D3D3", bg="#D3D3D3")
    label.grid(row=0, columnspan=4)
    
    #create & pack system mode frame
    SM_frame = Frame(win, bg="#ff928b")
    SM_frame.grid(row=2, column=0)
    act_label = Label(win, text = "Select Actuator Configuration", font=("Courier", 22), bg="#ff928b")
    act_label.grid(row=1, column=0, padx=(50,50), pady=(20,0))
    throttle = Button(SM_frame, height = 2, width = 15, command=lambda:sys_mode_change(throttle), text="Throttle Manual")
    steering = Button(SM_frame, height = 2, width = 15, command=lambda:sys_mode_change(steering), text="Steering Manual")
    aux1 = Button(SM_frame, height = 2, width = 15, command=lambda:sys_mode_change(aux1), text="Aux1 Manual")
    aux2 = Button(SM_frame, height = 2, width = 15, command=lambda:sys_mode_change(aux2), text="Aux2 Manual")
    act_ok = Button(SM_frame, height = 2, width = 12, command=lambda:sys_mode(throttle, steering, aux1, aux2), text="Send Command")
    throttle.pack(padx=(54,200), pady=(5,0))
    steering.pack(padx=(200,54), pady=(5,0))
    aux1.pack(padx=(54,200), pady=(5,0))
    aux2.pack(padx=(200,54), pady=(5,0))
    act_ok.pack(pady=(5,5))
    
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
    t_label = Label(AC_frame, text = "Throttle Level", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    t_label.grid(row=1, column=0, sticky=W, padx=(100,0))
    s_label = Label(AC_frame, text = "Steering Level", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    s_label.grid(row=2, column=0, sticky=W, padx=(100,0))
    tv_label = Label(AC_frame, text = "Tail Velocity Level", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    tv_label.grid(row=3, column=0, sticky=W, padx=(100,0))
    a_label = Label(AC_frame, text = "Aux2 Level", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    a_label.grid(row=4, column=0, sticky=W, padx=(100,0))
    #t_entry = Entry(AC_frame, width=4, highlightthickness=1)
    t_entry = Scale(AC_frame, from_=-100, to=100, orient=HORIZONTAL, length=200, highlightthickness=1, bg="#ffac81")
    t_entry.grid(row=1, column=1)
    #s_entry = Entry(AC_frame, width=4, highlightthickness=1)
    s_entry = Scale(AC_frame, from_=-100, to=100, orient=HORIZONTAL, length=200, highlightthickness=1, bg="#ffac81")
    s_entry.grid(row=2, column=1)
    #tv_entry = Entry(AC_frame, width=4, highlightthickness=1)
    tv_entry = Scale(AC_frame, from_=-100, to=100, orient=HORIZONTAL, length=200, highlightthickness=1, bg="#ffac81")
    tv_entry.grid(row=3, column=1)
    #a_entry = Entry(AC_frame, width=4, highlightthickness=1)
    a_entry = Scale(AC_frame, from_=-100, to=100, orient=HORIZONTAL, length=200, highlightthickness=1, bg="#ffac81")
    a_entry.grid(row=4, column=1)
    percent1 = Label(AC_frame, text = "%", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    percent1.grid(row=1, column=2, sticky=W)
    percent2 = Label(AC_frame, text = "%", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    percent2.grid(row=2, column=2, sticky=W)
    percent3 = Label(AC_frame, text = "%", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    percent3.grid(row=3, column=2, sticky=W)
    percent4 = Label(AC_frame, text = "%", font=("Courier", 18), highlightbackground="#ffac81", bg="#ffac81")
    percent4.grid(row=4, column=2, sticky=W)
    act2_ok = Button(AC_frame, height = 2, width = 18, command=lambda:sys_mode_and_change(throttle, steering, aux1, aux2), text="Disable Manual Control", highlightbackground="red")
    act2_ok.grid(row=5, column=0, columnspan=3)
    
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
    global t_entry, a_entry, s_entry, tv_entry
    t, a, s, tv = 0,0,0,0
    while (t_entry == None):
        pass
    while (not exit):
        if (t_entry.get() != t or a_entry.get() != a or s_entry.get() != s or tv_entry.get() != tv):
            t = t_entry.get()
            tv = tv_entry.get()
            a = a_entry.get()
            s = s_entry.get()
            act_comms(win, t_entry, s_entry, tv_entry, a_entry)
        time.sleep(0.5)
        
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