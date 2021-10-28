import usb.core as core
import usb.util as util
import sys

import core.usb_util as usb_util


def main():
	testEndpoint()


def testEndpoint():
	print("\nTest USB endpoint connection..")
	devs = core.find(idVendor=0x1d6b, idProduct=0x0104, find_all=True)
	count = 0
	for dev in devs:
		if dev.is_kernel_driver_active(0):
			try:
				dev.detach_kernel_driver(0)
			except core.USBError as e:
				sys.exit("Kernel driver couldn't be detached: %s" % str(e))

		if getEndpoints(dev):
			count += 1
	print("Found endpoints for %s devices!" % count)
	return count


def getEndpoints(dev) -> bool:
	cfg = dev.get_active_configuration()
	interface = cfg[(usb_util.CONFIGURATION_ID, usb_util.SETTING_ID)]
	out_ep = interface[usb_util.OUT_ENDPOINT_ID]
	in_ep = interface[usb_util.IN_ENDPOINT_ID]

	return out_ep and in_ep


if __name__ == '__main__':
	main()
