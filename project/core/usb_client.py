from functools import reduce
import os
import io
import threading
from typing import Dict, List, Union
import traceback

from core.usb_util import MsgAction, MsgOperation, MsgStatus, MsgSender, packMsg, unpackMsg, UnpackedMsg


def chunks(arr: List, n):
	n = max(1, n)
	return list(arr[i: i + n] for i in range(0, len(arr), n))


class USB_Client(threading.Thread):

	def __init__(self, id: int):
		super(USB_Client, self).__init__()
		self.id = id
		self.active = False
		self.deviceFile = "/dev/ttyGS%s" % (self.id)

		# Set to true, if the next message is not a control code
		# self.inputIncoming: bool = False
		# self.output: str = ""

	def activate(self):
		if self.active:
			print("Already active!")
			return
		self.active = True
		self.start()

	def run(self):
		try:
			f = io.TextIOWrapper(io.FileIO(os.open(self.deviceFile, os.O_RDWR), "r+"))
			for msg in iter(f.readline, None):
				unpackedMsg = unpackMsg(msg)
				if not unpackedMsg:
					continue

				response = self.respond(unpackedMsg)
				responseMsg = packMsg(MsgSender.CLIENT, response["status"], response["action"], response["operation"], response["data"])

				for rMsg in chunks(responseMsg, 255):
					f.write(rMsg)

				# stop listening if stop command was send
				if (response["action"] == MsgAction.STOP.value):
					break

		except Exception as e:
			pass
			# print("Receive Error:", e)
			# print(traceback.format_exc())
		finally:
			f.close()

	def respond(self, content: UnpackedMsg) -> Dict:
		# print("Receive message: ", content)
		response = {"status": MsgStatus.UNKNOWN, "action": int(content.action), "operation": int(content.operation), "data": ""}
		action = int(content.action)

		if action == MsgAction.STOP.value:
			if self.active:
				self.active = False
				response["status"] = MsgStatus.OK
			else:
				response["status"] = MsgStatus.FAIL
		elif action == MsgAction.PING.value:
			response["status"] = MsgStatus.OK
		elif action == MsgAction.CALCULATE.value:
			response["status"], response["data"] = self.handleInput(content)

		else:
			pass
			# print("Cannot respond to: ", action)
		return response

	def handleInput(self, content: UnpackedMsg) -> Dict:
		status = MsgStatus.OK
		data = ""
		try:
			if content.operation == MsgOperation.MULTIPLY.value:
				input = int(content.data)
				data = input * 2
			elif content.operation == MsgOperation.AVERAGE.value:
				# totalSum = sum(input)
				# data = totalSum / len(input)
				raise Exception
			elif content.operation == MsgOperation.FINDX.value:
				# data = input[1][input[0]]
				raise Exception
			elif content.operation == MsgOperation.TESTLOAD.value:
				dataLen = int(content.data.strip())
				data = "a" * dataLen
		except Exception as e:
			status = MsgStatus.FAIL
			print(e)
		return status, data
