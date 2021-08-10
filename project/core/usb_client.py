from functools import reduce
import os
import io
import threading
from typing import Union
from core.usb_util import MsgCode, MsgStatus


class USB_Client(threading.Thread):

	def __init__(self, id: int):
		super(USB_Client, self).__init__()
		self.id = id
		self.active = False
		self.deviceFile = "/dev/ttyGS%s" % self.id

		# Set to true, if the next message is not a control code
		self.inputIncoming: bool = False
		self.output: str = ""

	def activate(self):
		if self.active:
			print("Already active!")
			return
		self.start()

	def run(self):
		try:
			f = io.TextIOWrapper(io.FileIO(os.open(self.deviceFile, os.O_RDWR), "r+"))
			for msg in iter(f.readline, None):
				response = self.respond(msg.strip())

				# stop listening if stop command was send
				if (response == "STOP"):
					self.active = False
					f.write(MsgStatus.OK.value)
					break

				# any other message: just send
				f.write(response)

		except Exception as e:
			print("Receive Error:", e)
		finally:
			f.close()

	def respond(self, msg) -> str:
		# behave different if input is sent
		if self.inputIncoming:
			self.handleInput(msg)
			self.inputIncoming = False
			return MsgStatus.OK.value

		response = MsgStatus.UNKNOWN.value
		if msg in MsgCode.toList():
			request = MsgCode[msg]
			if request == MsgCode.STOP:
				return "STOP"
			if request == MsgCode.ECHO:
				response = MsgStatus.OK.value
			if request == MsgCode.SEND:
				response = MsgStatus.OK.value
				self.inputIncoming = True
			if request == MsgCode.RECV:
				return self.output

		else:
			print("Cannot respond to: ", msg)
		return response

	def handleInput(self, input: str) -> str:
		if input.isdigit:
			num = int(input)
			self.output = "%s" % (num * 2)
			return
		self.output = "[Return] " + input
