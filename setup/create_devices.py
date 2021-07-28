from util import runCommand, runRootCommand
import sys
import os
import re
from glob import glob
from enum import Enum
from subprocess import call


class SetupTypes(Enum):
	CREATE = "create"
	START = "start"
	STOP = "stop"
	CLEAR = "clear"

	@classmethod
	def toList(cls):
		return list(map(lambda c: c.value, cls))

# Startup


def main(args):
	if len(args) == 0:
		print("Keine Parameter!\n")
		showHelp()
		sys.exit()
	if len(args) > 1:
		print("Zu viele Parameter!\n")
		showHelp()
		sys.exit()
	setupType = args[0]
	if setupType not in SetupTypes.toList():
		print("Unzulässiger Setup Type!\n")
		showHelp()
		sys.exit()

	print("START")
	onStart()

	# Run according function
	setupType = SetupTypes[setupType.upper()]
	if setupType == SetupTypes.CREATE:
		create()
	elif setupType == SetupTypes.START:
		start()
	elif setupType == SetupTypes.STOP:
		stop()
	elif setupType == SetupTypes.CLEAR:
		clear()


def showHelp():
	text = "Dieses Programm soll die Erstellung und Verwaltung von CONFIGFS Usb-Geräten vereinfachen und automatisieren.\nFolgende modi sind möglich:\n"
	for type in SetupTypes.toList():
		text += " - " + type + "\n"
	print(text)


# Global variables

maxDeviceCount = 1
gadgetPath = ""

FUNC_TYPE = "acm"
FUNC_NAME = "ttyS1"

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


def onStart():
	getMaxDeviceCount()
	getGadgetPath()


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

# Main functionality


def create():
	# for i in range(maxDeviceCount):
	for i in range(3):
		name = "usb_%s" % i
		runRootCommand("gt create %s idProduct=0x00%s idVendor=0x1209 product='Virtual USB Device' manufacturer='USB Setup Helper' serialnumber='%s'" % (name, i, i))
		runRootCommand("gt config create %s def 1" % name)
		runRootCommand("gt config create %s def 2" % name)
		runRootCommand("gt func create %s %s %s" % (name, FUNC_TYPE, FUNC_NAME))
		runRootCommand("gt config add %s def 1 %s %s" % (name, FUNC_TYPE, FUNC_NAME))
		runRootCommand("gt config add %s def 2 %s %s" % (name, FUNC_TYPE, FUNC_NAME))


def start():
	for udc, gadget in enumerate(getAllUSBGadgets()):
		runRootCommand("gt enable %s %s" % (gadget, "dummy_udc.%s" % udc))


def stop():
	for gadget in getAllUSBGadgets():
		runRootCommand("gt disable %s" % gadget)


def clear():
	for gadget in getAllUSBGadgets():
		runRootCommand("gt rm -r -f %s" % gadget)

# Run Main


if __name__ == "__main__":
	main(sys.argv[1:])
