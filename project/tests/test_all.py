import __init__
import time
import sys
import unittest

from util import runCommandWithOutput
from test_connection import testUSBConnections
from test_endpoint import testEndpoint
from setup.create_devices import setup, SetupTypes, getCurDeviceCount
from core.usb_manager import TestClientCalculation, TestClientHostCommunication


class USB_Comm_Test(unittest.TestCase):

	def setUp(self) -> None:
		print("Create Devices")
		setup(SetupTypes.CREATE)
		setup(SetupTypes.START)

		# wait for gadget creation!
		time.sleep(1)

		self.count: int = getCurDeviceCount()

	def test_connection(self):
		self.assertEqual(testUSBConnections(), self.count)

	def test_endpoints(self):
		self.assertEqual(testEndpoint(), self.count)

	def test_comm(self):
		self.assertTrue(TestClientHostCommunication())

	def test_calc(self):
		self.assertTrue(TestClientCalculation())

	def tearDown(self) -> None:
		time.sleep(1)
		setup(SetupTypes.CLEAR)
		time.sleep(1)


if __name__ == '__main__':
	unittest.main()
