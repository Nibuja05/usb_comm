import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from util import runCommandWithOutput
from test_connection import testUSBConnections
from test_endpoint import testEndpoint
from test_send import testSending
from setup.create_devices import setup, SetupTypes


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
	print("Anzahl Testgeräte: %s" % count)
	if testUSBConnections() < count:
		fail("USB Verbindung")
	if testEndpoint() < count:
		fail("USB Endpoint Verfügbarkeit")
	if testSending() < count:
		fail("USB Kommunikation")
	cleanTest()

	print("\nAlle Tests erfolgreich!")


def prepareTest():
	print("Tests werden vorbereitet...")
	setup(SetupTypes.CREATE, 4)
	setup(SetupTypes.START)


def cleanTest():
	setup(SetupTypes.CLEAR)


def fail(reason):
	print("Test fehlgeschlagen!\n - " + reason)
	cleanTest()
	sys.exit()


if __name__ == '__main__':
	main()
