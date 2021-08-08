import sys
import os
import re
import getopt
import math
from glob import glob
from enum import Enum

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from util import runRootCommand, runCommandWithOutput

# Global variables

maxDeviceCount = 1
maxCount = 1
gadgetPath = ""

FUNC_TYPE = "acm"
FUNC_NAME = "ttyS1"


class SetupTypes(Enum):
	CREATE = "create"
	START = "start"
	STOP = "stop"
	CLEAR = "clear"
	STATUS = "status"

	@classmethod
	def toList(cls):
		return list(map(lambda c: c.value, cls))

# Startup


def main(args):
	if len(args) == 0:
		print("Keine Parameter!\n")
		showHelp()
		sys.exit()
	setupType = args[0]
	if setupType not in SetupTypes.toList():
		print("Unzulässiger Setup Type!\n")
		showHelp()
		sys.exit()

	count = -1
	try:
		opts, args = getopt.getopt(args[1:], "c:", ["count="])
	except getopt.GetoptError:
		print("Unzulässige Parameter!")
		sys.exit()
	else:
		if not len(opts) == 0:
			for opt, arg in opts:
				if opt == "-c" or opt == "--count":
					if not arg.isdigit():
						print("Count ist keine zulässige Angabe!")
						sys.exit()
					else:
						count = int(arg)

	setupType = SetupTypes[setupType.upper()]
	setup(setupType, count)

	print("DONE")


def setup(setupType, count=-1):
	onStart(count)

	# Run according function
	if setupType == SetupTypes.CREATE:
		create()
	elif setupType == SetupTypes.START:
		start()
	elif setupType == SetupTypes.STOP:
		stop()
	elif setupType == SetupTypes.CLEAR:
		clear()
	elif setupType == SetupTypes.STATUS:
		status()


def showHelp():
	text = "Dieses Programm soll die Erstellung und Verwaltung von CONFIGFS Usb-Geräten vereinfachen und automatisieren.\nFolgende modi sind möglich:\n"
	for type in SetupTypes.toList():
		text += " - " + type + "\n"
	print(text)

# Helper functions


def addConfigurationName(index: int):
	pass


def getAllUSBGadgets():
	gadgets = []
	for path in glob(os.path.join(gadgetPath, "usb_*/",)):
		if (match := re.search(r'(\w+)/$', path)):
			name = match.group(1)
			gadgets.append(name)
	return gadgets


# Startup functions


def onStart(count):
	global maxCount
	getMaxDeviceCount()
	getGadgetPath()
	# maxCount = count if count >= 0 else maxDeviceCount
	maxCount = count if count >= 0 else 4


def getMaxDeviceCount():
	global maxDeviceCount
	dummyPath = "/sys/module/dummy_hcd"
	if not os.path.isdir(dummyPath):
		print("DUMMY_HCD Module nicht gefunden!")
		sys.exit()
	numPath = os.path.join(dummyPath, "parameters/num")
	if os.path.isfile(numPath):
		with open(numPath, "r") as file:
			maxDeviceCount = int(file.read())


def getGadgetPath():
	global gadgetPath
	path = "/sys/kernel/config/usb_gadget"
	if not os.path.isdir(path):
		print("%s nicht gefunden!" % path)
		sys.exit()
	gadgetPath = path


def getCurDeviceCount():
	for i in range(0, maxDeviceCount or 10):
		output = runCommandWithOutput("gt get usb_%s" % i)
		if output == "":
			return i
	return maxDeviceCount

# Main functionality


def create():
	curCount = getCurDeviceCount()
	for i in range(curCount, maxCount):
		name = "usb_%s" % i
		runRootCommand("gt create %s idProduct=0x0104 idVendor=0x1d6b product='Virtual USB Device' manufacturer='USB Setup Helper' serialnumber='%s'" % (name, i))
		runRootCommand("gt config create %s def 1" % name)
		runRootCommand("gt func create %s %s %s" % (name, FUNC_TYPE, FUNC_NAME))
		runRootCommand("gt config add %s def 1 %s %s" % (name, FUNC_TYPE, FUNC_NAME))


def start():
	for udc, gadget in enumerate(getAllUSBGadgets()):
		runRootCommand("gt enable %s %s" % (gadget, "dummy_udc.%s" % udc))


def stop():
	for gadget in getAllUSBGadgets():
		runRootCommand("gt disable %s" % gadget)


def clear():
	for gadget in getAllUSBGadgets():
		runRootCommand("gt rm -r -f %s" % gadget)


def status():
	print("STATUS")
	print(" - MAX_DEVICES: %s" % maxDeviceCount)
	print(" - CUR_DEVICES: %s" % getCurDeviceCount())

# Run Main


if __name__ == "__main__":
	main(sys.argv[1:])
