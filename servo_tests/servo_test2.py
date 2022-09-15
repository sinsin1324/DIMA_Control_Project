from threading import Thread
import maestro
import time

servo = maestro.Controller()
target = 0
def main():
	global servo, target
	min_pos = 800*4
	max_pos = 2000*4
	channel = 0

	servo.setAccel(channel,4)      #set servo 0 acceleration to 4
	servo.setTarget(channel,6000)  #set servo to move to center position
	servo.setSpeed(channel,0)     #set speed of servo 0
	x = servo.getPosition(channel+1) #get the current position of servo
	servo.setAccel(channel+1,4)      #set servo 1 acceleration to 4
	servo.setTarget(channel+1,6000)  #set servo to move to center position
	servo.setSpeed(channel+1,0)     #set speed of servo 1
	servo.setAccel(channel+2,4)      #set servo 2 acceleration to 4
	servo.setTarget(channel+2,6000)  #set servo to move to center position
	servo.setSpeed(channel+2,0)     #set speed of servo 2
	x = servo.getPosition(channel+1) #get the current position of servo 1
	print(x)
	if x < min_pos+((max_pos - min_pos)/2): # if less than
	        target = max_pos
	else:   
	        target = min_pos
	
	chan0 = Thread(target=control, args=(0,))
	chan1 = Thread(target=control, args=(1,))
	chan2 = Thread(target=control, args=(2,))
	chan0.start()    
	chan1.start()
	chan2.start()

def control(c):
	global servo, target
	#for x in range(6000,7000,200):
	#	time.sleep(2)
	#	servo.setTarget(c, x)	
	#	print("going to: ", x)
	#Time.sleep(2)
	if c == 0 or c == 1:
		servo.setTarget(c,target)
		time.sleep(3)
	else:
		servo.setTarget(2,7000)
		time.sleep(5)
		servo.setTarget(c, 6000)

if __name__ == "__main__":
	main()
