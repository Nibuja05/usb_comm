
import usb.core as core
import usb.util as util
import usb.control as control
import sys

import usb_util

import array

dev = core.find(idVendor=0x1d6b, idProduct=0x0104)
# dev = usb.core.find(idVendor=0x23a9, idProduct=0xef18)

if dev.is_kernel_driver_active(0):
	try:
		dev.detach_kernel_driver(0)
		print("Detached!")
	except core.USBError as e:
		sys.exit("Could not detach kernel driver: %s" % str(e))

# try:
# 	usb.util.claim_interface(dev, 0)
# 	print("claimed device")
# except Exception as e:
# 	sys.exit("Could not claim the device: %s" % str(e))

dev.set_configuration()

CONFIGURATION_ID = 1
SETTING_ID = 0
ENDPOINT_ID = 0

cfg = dev.get_active_configuration()
interface = cfg[(CONFIGURATION_ID, SETTING_ID)]
endpoint = interface[ENDPOINT_ID]

print(endpoint)

# bmRequestType = util.build_request_type(util.CTRL_IN, util.CTRL_TYPE_STANDARD, util.CTRL_RECIPIENT_ENDPOINT)
# c = dev.ctrl_transfer(bmRequestType, usb_util.GET_STATUS, wIndex=0x81)
# print(c)

# lid = util.get_langids(dev)[0]
# s = util.get_string(dev, 5, lid)

# t = endpoint.write("")
# print(t)

# t = dev.ctrl_transfer(0x21, 0x22, 0x01 | 0x02, 0, None)
# t = dev.ctrl_transfer(0x21, 0x20, 0, 0, array.array('B', [0x80, 0x25, 0x00, 0x00, 0x00, 0x00, 0x08]))

# print(t)

# endpoint.write('0')
# t = endpoint.read(1000)
# t = dev.read(0x85, 100)
# dev.write()
# print(t)
# returns: array('B', [161, 32, 0, 0, 0, 0, 2, 0, 0, 0])

# t = dev.write(0x2, "TestTest")
# print(t)

sys.exit()

ep = util.find_descriptor(
	interface,
	custom_match=lambda e: util.endpoint_direction(e.bEndpointAddress) == util.ENDPOINT_OUT)

assert ep is not None
# print(ep)

msg = "Test"

# assert dev.ctrl_transfer(0x40, CTRL_LOOPBACK_WRITE, 0, 0, msg) == len(msg)
ep.write(msg, 1000)

# ep.write("test")

# CTRL_LOOPBACK_WRITE = 0
# CTRL_LOOPBACK_READ = 1

# msg = 'test'
# assert dev.ctrl_transfer(0x40, CTRL_LOOPBACK_WRITE, 0, 0, msg) == len(msg)
# ret = dev.ctrl_transfer(0xC0, CTRL_LOOPBACK_READ, 0, 0, len(msg))
# sret = ''.join([chr(x) for x in ret])
# assert sret == msg

# devs = usb.core.find(find_all=True)

# for i, dev in enumerate(devs):
# 	try:
# 		text = "Device %s:\n" % i
# 		text += "\tiManufacturer\t%s\t%s\n" % (dev.iManufacturer, dev.manufacturer)
# 		text += "\tiProduct\t%s\t%s\n" % (dev.iProduct, dev.product)
# 		text += "\tiSerialNumber\t%s\t%s\n" % (dev.iSerialNumber, dev.serial_number)
		
# 		print(text)

# 		# print(dev)

# 	except Exception as e:
# 		pass