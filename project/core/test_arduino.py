
import usb.core as core
import usb.util as util
import usb.control as control
import sys
import array
import struct
from functools import reduce

dev = core.find(idVendor=0x1a86, idProduct=0x7523)

if dev.is_kernel_driver_active(0):
	try:
		dev.detach_kernel_driver(0)
		print("Detached!")
	except core.USBError as e:
		sys.exit("Could not detach kernel driver: %s" % str(e))

CONFIGURATION_ID = 0
SETTING_ID = 0
OUT_ENDPOINT_ID = 1
IN_ENDPOINT_ID = 0

cfg = dev.get_active_configuration()
interface = cfg[(CONFIGURATION_ID, SETTING_ID)]
out_ep = interface[OUT_ENDPOINT_ID]
in_ep = interface[IN_ENDPOINT_ID]

msg = "hv93ub4v93b"

out_ep.write(msg)

result = in_ep.read(64)
resMsg = ""


def byteArrToString(arr):
	strBytes = struct.unpack("%sc" % len(arr), arr)
	text = str(reduce(lambda a, b: a + b, strBytes), "utf-8")
	return text


print(result)
# print(result.decode("UTF-8"))

r = byteArrToString(result)
print(r)
