import maestro
from time import sleep
servo = maestro.Controller()
target = 0
var = False


def main():
    global servo, target, var
    min_pos = 800*4
    max_pos = 2000*4
    
    print(servo.getMin(0), servo.getMax(0))

    channel = 0
    curr = None
    servo.setAccel(channel, 4)  # set servo 0 acceleration to 4
    servo.setSpeed(channel, 0)  # set speed of servo 0
    curr = servo.getPosition(channel)
    print("debug", curr)
    servo.setTarget(channel, curr+100)
    while True:
        next1 = servo.getPosition(channel)
        if next1 != curr:
            print(next1)
            curr = next1
            servo.setTarget(channel, curr+100)
            sleep(0.1)
            
main()
