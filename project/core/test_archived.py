
import usb.core as core
import usb.util as util
import usb.control as control
import sys
import array

# dev = core.find(idVendor=0x1d6b, idProduct=0x0104)
# dev = core.find(idVendor=0x23a9, idProduct=0xef18)
dev = core.find(idVendor=0x1a86, idProduct=0x7523)

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

# dev.set_configuration()

CONFIGURATION_ID = 0
SETTING_ID = 0
ENDPOINT_ID = 1

cfg = dev.get_active_configuration()
interface = cfg[(CONFIGURATION_ID, SETTING_ID)]
# endpoint = interface[ENDPOINT_ID]
endpoint = util.find_descriptor(
	interface,
	# match the first OUT endpoint
	custom_match=lambda e: util.endpoint_direction(e.bEndpointAddress) == util.ENDPOINT_OUT)

print(endpoint)
# t = endpoint.read(100)
# print(t)
# endpoint.write("1")

# rc = dev.ctrl_transfer()

ACM_CTRL_DTR = 0x01
ACM_CTRL_RTS = 0x02

# bmRequestType = util.build_request_type(util.CTRL_IN, util.CTRL_TYPE_STANDARD, util.CTRL_RECIPIENT_ENDPOINT)
# c = dev.ctrl_transfer(bmRequestType, util.GET_STATUS, wIndex=0x81)
# print(c)

# rc = dev.ctrl_transfer(0x21, 0x22, )

# lid = util.get_langids(dev)[0]
# s = util.get_string(dev, 5, lid)

# t = endpoint.write("gg")
# print(t)

encoding = array.array('B', [0x80, 0x25, 0x00, 0x00, 0x00, 0x00, 0x08])

# Set line state
# rc = dev.ctrl_transfer(0x21, 0x22, 0x01 | 0x02, 0, None)
# print(rc)

# if rc < 0:
# pass

# Set line encoding: 9600 (baudrate?)
# rc = dev.ctrl_transfer(0x21, 0x20, 0, 0, encoding, 0)
# print(rc)

# print(t)

endpoint.write('00000000000000000000000')
# t = endpoint.read(1000)
# t = dev.read(0x85, 100)
# dev.write()
# print(t)
# returns: array('B', [161, 32, 0, 0, 0, 0, 2, 0, 0, 0])

# t = dev.write(0x2, "TestTest")
# print(t)
