import usb.core
import usb.util
import sys

dev = usb.core.find(idVendor=0x1209, idProduct=0x0000)

if dev.is_kernel_driver_active(0):
	try:
		dev.detach_kernel_driver(0)
		print("Detached!")
	except usb.core.USBError as e:
		sys.exit("Could not detach kernel driver: %s" % str(e))

dev.set_configuration()

endpoint_out = dev[0][(0, 0)][1]

print(endpoint_out)

msg = b'\x81'

endpoint_out.write("test")
