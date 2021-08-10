# -*- coding: utf-8 -*-
import usb.core as core
import usb.util as util
import sys

CONFIGURATION_ID = 1
SETTING_ID = 0


def main():
	testEndpoint()


def testEndpoint():
	print("\nTest USB endoiint connection..")
	devs = core.find(idVendor=0x1d6b, idProduct=0x0104, find_all=True)
	count = 0
	for dev in devs:
		if dev.is_kernel_driver_active(0):
			try:
				dev.detach_kernel_driver(0)
			except core.USBError as e:
				sys.exit("Kernel driver couldn't be detached: %s" % str(e))

		endpoint = getEndpoint(dev)
		if endpoint is not None:
			count += 1
	print("Found endpoint for %s devices!" % count)
	return count


def getEndpoint(dev):
	cfg = dev.get_active_configuration()
	interface = cfg[(CONFIGURATION_ID, SETTING_ID)]
	return util.find_descriptor(
		interface,
		custom_match=lambda e: util.endpoint_direction(e.bEndpointAddress) == util.ENDPOINT_OUT)


if __name__ == '__main__':
	main()
