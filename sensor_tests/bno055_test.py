import adafruit_bno055
import board
import busio
import time
bno55=0x28

i2c = board.I2C()
sensor = adafruit_bno055.BNO055_I2C(i2c)

last_val = 0xFFFF
x = 0
def temperature():
    global last_val  # pylint: disable=global-statement
    result = sensor.temperature
    if abs(result - last_val) == 128:
        result = sensor.temperature
        if abs(result - last_val) == 128:
            return 0b00111111 & result
    last_val = result
    return result

def prin():
    global x
    while (x<20):
        print(x)
        print(sensor.euler)
        print(sensor.gravity)
        x+=1

if __name__ == "__main__":
    time.sleep(2)
    st = time.time()
    prin()  
    print(time.time()-st)
