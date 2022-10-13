import hid

vid = 0x16c0	# Change it for your device
pid = 0x0486	# Change it for your device
# 
# encoded 1;1;0;0;0;0;0;2;1;0;0;0;0;0|


# 1;0;0;0;0;0;0;2;0;0;0;0;0;0| exits motor control
# with hid.Device(vid, pid) as h:
#     print(f'Device manufacturer: {h.manufacturer}')
#     print(f'Product: {h.product}')
#     print(f'Serial Number: {h.serial}')
#     res = h.write('1;0;0;0;0;0;0;2;0;0;0;0;0;0|'.encode('utf-8'))
#     print(res)
exitc = '1;0;0;0;0;0;0;2;0;0;0;0;0;0|'.encode()
enterc = '1;1;0;0;0;0;0;2;1;0;0;0;0;0|'.encode()
c1 = '1;2;0;0;0;0;0;2;2;0;0;0;0;0|'.encode()
with open('/dev/hidraw0', 'rb+') as f:
    f.flush()
    res = f.write(exitc)
    print(res)
    res = f.write(enterc)
    print(res)
    res = f.write(c1)
    print(res)
    res = f.write(exitc)
    