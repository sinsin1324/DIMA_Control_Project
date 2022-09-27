import Jetson.GPIO as GPIO
import board
import busio
import digitalio
from time import sleep
from adafruit_bus_device.spi_device import SPIDevice
import spidev
from adafruit_mcp2515.canio import Message, RemoteTransmissionRequest
import adafruit_mcp2515

print(GPIO.model)

cs = digitalio.DigitalInOut(board.D8)
cs.direction = digitalio.Direction.OUTPUT
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
mcp = adafruit_mcp2515.MCP2515(spi, cs)
# use loopback to test without another device

while not spi.try_lock():
    pass

device = SPIDevice(spi, cs, baudrate=9600, polarity=0, phase=0)
