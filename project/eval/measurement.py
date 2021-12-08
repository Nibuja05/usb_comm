import __init__
from itertools import product
from usb_testload import TestLoad
from core.usb_manager import GetAndActivateHost, ProcessTestLoad
from typing import List

from core.usb_util import CommunicationType
from eval.storage import MeasurementFile, MeasurementTable
from core.usb_host import USB_Host
from util import printProgress

# OPERATION_COUNTS = [10000, 100000, 1000000, 10000000]  # 200000...
# TRANSFER_SIZES = [100, 1000, 10000, 100000]
# OPERATION_COUNTS = [100, 1000, 10000, 100000]  # 200000...
# TRANSFER_SIZES = [1, 10, 100, 1000]
OPERATION_COUNTS = [1000, 10000]
TRANSFER_SIZES = [100, 1000]
REPEAT_COUNT = 1


def runTestsFor(comType: CommunicationType, loadsPerDevice: int) -> MeasurementTable:
	print("Prepare Tests...")
	host = GetAndActivateHost(comType)

	# sometimes the first communication with a device is a little slower after the devices were created,
	# so we ping them here to let the ping take up the creation delay
	host.ping()
	host.clearMessages()

	tab = MeasurementTable(OPERATION_COUNTS, TRANSFER_SIZES)
	for opCount, tSize in product(OPERATION_COUNTS, TRANSFER_SIZES):
		print("[%s, %s]" % (opCount, tSize))
		tl = TestLoad(opCount, tSize)
		ProcessTestLoad(host, tl, -1, REPEAT_COUNT)
		tab.insert(opCount, tSize, tl.getAvgTime())
		# print("[%s, %s]" % (opCount, tSize), "%s/%s" % (tl.successCount, tl.tryCount), tl.getAvgTime())

		# host.clearMessages()

	host.deactivate()
	return tab


def runVarianceTestFor(comType: CommunicationType, opCount: int, tSize: int, repeats: int, origHost: USB_Host = None) -> List[float]:
	print("Prepare Tests...")
	if origHost:
		host = origHost
	else:
		host = GetAndActivateHost(comType)

		# sometimes the first communication with a device is a little slower after the devices were created,
		# so we ping them here to let the ping take up the creation delay
		host.ping()
		host.clearMessages()

	results = []

	tl = TestLoad(opCount, tSize)
	for i in range(repeats):
		printProgress("Run Tests...", repeats, i + 1)
		ProcessTestLoad(host, tl, -1, REPEAT_COUNT)
		results.append(tl.getAvgTime())
		tl.reset()

	if not origHost:
		host.deactivate()
	return results


def runVarianceTestsForAll(comType: CommunicationType, repeats: int):
	totalCount = len(OPERATION_COUNTS) * len(TRANSFER_SIZES)
	curProgress = 1

	host = GetAndActivateHost(comType)

	# sometimes the first communication with a device is a little slower after the devices were created,
	# so we ping them here to let the ping take up the creation delay
	host.ping()

	for opCount, tSize in product(OPERATION_COUNTS, TRANSFER_SIZES):
		print("Variance Test (%s/%s)" % (curProgress, totalCount))
		host.clearMessages()
		data = runVarianceTestFor(comType, opCount, tSize, repeats, host)

		with MeasurementFile() as mf:
			mf.addVarianceMeasurement(comType, opCount, tSize, data, {"Repeat Count": repeats}, force=True)
		curProgress += 1

	host.deactivate()


def main():
	comType = CommunicationType.MULTIPROCESSING

	# runVarianceTestsForAll(comType, 100)

	# opCount, tSize = 10000, 100
	# data = runVarianceTestFor(comType, opCount, tSize, 100)
	# print(data)

	# with MeasurementFile() as mf:
	# 	mf.addVarianceMeasurement(comType, opCount, tSize, data, {"Notice": "First Test"}, force=True)

	tab = runTestsFor(comType, 1)

	data = tab.export()
	print(data)
	# measureName = "Size1"

	# with MeasurementFile() as mf:
	# 	mf.addMeasurement(measureName, comType, {"Info": "Measurements taken with a specific amount of Testloads per device", "Count": 1})
	# 	mf.addMeasurementData(measureName, comType, data, {	"Repeats": REPEAT_COUNT})

	# host = GetAndActivateHost(CommunicationType.ASYNCIO)
	# print(host.ping())

	# print("Clear messages...")
	# host.clearMessages()
	# print("CLear done!")

	# tl1 = TestLoad(10, 10)
	# for i in range(1):
	# 	ProcessTestLoad(host, tl1, -1, 1)
	# 	print("\n\n%s/%s" % (tl1.successCount, tl1.tryCount), tl1.getAvgTime())

	# host.deactivate()


if __name__ == "__main__":
	main()
