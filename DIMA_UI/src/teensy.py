defaultDevice = '/dev/usb/hiddev0'

inDev = open(defaultDevice, 'rb')

while True:
 inBytes = inDev.write('1;1;0;0;0;0;0;2;1;0;0;0;0;0|')
 for x in inBytes:
  print(x)