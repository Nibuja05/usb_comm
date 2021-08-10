import __init__
import time
import sys
from util import runCommandWithOutput
from test_connection import testUSBConnections
from test_endpoint import testEndpoint
from setup.create_devices import setup, SetupTypes
from core.usb_manager import TestClientHostCommunication


def main():
	testAll()


def getCurDeviceCount():
	for i in range(10):
		output = runCommandWithOutput("gt get usb_%s" % i)
		if output == "":
			return i
	return 10


def testAll():
	prepareTest()
	count = getCurDeviceCount()
	print("Device count: %s" % count)
	if testUSBConnections() < count:
		fail("USB Connection")
	if testEndpoint() < count:
		fail("USB Endpoint Availability")
	# if testSending() < count:
		# fail("USB Kommunikation")
	if not TestClientHostCommunication():
		fail("USB Client <-> Host Communication")
	cleanTest()

	print("\nAlle Tests erfolgreich!")


def prepareTest():
	print("Initialize Test...")
	setup(SetupTypes.CREATE, 4)
	setup(SetupTypes.START)
	time.sleep(1)


def cleanTest():
	setup(SetupTypes.CLEAR)


def fail(reason):
	print("Test failed!\n - " + reason)
	cleanTest()
	sys.exit()


if __name__ == '__main__':
	main()
