from multiprocessing.connection import Connection
import sys
import os
import usb.core as core
from typing import Dict, List, Union, Tuple
import threading
from multiprocessing import Pipe, Process, Queue, Pool
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback
from functools import partial
import psutil
import time

from core.usb_util import GetDevice, MsgAction, MsgOperation, MsgStatus, MsgSender, packMsg, unpackMsg, GetAllDevices, UnpackedMsg, byteArrToString
from core.usb_util import CONFIGURATION_ID, SETTING_ID, OUT_ENDPOINT_ID, IN_ENDPOINT_ID
from core.resource_manager import SetHostCores
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

	def prepareDevices(self):
		self.getDevices(-1)

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

				msg = lastMsg + byteArrToString(result)
				unpackedMsg = unpackMsg(msg)
				if not unpackedMsg:
					continue

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

	def requestClientAction(self, operation: MsgOperation, maxDevices: int = -1, data: str = "", count: int = 0):
		# do time intensive calculations on the host
		answers = []
		actionCount = maxDevices if maxDevices >= 0 else self.getCount()
		for i in range(actionCount):
			dataLen = int(data)
			if dataLen > 0:
				answers.append(self.sendMessage(MsgAction.CALCULATE, operation, data, i, minSize=dataLen))
			else:
				answers.append(UnpackedMsg._make([True, True, -1, -1, -1, -1, ""]))
			if operation == MsgOperation.TESTLOAD:
				calculate(count)
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

	def processRequests(self, operation: MsgOperation, actionCount: int, data: str = "", count: int = 0):
		results: List[UnpackedMsg] = [None] * self.getCount()
		threads: List[threading.Thread] = []
		for i in range(actionCount):
			t = threading.Thread(target=self.processSingleRequest, args=(i, results, operation, data, count))
			threads.append(t)
			t.start()
		for t in threads:
			t.join()

		return results

	def processSingleRequest(self, index: int, results: List[UnpackedMsg], operation: MsgOperation, data: str, count: int):
		# do time intensive calculations on the host
		dataLen = int(data)
		device = self.devices[index]
		if dataLen > 0:
			results[index] = self.sendSingleMessage(device, MsgAction.CALCULATE, operation, dataLen, data)
		else:
			results[index] = UnpackedMsg._make([True, True, -1, -1, -1, -1, ""])

		if operation == MsgOperation.TESTLOAD:
			calculate(count)

		device.device.finalize()

	def requestClientAction(self, operation: MsgOperation, maxDevices: int = -1, data: str = "", count: int = 0):
		actionCount = maxDevices if maxDevices >= 0 else self.getCount()
		return self.processRequests(operation, actionCount, data, count)


class USB_Host_Asyncio(USB_Host):

	def clearMessages(self, id: int = -1):
		with suppress_stdout():
			for dev in self.getDevices(id):
				self.readMessage(dev, True)
				dev.device.finalize()

	def processRequests(self, operation: MsgOperation, actionCount: int, data: str = "", count: int = 0):
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		future = asyncio.ensure_future(self.processRequestsAsync(operation, actionCount, data, count))
		loop.run_until_complete(future)
		results = future.result()

		return results

	async def processRequestsAsync(self, operation: MsgOperation, actionCount: int, data: str, count: int):
		results = []
		with ThreadPoolExecutor(max_workers=actionCount) as executor:
			loop = asyncio.get_event_loop()
			tasks = [
				loop.run_in_executor(
					executor,
					self.processSingleRequest,
					*(id, operation, data, count)
				)
				for id in range(actionCount)
			]
			for response in await asyncio.gather(*tasks):
				results.append(response)
		return results

	def processSingleRequest(self, index: int, operation: MsgOperation, data: str, count: int):
		dataLen = int(data)
		device = self.devices[index]
		if dataLen > 0:
			result = self.sendSingleMessage(device, MsgAction.CALCULATE, operation, dataLen, data)
		else:
			result = UnpackedMsg._make([True, True, -1, -1, -1, -1, ""])

		if operation == MsgOperation.TESTLOAD:
			calculate(count)

		device.device.finalize()
		return result

	def requestClientAction(self, operation: MsgOperation, maxDevices: int = -1, data: str = "", count: int = 0):
		actionCount = maxDevices if maxDevices >= 0 else self.getCount()
		return self.processRequests(operation, actionCount, data, count)


class USB_Host_Multiprocessing(USB_Host):

	def __init__(self, count):
		self.devices = None
		self.count = count
		self.workerCount = count
		self.pCount = 6

	def prepareDevices(self):
		self.test = False

		self.processes: List[Process] = []
		self.cons: List[Tuple[Connection, Connection]] = []
		for i in range(self.workerCount):
			recvCon, sendCon = Pipe(False)
			sRecvCon, sSendCon = Pipe(False)
			process = Process(target=self.handleProcess, args=(i, sendCon, sRecvCon))
			self.processes.append(process)
			self.cons.append((recvCon, sSendCon))
			process.start()

		for i in range(self.workerCount):
			con, _ = self.cons[i]
			process = self.processes[i]
			con.recv()
			ps = psutil.Process(process.pid)
			ps.suspend()

	def deactivate(self, id: int = -1) -> Union[MsgStatus, List[MsgStatus]]:
		for i in range(self.workerCount):
			_, sendCon = self.cons[i]
			process = self.processes[i]
			ps = psutil.Process(process.pid)
			ps.resume()
			sendCon.send((MsgOperation.NONE, None, None))

		for i in range(self.workerCount):
			con, _ = self.cons[i]
			process = self.processes[i]
			con.recv()
			process.kill()

		self.processes = None
		self.cons = None

	def clearMessages(self, id: int = -1):
		with suppress_stdout():
			for dev in self.getDevices(id):
				self.readMessage(dev, True)
				dev.device.finalize()

	def processRequests(self, operation: MsgOperation, actionCount: int, data: str = "", count: int = 0):
		messages: List[UnpackedMsg] = []

		# send request to process
		for i in range(min(self.workerCount, actionCount)):
			_, sendCon = self.cons[i]
			process = self.processes[i]
			ps = psutil.Process(process.pid)
			ps.resume()
			sendCon.send((operation, data, count))

		# gather answers
		for i in range(min(self.workerCount, actionCount)):
			con, _ = self.cons[i]
			process = self.processes[i]
			messages.append(con.recv())
			ps = psutil.Process(process.pid)
			ps.suspend()

		return messages

	def handleProcess(self, index: int, sendCon: Connection, statusCon: Connection):
		device: USB_Device = USB_Device(index, GetDevice(index))
		SetHostCores()
		sendCon.send(None)

		while True:
			operation, data, count = statusCon.recv()
			if operation == MsgOperation.NONE:
				self.sendSingleMessage(device, MsgAction.STOP, operation)
				sendCon.send(None)
			else:
				answer = self.processSingleRequest(index, operation, data, count, device)
				sendCon.send(answer)

	def processSingleRequest(self, index: int, operation: MsgOperation, data: str, count: int, device: USB_Device):
		# do time intensive calculations on the host
		dataLen = int(data)
		if dataLen > 0:
			unpackedMsg = self.sendSingleMessage(device, MsgAction.CALCULATE, operation, dataLen, data)
		else:
			unpackedMsg = UnpackedMsg._make([True, True, -1, -1, -1, -1, ""])

		if operation == MsgOperation.TESTLOAD:
			calculate(count)

		device.device.finalize()
		return unpackedMsg

	def requestClientAction(self, operation: MsgOperation, maxDevices: int = -1, data: str = "", count: int = 0):
		actionCount = maxDevices if maxDevices >= 0 else self.getCount()
		return self.processRequests(operation, actionCount, data, count)
