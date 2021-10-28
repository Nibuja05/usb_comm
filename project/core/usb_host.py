import sys
import os
import usb.core as core
from typing import Dict, List, Union
import threading
from multiprocessing import Process, Queue, Pool
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback
from functools import partial
from timeit import default_timer as timer

from core.usb_util import GetDevice, MsgAction, MsgOperation, MsgStatus, MsgSender, packMsg, unpackMsg, GetAllDevices, UnpackedMsg, byteArrToString
from core.usb_util import CONFIGURATION_ID, SETTING_ID, OUT_ENDPOINT_ID, IN_ENDPOINT_ID
from util import suppress_stdout


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


def calculate(count):
	num = 0
	for _ in range(int(count)):
		num += 1


class USB_Host:

	def __init__(self, count):
		self.devices = None
		self.count = count

	def getCount(self) -> int:
		return self.count

	def ping(self, id: int = -1) -> bool:
		answers = self.sendMessage(MsgAction.PING, MsgOperation.NONE, "", id)
		if not isinstance(answers, list):
			return answers.status == MsgStatus.OK.value
		for answer in answers:
			if answer.status != MsgStatus.OK.value:
				return False
		return True

	def deactivate(self, id: int = -1) -> Union[MsgStatus, List[MsgStatus]]:
		return self.sendMessage(MsgAction.STOP, MsgOperation.NONE, "", id)

	def readMessage(self, dev: USB_Device, skipAll: bool = False, wantedAction: MsgAction = None, echoSize: int = 8, minSize: int = 0) -> UnpackedMsg:
		try:
			lastMsg = ""
			waitForEcho = True
			bufferSize = echoSize + 8 if waitForEcho else minSize + 8
			while (result := dev.inEp.read(bufferSize, 1000 if not skipAll else 100)):
				if skipAll:
					continue

				# print("LEN:", len(result), bufferSize)
				# print(result)

				# print("RECV (Host, RAW):", result)
				msg = lastMsg + byteArrToString(result)
				unpackedMsg = unpackMsg(msg)
				# print("RECV (Host): ", unpackedMsg)

				if not unpackedMsg.isEnd:
					lastMsg = msg.strip()
					continue
				else:
					lastMsg = ""

				# ignore echoed commands:
				if unpackedMsg.sender == MsgSender.HOST.value:
					waitForEcho = False
					bufferSize = echoSize + 8 if waitForEcho else minSize + 8
					continue

				# if this wasn't the wanted action
				if wantedAction and unpackedMsg.action != wantedAction.value:
					continue

				return unpackedMsg
		except Exception as e:
			pass
			print("Timeout", e)
			# print(traceback.format_exc())

	def readAllMessages(self) -> List[MsgStatus]:
		status = []
		for dev in self.devices:
			status.append(self.readMessage(dev))
		return status

	def sendMessage(
		self,
		action: MsgAction,
		operation: MsgOperation,
		data: str = "",
		id: int = -1,
		minSize: int = 0) -> Union[None, UnpackedMsg, List[UnpackedMsg]]:

		answers = []
		for dev in self.getDevices(id):
			try:
				pack = packMsg(MsgSender.HOST, MsgStatus.OK, action, operation, data)

				t = dev.outEp.write(pack)
				answer = self.readMessage(dev, wantedAction=action, echoSize=len(pack), minSize=minSize)

				if id >= 0:
					return answer
				else:
					answers.append(answer)

			except Exception as e:
				pass
				# print("Send Error:", e)
				# print(traceback.format_exc())
		return answers

	def sendSingleMessage(self, device: USB_Device, action: MsgAction, operation: MsgOperation, minSize: int = 0, data: str = ""):
		pack = packMsg(MsgSender.HOST, MsgStatus.OK, action, operation, data)
		t = device.outEp.write(pack)
		answer = self.readMessage(device, wantedAction=action, echoSize=len(pack), minSize=minSize)
		return answer

	def requestClientAction(self, operation: MsgOperation, data: str = "", id: int = -1, count: int = 0):
		# do time intensive calculations on the host
		if id > 0:
			if operation == MsgOperation.TESTLOAD:
				calculate(count)
			return self.sendMessage(MsgAction.CALCULATE, operation, data, id)
		else:
			answers = []
			for i in range(self.getCount()):
				if operation == MsgOperation.TESTLOAD:
					calculate(count)
				dataLen = int(data)
				answers.append(self.sendMessage(MsgAction.CALCULATE, operation, data, i, minSize=dataLen))
			return answers

	def clearMessages(self, id: int = -1):
		with suppress_stdout():
			for dev in self.getDevices(id):
				self.readMessage(dev, True)

	def getDevices(self, id: int) -> List[USB_Device]:
		if not self.devices:
			devices = GetAllDevices()
			self.devices: List[USB_Device] = []
			for i, dev in enumerate(devices):
				self.devices.append(USB_Device(i, dev))

		devices = []
		if id < 0:
			return self.devices
		else:
			if id < len(self.devices):
				devices.append(self.devices[id])
		return devices


class USB_Host_Threading(USB_Host):

	def clearMessages(self, id: int = -1):
		with suppress_stdout():
			for dev in self.getDevices(id):
				self.readMessage(dev, True)
				dev.device.finalize()
			self.devices = None

	def processRequests(self, operation: MsgOperation, data: str = "", count: int = 0):
		results: List[UnpackedMsg] = [None] * self.getCount()
		threads: List[threading.Thread] = []
		for i in range(self.getCount()):
			t = threading.Thread(target=self.processSingleRequest, args=(i, results, operation, data, count))
			threads.append(t)
			t.start()
		for t in threads:
			t.join()

		return results

	def processSingleRequest(self, index: int, results: List[UnpackedMsg], operation: MsgOperation, data: str, count: int):
		if operation == MsgOperation.TESTLOAD:
			calculate(count)
		dataLen = int(data)
		device: USB_Device = USB_Device(index, GetDevice(index))
		results[index] = self.sendSingleMessage(device, MsgAction.CALCULATE, operation, dataLen, data)

		device.device.finalize()

	def requestClientAction(self, operation: MsgOperation, data: str = "", id: int = -1, count: int = 0):
		# do time intensive calculations on the host
		if id > 0:
			if operation == MsgOperation.TESTLOAD:
				calculate(count)
			return self.sendMessage(MsgAction.CALCULATE, operation, data, id)
		else:
			return self.processRequests(operation, data, count)


class USB_Host_Multiprocessing(USB_Host):

	def getCount(self) -> int:
		return 32

	def clearMessages(self, id: int = -1):
		with suppress_stdout():
			for dev in self.getDevices(id):
				self.readMessage(dev, True)
				dev.device.finalize()
			self.devices = None

	def processRequests(self, operation: MsgOperation, data: str = "", count: int = 0):
		workerCount = 32

		messages: List[UnpackedMsg] = []
		with Pool(6) as pool:
			results = [pool.apply_async(self.processSingleRequest, (i, operation, data, count)) for i in range(workerCount)]
			for res in results:
				try:
					result = res.get(timeout=10)
					if result:
						messages.append(result)
				except Exception as e:
					print("MP Error:", e)
		return messages

	def processSingleRequest(self, index: int, operation: MsgOperation, data: str, count: int):
		device: USB_Device = USB_Device(index, GetDevice(index))

		if operation == MsgOperation.TESTLOAD:
			calculate(count)

		unpackedMsg = self.sendSingleMessage(device, MsgAction.CALCULATE, operation, int(data), data)

		# self.sendSingleMessage(device, MsgAction.STOP, MsgOperation.NONE)

		device.device.finalize()

		return unpackedMsg

	def requestClientAction(self, operation: MsgOperation, data: str = "", id: int = -1, count: int = 0):
		# do time intensive calculations on the host
		if id > 0:
			if operation == MsgOperation.TESTLOAD:
				calculate(count)
			return self.sendMessage(MsgAction.CALCULATE, operation, data, id)
		else:
			return self.processRequests(operation, data, count)


class USB_Host_Asyncio(USB_Host):

	def clearMessages(self, id: int = -1):
		with suppress_stdout():
			for dev in self.getDevices(id):
				self.readMessage(dev, True)
				dev.device.finalize()
			self.devices = None

	def processRequests(self, operation: MsgOperation, data: str = "", count: int = 0):
		# res = asyncio.run(self.gatherAnswers(operation, data, count))

		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		future = asyncio.ensure_future(self.processRequestsAsync(operation, data, count))
		loop.run_until_complete(future)
		results = future.result()

		return results

	async def processRequestsAsync(self, operation: MsgOperation, data: str, count: int):
		devCount = self.getCount()
		results = []
		with ThreadPoolExecutor(max_workers=devCount) as executor:
			loop = asyncio.get_event_loop()
			tasks = [
				loop.run_in_executor(
					executor,
					self.processSingleRequest,
					*(id, operation, data, count)
				)
				for id in range(devCount)
			]
			for response in await asyncio.gather(*tasks):
				results.append(response)
		return results

	def processSingleRequest(self, index: int, operation: MsgOperation, data: str, count: int):
		if operation == MsgOperation.TESTLOAD:
			calculate(count)
		dataLen = int(data)
		device: USB_Device = USB_Device(index, GetDevice(index))
		result = self.sendSingleMessage(device, MsgAction.CALCULATE, operation, dataLen, data)

		device.device.finalize()
		return result

	def requestClientAction(self, operation: MsgOperation, data: str = "", id: int = -1, count: int = 0):
		# do time intensive calculations on the host
		if id > 0:
			if operation == MsgOperation.TESTLOAD:
				calculate(count)
			return self.sendMessage(MsgAction.CALCULATE, operation, data, id)
		else:
			return self.processRequests(operation, data, count)
