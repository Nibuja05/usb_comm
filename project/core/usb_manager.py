import os
import __init__
from typing import Any, List, Union
import time
from util import suppress_stdout
from core.usb_util import MsgOperation, MsgAction, MsgSender, USE_ACM, CommunicationType, MsgStatus, GetDeviceCount
from core.usb_host import USB_Host, USB_Host_Asyncio, USB_Host_Multiprocessing, USB_Host_Threading
from core.usb_client import USB_Client
from eval.usb_testload import TestLoad
from core.resource_manager import SetHostCores


def main():
	# TestClientHostCommunication()
	# return

	print("Start!")

	# MakeSingleClients(5)

	host = GetAndActivateHost()

	# r = host.sendMessage(MsgAction.CALCULATE, MsgOperation.TESTLOAD, "5,aaaaaaaaaa", 2)
	r = host.sendMessage(MsgAction.PING, MsgOperation.NONE, "", 2)
	print("> RESULT", r)

	return

	# host.clearMessages()
	# res = host.ping()
	# print("Ping res: ", res)

	# host.clearMessages()

	t = StartClientCalculation(host, CalcOperation.FINDX, (2, "Das ist ein ewig langer String, um längere Nachrichten zu verdeutlichen!"), 0)
	print("Test:", t)

	# output = host.requestOutput(0)
	# print("OUTPUT: ", output)

	time.sleep(1)
	host.deactivate()


def ProcessTestLoad(host: USB_Host, load: TestLoad, clientID: int, count: int = 1):
	for _ in range(count):
		if clientID >= 0:
			load.startMeasure()
			answer, _ = host.requestClientAction(MsgOperation.TESTLOAD, str(load.dataLen), clientID, load.count)
			if answer:
				load.checkResult(answer.data)
			else:
				load.addFailedTry()
		else:
			load.startMeasure()
			count = host.getCount()
			answers = host.requestClientAction(MsgOperation.TESTLOAD, str(load.dataLen), clientID, load.count)
			if not answers:
				return
			load.stopMeasure()
			for i, answer in enumerate(answers):
				if answer:
					try:
						load.checkResult(answer.data, True)
					except Exception as e:
						load.addFailedTry()
				else:
					load.addFailedTry()


def StartClientCalculation(host: USB_Host, operation: MsgOperation, data: str, clientID: int = -1) -> Union[None, str]:
	answer = host.requestClientAction(operation, data, clientID)
	if not answer:
		return
	if clientID >= 0:
		return answer.data
	return [entry.data for entry in answer]


def TestClientHostCommunication() -> bool:
	print("\nTest client - host communication...")
	if not USE_ACM:
		print("Non acm communication not yet implemented!")
		return False

	host = GetAndActivateHost()

	answer = host.ping()
	if answer:
		print("%s Pings successfull!" % host.getCount())

	time.sleep(1)
	host.deactivate()
	return answer


def TestClientCalculation() -> bool:
	print("\nTest client calcuation...")
	if not USE_ACM:
		print("Non acm communication not yet implemented!")
		return False

	host = GetAndActivateHost()

	answers = StartClientCalculation(host, MsgOperation.MULTIPLY, "500")
	answerCount = sum(map(lambda c: 1 if c == "1000" else 0, answers))

	print("%s Calculations successfull!" % answerCount)

	time.sleep(1)
	host.deactivate()
	return answerCount == host.getCount()


def MakeClients(count: int) -> List[USB_Client]:
	clients = []
	for i in range(count):
		client = USB_Client(i)
		clients.append(client)
	return clients


def MakeSingleClients(count: int):
	command = ""
	for index in range(count):
		path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "usb_single_client.py")
		command += "python3.8 %s %s &" % (path, index)
	os.system(command)


def GetAndActivateHost(comType: CommunicationType = CommunicationType.BASIC) -> USB_Host:
	SetHostCores()
	# count = GetDeviceCount()
	count = 32

	if comType == comType.THREADING:
		host = USB_Host_Threading(count)
	elif comType == comType.MULTIPROCESSING:
		host = USB_Host_Multiprocessing(count)
	elif comType == comType.ASYNCIO:
		host = USB_Host_Asyncio(count)
	else:
		host = USB_Host(count)

	MakeSingleClients(count)

	return host


if __name__ == "__main__":
	main()
