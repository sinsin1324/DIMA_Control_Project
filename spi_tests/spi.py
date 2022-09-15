import Jetson.GPIO as GPIO
import board
import busio
import digitalio
import time
from adafruit_bus_device.spi_device import SPIDevice
import spidev

print(GPIO.model)

cs = digitalio.DigitalInOut(board.D8)
cs.direction = digitalio.Direction.OUTPUT
cs.value = True
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

while not spi.try_lock():
    pass

device = SPIDevice(spi, cs, baudrate=5000000, polarity=0, phase=0)

with device:
    while 1:
        spi.write(bytes([0x01, 0xFF]))
        time.sleep(0.5)
