import struct
from functools import reduce
import usb.core as core

from util import ListEnum

CONFIGURATION_ID = 1
SETTING_ID = 0
OUT_ENDPOINT_ID = 1
IN_ENDPOINT_ID = 0


class MsgCode(ListEnum):
	SEND = "SEND"
	ECHO = "ECHO"
	RECV = "RECV"
	STOP = "STOP"


class MsgStatus(ListEnum):
	UNKNOWN = "UNKNOWN"
	OK = "OK"
	FAIL = "FAIL"


def byteArrToString(arr):
	strBytes = struct.unpack("%sc" % len(arr), arr)
	text = str(reduce(lambda a, b: a + b, strBytes), "utf-8")
	return text


def GetAllDevices():
	devs = core.find(idVendor=0x1d6b, idProduct=0x0104, find_all=True)
	return devs
