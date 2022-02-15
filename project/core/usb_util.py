import __init__
import struct
from functools import reduce
import usb.core as usbcore
from collections import namedtuple

from util import ListEnum

VENDOR_ID = 0x1d6b
PRODUCT_ID = 0x0104

# do you want to use GT (GadgetTool) ?
USE_GT = True

# do you want to use ACM? Otherwise it will use Loopback
USE_ACM = True
FUNC_TYPE = "Loopback" if not USE_ACM else "acm"

CONFIGURATION_ID = 1 if USE_ACM else 0
SETTING_ID = 0
OUT_ENDPOINT_ID = 1
IN_ENDPOINT_ID = 0


class MsgSender(ListEnum):
	HOST = 0
	CLIENT = 1


class MsgStatus(ListEnum):
	UNKNOWN = 0
	OK = 1
	FAIL = 2
	ONGOING = 3


class MsgAction(ListEnum):
	PING = 0
	STOP = 1
	CALCULATE = 2


class MsgOperation(ListEnum):
	NONE = 0
	MULTIPLY = 1
	AVERAGE = 2
	FINDX = 3
	TESTLOAD = 4


class CommunicationType(ListEnum):
	BASIC = "BASIC"
	THREADING = "THREADING"
	ASYNCIO = "ASYNCIO"
	MULTIPROCESSING = "MULTIPROCESSING"


def byteArrToString(arr):
	strBytes = struct.unpack("%sc" % len(arr), arr)
	text = str(reduce(lambda a, b: a + b, strBytes), "utf-8")
	return text


def getEnumValue(enum: ListEnum):
	return enum if isinstance(enum, int) else enum.value


def packMsg(sender: MsgSender, status: MsgStatus, action: MsgAction, operation: MsgOperation, data: str):
	return "~%s%s%s%s%s;\r" % (getEnumValue(sender), getEnumValue(status), getEnumValue(action), getEnumValue(operation), data)


UnpackedMsg = namedtuple("UnpackedMsg", ["isStart", "isEnd", "sender", "status", "action", "operation", "data"])


def unpackMsg(msg) -> UnpackedMsg:
	if len(msg) < 3:
		return
	isStart = msg[0] == "~"
	isEnd = msg[-2] == ";" or msg[-3] == ";"
	dataLen = len(msg)
	dataIndex = 0
	if isStart:
		dataLen -= 4
		dataIndex = 5
	if isEnd:
		dataLen -= 1

	sender, status, action, operation = -1, -1, -1, -1

	if isStart and len(msg) > 4:
		sender, status, action, operation = msg[1], msg[2], msg[3], msg[4]

	data = msg[dataIndex:dataIndex + dataLen - 1]
	if data[-1:] == "\r":
		data = data[:-1]
	if data[-1:] == ";":
		data = data[:-1]
	return UnpackedMsg._make([isStart, isEnd, int(sender), int(status), int(action), int(operation), data])


def GetAllDevices():
	devs = usbcore.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID, find_all=True)
	return devs


def GetDeviceCount():
	devs = usbcore.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID, find_all=True)
	count = 0
	for dev in devs:
		count += 1
		dev.finalize()
	return count


def GetDevice(index: int):
	devs = usbcore.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID, find_all=True)
	for i, dev in enumerate(devs):
		if i == index:
			return dev
