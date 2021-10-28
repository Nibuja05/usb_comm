
import usb.core as core
import usb.util as util
import usb.control as control
import sys
import array
import os

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import core.usb_util as usb_util

# find device
dev = core.find(idVendor=usb_util.VENDOR_ID, idProduct=usb_util.PRODUCT_ID)

if dev.is_kernel_driver_active(0):
	try:
		dev.detach_kernel_driver(0)
		print("Detached!")
	except core.USBError as e:
		sys.exit("Could not detach kernel driver: %s" % str(e))

# get config
cfg = dev.get_active_configuration()
# interface = cfg[(usb_util.CONFIGURATION_ID, usb_util.SETTING_ID)]
# out_ep = interface[usb_util.OUT_ENDPOINT_ID]
# in_ep = interface[usb_util.IN_ENDPOINT_ID]

print(cfg)

# read/write tests
sys.exit()

testStr = "Test2"
out_ep.write(testStr)
t = in_ep.read(len(testStr) * 8)

print(t)

t = usb_util.byteArrToString(t)

print(t)

print(in_ep.read(10000))

# print(endpoint)
# t = endpoint.read(100)
# print(t)
# endpoint.write("1")

# rc = dev.ctrl_transfer()

# ACM_CTRL_DTR = 0x01
# ACM_CTRL_RTS = 0x02

# bmRequestType = util.build_request_type(util.CTRL_IN, util.CTRL_TYPE_STANDARD, util.CTRL_RECIPIENT_ENDPOINT)
# c = dev.ctrl_transfer(bmRequestType, util.GET_STATUS, wIndex=0x81)
# print(c)

# rc = dev.ctrl_transfer(0x21, 0x22, )

# lid = util.get_langids(dev)[0]
# s = util.get_string(dev, 5, lid)

# t = endpoint.write("gg")
# print(t)

# encoding = array.array('B', [0x80, 0x25, 0x00, 0x00, 0x00, 0x00, 0x08])

# Set line state
# rc = dev.ctrl_transfer(0x21, 0x22, 0x01 | 0x02, 0, None)
# print(rc)

# if rc < 0:
# pass

# Set line encoding: 9600 (baudrate?)
# rc = dev.ctrl_transfer(0x21, 0x20, 0, 0, encoding, 0)
# print(rc)

# print(t)

# endpoint.write('00000000000000000000000')
# t = endpoint.read(1000)
# t = dev.read(0x85, 100)
# dev.write()
# print(t)
# returns: array('B', [161, 32, 0, 0, 0, 0, 2, 0, 0, 0])

# t = dev.write(0x2, "TestTest")
# print(t)
