
import usb.core as core
import usb.util as util
import sys

CONFIGURATION_ID = 1
SETTING_ID = 0

GET_STATUS = 0x00
CLEAR_FEATURE = 0x01
SET_FEATURE = 0x03
SET_ADDRESS = 0x05
GET_DESCRIPTOR = 0x06
SET_DESCRIPTOR = 0x07
GET_CONFIGURATION = 0x08
SET_CONFIGURATION = 0x09


def main():
	testSending()


def testSending():
	print("Teste USB Kommunikation...")
	devs = core.find(idVendor=0x1d6b, idProduct=0x0104, find_all=True)
	count = 0
	for dev in devs:
		if dev.is_kernel_driver_active(0):
			try:
				dev.detach_kernel_driver(0)
			except core.USBError as e:
				sys.exit("Kernel driver konnte nicht detached werden: %s" % str(e))

		endpoint = getEndpoint(dev)

		if not endpoint:
			continue

		# Teste Control Anfragen:
		bmRequestType = util.build_request_type(util.CTRL_IN, util.CTRL_TYPE_STANDARD, util.CTRL_RECIPIENT_DEVICE)
		c = dev.ctrl_transfer(bmRequestType, GET_STATUS, data_or_wLength=2)
		if not c:
			print("Kontrollanfrage nicht erfolgreich!")
			continue

		try:
			endpoint.write("Test")
		except Exception as e:
			print("Daten-Sendeanfrage nicht efolgreich!")
			print(e)
			continue

		count += 1
	print("Mit %s Geräten erfolgreich kommuniziert!" % count)
	return count


def getEndpoint(dev):
	cfg = dev.get_active_configuration()
	interface = cfg[(CONFIGURATION_ID, SETTING_ID)]
	return util.find_descriptor(
		interface,
		custom_match=lambda e: util.endpoint_direction(e.bEndpointAddress) == util.ENDPOINT_OUT)


if __name__ == '__main__':
	main()
