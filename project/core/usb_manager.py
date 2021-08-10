import __init__
from typing import List
import time
from core.usb_util import GetAllDevices, MsgCode
from core.usb_host import USB_Host
from core.usb_client import USB_Client


def main():
	# TestClientHostCommunication()
	# return
	print("Start!")
	host = USB_Host()
	count = host.getCount()
	clients = MakeClients(count)
	for c in clients:
		c.activate()

	# host.clearMessages()
	# res = host.ping()
	# print("Ping res: ", res)

	host.sendMessage(MsgCode.SEND, -1, "500")
	t = host.sendMessage(MsgCode.RECV, -1)
	print("Test:", t)

	# output = host.requestOutput(0)
	# print("OUTPUT: ", output)

	time.sleep(1)
	host.deactivate()


def TestClientHostCommunication() -> bool:
	print("\nTest client - host communication...")
	host = USB_Host()
	count = host.getCount()
	clients = MakeClients(count)
	for c in clients:
		c.activate()

	answer = host.ping()
	if answer:
		print("Pings successfull!")

	time.sleep(1)
	host.deactivate()
	return answer


def MakeClients(count: int) -> List[USB_Client]:
	clients = []
	for i in range(count):
		client = USB_Client(i)
		clients.append(client)
	return clients


if __name__ == "__main__":
	main()
