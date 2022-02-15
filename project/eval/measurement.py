import __init__
from itertools import product
from usb_testload import TestLoad
from core.usb_manager import GetAndActivateHost, ProcessTestLoad
from typing import List
import time
import numpy as np

from core.usb_util import CommunicationType
from eval.storage import MeasurementFile, MeasurementTable, MultiMeasurementTable
from core.usb_host import USB_Host
from setup.create_devices import setup, SetupTypes
from util import printProgress

OPERATION_COUNTS = [10000, 100000, 1000000, 10000000]  # 200000...
TRANSFER_SIZES = [100, 1000, 10000, 100000]
# OPERATION_COUNTS = [100, 1000, 10000, 100000]  # 200000...
# TRANSFER_SIZES = [1, 10, 100, 1000]
# OPERATION_COUNTS = [20000000, 30000000]
# TRANSFER_SIZES = [100]
DEVICE_COUNTS = [1, 2, 4, 8, 16, 32]
LOADS_PER_DEVICE = [1, 2, 4]
REPEAT_COUNT = 10


def runTestsFor(comType: CommunicationType, totalLoads: int = 1) -> MeasurementTable:
	print("\nPrepare Tests...")
	host = GetAndActivateHost(comType)
	host.prepareDevices()

	# sometimes the first communication with a device is a little slower after the devices were created,
	# so we ping them here to let the ping take up the creation delay
	host.ping()
	host.clearMessages()

	tab = MeasurementTable(OPERATION_COUNTS, TRANSFER_SIZES)
	for opCount, tSize in product(OPERATION_COUNTS, TRANSFER_SIZES):
		print("[%s, %s]" % (opCount, tSize))
		tl = TestLoad(opCount, tSize)
		ProcessTestLoad(host, tl, totalLoads, REPEAT_COUNT)
		tab.insert(opCount, tSize, tl.getAvgTime())

	host.deactivate()
	return tab


def runDetailedTestsFor(comType: CommunicationType, totalLoads: int = 1) -> MeasurementTable:
	print("\nPrepare Tests...")
	host = GetAndActivateHost(comType)
	host.prepareDevices()

	# sometimes the first communication with a device is a little slower after the devices were created,
	# so we ping them here to let the ping take up the creation delay
	host.ping()
	host.clearMessages()

	tab = MultiMeasurementTable(OPERATION_COUNTS, TRANSFER_SIZES)
	for opCount, tSize in product(OPERATION_COUNTS, TRANSFER_SIZES):
		print("[%s, %s]" % (opCount, tSize))
		tl = TestLoad(opCount, tSize)
		ProcessTestLoad(host, tl, totalLoads, REPEAT_COUNT)
		tab.insert(opCount, tSize, tl.getAllTimes())

	host.deactivate()
	return tab


def runVarianceTestFor(comType: CommunicationType, opCount: int, tSize: int, repeats: int, origHost: USB_Host = None) -> List[float]:
	print("Prepare Tests...")
	if origHost:
		host = origHost
	else:
		host = GetAndActivateHost(comType)
		host.prepareDevices()

		# sometimes the first communication with a device is a little slower after the devices were created,
		# so we ping them here to let the ping take up the creation delay
		host.ping()
		host.clearMessages()

	results = []

	tl = TestLoad(opCount, tSize)
	for i in range(repeats):
		printProgress("Run Tests...", repeats, i + 1)
		ProcessTestLoad(host, tl, 32, 1)
		results.append(tl.getAvgTime())
		tl.reset()

	if not origHost:
		host.deactivate()
	return results


def runVarianceTestsForAll(comType: CommunicationType, repeats: int):
	totalCount = len(OPERATION_COUNTS) * len(TRANSFER_SIZES)
	curProgress = 1

	host = GetAndActivateHost(comType)
	host.prepareDevices()

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


def runAutomatedTests(devices: List[int], totalLoads: List[int], comType: CommunicationType, multiplyLoadCount: bool = False):
	print("\n\nStarting Automated Tests [%s] for:\n - Device Counts: %s\n - Total Load Count: %s" % (comType.value, devices, totalLoads))
	if multiplyLoadCount:
		print(" - Multiplying Total Load Count by Device Counts")

	for deviceCount in devices:
		print("\nRunning Tests for %s device%s..." % (deviceCount, "" if deviceCount == 1 else "s"))

		for totalLoad in totalLoads:
			if multiplyLoadCount:
				totalLoad *= deviceCount

			setup(SetupTypes.CLEAR)
			setup(SetupTypes.CREATE, deviceCount)
			setup(SetupTypes.START)
			time.sleep(0.25)

			measureName = "%s/%s" % (totalLoad, deviceCount)

			time.sleep(0.5)
			table = runTestsFor(comType, totalLoad)
			data = table.export()

			with MeasurementFile() as mf:
				mf.addMeasurement(measureName, comType, {
					"Info": "Measurements taken with a specific amount of total testloads for device count",
					"Total Load Count": totalLoad,
					"Device Count": deviceCount
				})
				mf.addMeasurementData(measureName, comType, data, {"Repeats": REPEAT_COUNT})

		setup(SetupTypes.CLEAR)


def runDetailedAutomatedTests(devices: List[int], totalLoads: List[int], comType: CommunicationType, multiplyLoadCount: bool = False):
	print("\n\nStarting Automated Tests [%s] for:\n - Device Counts: %s\n - Total Load Count: %s" % (comType.value, devices, totalLoads))
	if multiplyLoadCount:
		print(" - Multiplying Total Load Count by Device Counts")

	for deviceCount in devices:
		print("\nRunning Tests for %s device%s..." % (deviceCount, "" if deviceCount == 1 else "s"))

		for totalLoad in totalLoads:
			if multiplyLoadCount:
				totalLoad *= deviceCount

			setup(SetupTypes.CLEAR)
			setup(SetupTypes.CREATE, deviceCount)
			setup(SetupTypes.START)
			time.sleep(0.25)

			measureName = "%s/%s" % (totalLoad, deviceCount)

			time.sleep(0.5)
			table = runDetailedTestsFor(comType, totalLoad)
			data = table.export()

			with MeasurementFile(True) as mf:
				mf.addMeasurement(measureName, comType, {
					"Info": "Measurements taken with a specific amount of total testloads for device count",
					"Total Load Count": totalLoad,
					"Device Count": deviceCount,
					"Try Count": REPEAT_COUNT
				})
				mf.addMeasurementData(measureName, comType, data, {"Repeats": REPEAT_COUNT})

		setup(SetupTypes.CLEAR)


def runAutomatedVarianceTests(repeats: int, comTypes: List[CommunicationType] = []):
	print("\n\nStarting Automated Variance Tests with %s repeats\n" % repeats)

	if len(comTypes) < 1:
		comTypes = CommunicationType

	for comType in comTypes:
		print("Run for %s" % comType.value)

		setup(SetupTypes.CLEAR)
		setup(SetupTypes.CREATE, 32)
		setup(SetupTypes.START)
		time.sleep(3)

		print("Setup complete")
		runVarianceTestsForAll(comType, repeats)

		time.sleep(3)

	setup(SetupTypes.CLEAR)


def main():
	print("=======================")
	print("TEST AUTOMATION RUNNING")
	print("=======================\n")

	# runVarianceTestFor(CommunicationType.ASYNCIO, 10000, 100, 10)

	runAutomatedVarianceTests(30, [CommunicationType.ASYNCIO, CommunicationType.MULTIPROCESSING])
	# runAutomatedVarianceTestsFor(CommunicationType.MULTIPROCESSING, 100)
	# comType = CommunicationType.MULTIPROCESSING
	# runAutomatedTests([1, 2, 4, 8, 16, 32], [1, 2, 4], comType, True)

	# runAutomatedTests(DEVICE_COUNTS, LOADS_PER_DEVICE, CommunicationType.BASIC, True)
	# runAutomatedTests(DEVICE_COUNTS, LOADS_PER_DEVICE, CommunicationType.THREADING, True)
	# runAutomatedTests(DEVICE_COUNTS, LOADS_PER_DEVICE, CommunicationType.ASYNCIO, True)
	# runAutomatedTests(DEVICE_COUNTS, LOADS_PER_DEVICE, CommunicationType.MULTIPROCESSING, True)

	# runDetailedAutomatedTests(DEVICE_COUNTS, LOADS_PER_DEVICE, CommunicationType.BASIC, True)
	# runDetailedAutomatedTests(DEVICE_COUNTS, LOADS_PER_DEVICE, CommunicationType.THREADING, True)
	# runDetailedAutomatedTests(DEVICE_COUNTS, LOADS_PER_DEVICE, CommunicationType.ASYNCIO, True)
	# runDetailedAutomatedTests(DEVICE_COUNTS, LOADS_PER_DEVICE, CommunicationType.MULTIPROCESSING, True)

	# setup(SetupTypes.CLEAR)
	# setup(SetupTypes.CREATE)
	# setup(SetupTypes.START)

	# t = runVarianceTestFor(comType, 1000, 100, 10)
	# print(t)

	# print("Start...")

	# host = GetAndActivateHost(comType)
	# host.prepareDevices()
	# host.ping()
	# host.clearMessages()

	# print("Run...")

	# tl = TestLoad(1000000, 10000)
	# ProcessTestLoad(host, tl, 32, 10)

	# print(tl.getAvgTime())

	# opCounts = np.linspace(10**4, 10**7, 25)
	# results = []

	# for opCount, tSize in product(opCounts, TRANSFER_SIZES):
	# 	print("[%s, %s]" % (opCount, tSize))
	# 	tl = TestLoad(opCount, tSize)
	# 	ProcessTestLoad(host, tl, 32, REPEAT_COUNT)
	# 	results.append(tl.getAvgTime())
	# 	# print(tl.getAvgTime())

	# with MeasurementFile() as mf:
	# 	mf.addSimpleMeasurement(results, "CountProgress [%s]" % comType.value, {"info": "created with 'np.linspace(10**4, 10**7, 25)'", "transfer size": "100"})

	# runVarianceTestsForAll(comType, 100)

	# opCount, tSize = 10000, 100
	# data = runVarianceTestFor(comType, opCount, tSize, 100)
	# print(data)

	# with MeasurementFile() as mf:
	# 	mf.addVarianceMeasurement(comType, opCount, tSize, data, {"Notice": "First Test"}, force=True)

	# tab = runTestsFor(comType, 32)

	# data = tab.export()
	# print(data)
	# measureName = "Final"

	# with MeasurementFile() as mf:
	# 	mf.addMeasurement(measureName, comType, {"Info": "Measurements taken with a specific amount of Testloads per device", "Count": 1})
	# 	mf.addMeasurementData(measureName, comType, data, {	"Repeats": REPEAT_COUNT})

	# host = GetAndActivateHost(CommunicationType.ASYNCIO)
	# host.prepareDevices()
	# # print(host.ping())

	# print("Clear messages...")
	# host.clearMessages()
	# print("CLear done!")

	# tl1 = TestLoad(10000000, 100000)
	# for i in range(1):
	# 	ProcessTestLoad(host, tl1, -1, 1)
	# 	print("\n\n%s/%s" % (tl1.successCount, tl1.tryCount), tl1.getAvgTime())

	# host.deactivate()
	# setup(SetupTypes.CLEAR)


if __name__ == "__main__":
	main()
