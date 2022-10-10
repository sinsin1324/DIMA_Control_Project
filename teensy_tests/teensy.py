import usb.core
import usb.util

# find our device
dev = usb.core.find(idVendor=0x16c0, idProduct=0x0486)
if dev is None:
    raise ValueError('Device not found')
dev.set_configuration()
cfg = dev.get_active_configuration()
intf = cfg[(0,0)]

ep = usb.util.find_descriptor(
    intf,
    # match the first OUT endpoint
    custom_match = \
    lambda e: \
        usb.util.endpoint_direction(e.bEndpointAddress) == \
        usb.util.ENDPOINT_OUT)

assert ep is not None

# write the data
ep.write('1;1;0;0;0;0;0;2;1;0;0;0;0;0|')
print(ep.read(64))