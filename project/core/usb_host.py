import sys
import usb.core as core

from core.usb_util import MsgCode, MsgStatus, byteArrToString, GetAllDevices
from core.usb_util import CONFIGURATION_ID, SETTING_ID, OUT_ENDPOINT_ID, IN_ENDPOINT_ID
from typing import List, Union


class USB_Device:

	def __init__(self, id: int, device: core.Device):
		self.id = id
		self.device = device

		if device.is_kernel_driver_active(0):
			try:
				device.detach_kernel_driver(0)
			except core.USBError as e:
				sys.exit("Kernel driver could not be detached: %s" % str(e))

		cfg = device.get_active_configuration()
		interface = cfg[(CONFIGURATION_ID, SETTING_ID)]
		self.outEp = interface[OUT_ENDPOINT_ID]
		self.inEp = interface[IN_ENDPOINT_ID]


class USB_Host:

	def __init__(self):
		devices = GetAllDevices()
		self.devices: List[core.Device] = []
		for i, dev in enumerate(devices):
			self.devices.append(USB_Device(i, dev))

		# Set to true, if next message received should be ignored
		self.ignoreNext: bool = False

	def getCount(self) -> int:
		return len(self.devices)

	def ping(self, id: int = -1) -> bool:
		answers = self.sendMessage(MsgCode.ECHO, id)
		if not isinstance(answers, list):
			return answers == MsgStatus.OK
		for answer in answers:
			if answer != MsgStatus.OK:
				return False
		return True

	def deactivate(self, id: int = -1) -> Union[MsgStatus, List[MsgStatus]]:
		print("Deactivate clients...")
		return self.sendMessage(MsgCode.STOP, id)

	def readMessage(self, id: int, skipAll: bool = False) -> Union[MsgStatus, str]:
		if id < 0:
			print("Cannot read messages from multiple devices at the same time! Use 'readAllMessages' instead")
		for dev in self.__getDevices(id):
			response = MsgStatus.FAIL
			try:
				while (result := dev.inEp.read(64, 1000)):
					if skipAll:
						continue

					msg = byteArrToString(result).strip()

					# Ignore echod commands
					if msg in MsgCode.toList():
						continue
					if msg in MsgStatus.toList():
						status = MsgStatus[msg]
						return status
					else:
						if self.ignoreNext:
							self.ignoreNext = False
							continue
						return msg
			except Exception as e:
				print("Timeout", e)
			return response

	def readAllMessages(self) -> List[MsgStatus]:
		status = []
		for dev in self.devices:
			status.append(self.readMessage(dev.id))
		return status

	def sendMessage(self, code: MsgCode, id: int = -1, message: str = None) -> Union[MsgStatus, List[MsgStatus]]:
		status = []
		for dev in self.__getDevices(id):
			try:
				dev.outEp.write(code.value + "\r")
				answer = self.readMessage(dev.id)

				if message and code == MsgCode.SEND and answer == MsgStatus.OK:
					self.ignoreNext = True
					dev.outEp.write(message + "\r")
					answer = self.readMessage(dev.id)
				if id >= 0:
					return answer
				else:
					status.append(answer)
			except Exception as e:
				print("Send Error:", e)
		return status

	def clearMessages(self, id: int = -1):
		for dev in self.__getDevices(id):
			self.readMessage(dev.id, True)

	def __getDevices(self, id: int) -> List[USB_Device]:
		devices = []
		if id < 0:
			for dev in self.devices:
				devices.append(dev)
		else:
			if id < len(self.devices):
				devices.append(self.devices[id])
		return devices
