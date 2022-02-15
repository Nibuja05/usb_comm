# -*- coding: utf-8 -*-
import __init__
import sys
import os
import re
import getopt
import math
from glob import glob
from typing import List, Literal, Tuple

from util import runRootCommandIn, runRootCommand, runCommandWithOutput, ListEnum
import core.usb_util as usb_util

# Global variables

maxDeviceCount = 0
maxCount = -1
gadgetPath = ""

BASE_PATH = "/sys/kernel/config/usb_gadget"

# loopback type
FUNC_TYPE = "Loopback"
FUNC_NAME = ""
FUNC_NAME_BASE = ""

# acm or loopback?
FUNC_TYPE = usb_util.FUNC_TYPE
FUNC_NAME_BASE = "ttyS" if usb_util.USE_ACM else ""


class SetupTypes(ListEnum):
	CREATE = "create"
	START = "start"
	STOP = "stop"
	CLEAR = "clear"
	STATUS = "status"


# class FuncTypes(ListEnum):
# 	ACM = "acm"
# 	SERIAL = "gser"

# def getFuncDef(funcType: FuncTypes) -> Tuple[str, str]:
# 	if (funcType == FuncTypes.ACM):
# 		return ("acm", "ttyS")
# 	if


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


def getAllUSBGadgets() -> List[str]:
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

	if maxCount < 0:
		maxCount = maxDeviceCount
	maxCount = count if count >= 0 else maxCount
	# maxCount = 8 if usb_util.USE_ACM and maxCount > 8 else maxCount


def getMaxDeviceCount():
	global maxDeviceCount
	path = "/sys/module/dummy_hcd"
	if not os.path.isdir(path):
		print("DUMMY_HCD Module nicht gefunden!")
		sys.exit()
	numPath = os.path.join(path, "parameters/num")
	if os.path.isfile(numPath):
		with open(numPath, "r") as file:
			maxDeviceCount = int(file.read())


def getGadgetPath() -> str:
	global gadgetPath
	if not os.path.isdir(BASE_PATH):
		print("%s nicht gefunden!" % BASE_PATH)
		sys.exit()
	gadgetPath = BASE_PATH


def getCurDeviceCount() -> int:
	count = 0
	gadgetNames = [name for name in os.listdir(gadgetPath)]
	for gadgetName in gadgetNames:
		if "usb_" in gadgetName:
			count += 1
	return count


def getActiveDeciveCount() -> int:
	count = 0
	if not gadgetPath or gadgetPath == "":
		getGadgetPath()
	gadgetNames = [name for name in os.listdir(gadgetPath)]
	for gadgetName in gadgetNames:
		if "usb_" in gadgetName:
			path = os.path.join(gadgetPath, gadgetName)
			with open(os.path.join(path, "UDC")) as file:
				if "dummy_udc." in file.readline():
					count += 1
	return count


def getFuncName(index: int, complete: bool = False) -> str:
	funcName = FUNC_NAME_BASE + "%s" % (index + 0)
	funcName = FUNC_NAME if FUNC_NAME != "" else funcName

	if not complete:
		return funcName
	return "%s.%s" % (FUNC_TYPE, funcName)

# Main functionality


def createNewGadget(index: int, vendor: Literal, product: Literal):
	name = "usb_%s" % index
	completeFuncName = getFuncName(index, True)
	gadgetDir = os.path.join(gadgetPath, name)

	# create gadget
	runRootCommand("mkdir %s" % gadgetDir)

	# create config and function
	runRootCommandIn("mkdir configs/def.1", gadgetDir)
	runRootCommandIn("mkdir functions/%s" % completeFuncName, gadgetDir)

	# create and set strings
	runRootCommandIn("mkdir strings/0x409", gadgetDir)
	runRootCommandIn("mkdir configs/def.1/strings/0x409", gadgetDir)
	runRootCommandIn("echo %s > idProduct" % product, gadgetDir)
	runRootCommandIn("echo %s > idVendor" % vendor, gadgetDir)
	runRootCommandIn("echo %03d > strings/0x409/serialnumber" % index, gadgetDir)
	runRootCommandIn("echo 'USB Setup Helper' > strings/0x409/manufacturer", gadgetDir)
	runRootCommandIn("echo 'Virtual USB Device' > strings/0x409/product", gadgetDir)
	runRootCommandIn("echo 'Primary configuration' > configs/def.1/strings/0x409/configuration", gadgetDir)

	# link function
	runRootCommandIn("ln -s functions/%s configs/def.1" % completeFuncName, gadgetDir)
	# runCommandIn("", gadgetDir)


def create():
	curCount = getCurDeviceCount()
	vendor = usb_util.VENDOR_ID
	product = usb_util.PRODUCT_ID
	for i in range(curCount, maxCount):
		if not usb_util.USE_GT:
			createNewGadget(i, vendor, product)
		else:
			name = "usb_%s" % i
			runRootCommand("gt create %s idProduct=%s idVendor=%s product='Virtual USB Device' manufacturer='USB Setup Helper' serialnumber='000'" % (
				name,
				product,
				vendor)
			)
			runRootCommand("gt config create %s def 1" % name)

			funcName = getFuncName(i)
			runRootCommand("gt func create %s %s %s" % (name, FUNC_TYPE, funcName))
			runRootCommand("gt config add %s def 1 %s %s" % (name, FUNC_TYPE, funcName))


def start():
	for udc, gadget in enumerate(getAllUSBGadgets()):
		if not usb_util.USE_GT:
			gadgetDir = os.path.join(gadgetPath, gadget)
			runRootCommandIn("echo dummy_udc.%s > UDC" % udc, gadgetDir)
		else:
			runRootCommand("gt enable %s %s" % (gadget, "dummy_udc.%s" % udc))


def stop():
	for gadget in getAllUSBGadgets():
		if not usb_util.USE_GT:
			gadgetDir = os.path.join(gadgetPath, gadget)
			runRootCommandIn("echo '' > UDC", gadgetDir)
		else:
			runRootCommand("gt disable %s" % gadget)


def clear():
	# stop the devices first when not using GT
	if not usb_util.USE_GT:
		stop()

	for gadget in getAllUSBGadgets():
		if not usb_util.USE_GT:
			index = int(gadget[4:])
			gadgetDir = os.path.join(gadgetPath, gadget)
			completeFuncName = getFuncName(index, True)
			runRootCommandIn("rm configs/def.1/%s" % completeFuncName, gadgetDir)
			runRootCommandIn("rmdir configs/def.1/strings/0x409", gadgetDir)
			runRootCommandIn("rmdir configs/def.1", gadgetDir)
			runRootCommandIn("rmdir functions/%s" % completeFuncName, gadgetDir)
			runRootCommandIn("rmdir strings/0x409", gadgetDir)
			runRootCommand("rmdir %s" % gadgetDir)
		else:
			runRootCommand("gt rm -r -f %s" % gadget)


def status():
	print("STATUS (%s)" % FUNC_TYPE)
	print(" - MAX DEVICES: %s" % maxDeviceCount)
	print(" - CURRENT DEVICES: %s" % getCurDeviceCount())
	print(" - ACTIVE DEVICES: %s" % getActiveDeciveCount())

# Run Main


if __name__ == "__main__":
	main(sys.argv[1:])
