from h5py._hl.dataset import Dataset
import __init__
import os
import h5py
import numpy as np
from typing import Any, List, Dict
from datetime import datetime

from core.usb_util import CommunicationType

DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


def getCurDate() -> str:
	return datetime.now().strftime("%d.%m.%Y %H:%M")


class MeasurementTable():

	def __init__(self, opCounts: List[int], tSizes: List[int]):
		self.size = (len(opCounts), len(tSizes))
		self.data = np.zeros(self.size, dtype=np.float32)
		self.opCounts = np.array(opCounts, dtype=np.float32)
		self.tSizes = np.array(tSizes, dtype=np.float32).reshape((len(tSizes), 1))

	def insert(self, opCount: int, tSize: int, value: float):
		foundOpCount = np.where(self.opCounts == opCount)[0]
		if len(foundOpCount) <= 0:
			return
		xIndex = foundOpCount[0]
		foundTSizes = np.where(self.tSizes == tSize)[0]
		if len(foundOpCount) <= 0:
			return
		yIndex = foundTSizes[0]
		self.data[yIndex, xIndex] = value

	def export(self):
		tab = np.zeros((self.size[0] + 1, self.size[1] + 1), dtype=np.float32)
		tab[0, 1:1 + len(self.opCounts)] = self.opCounts
		tab[1:1 + self.tSizes.shape[0], 0:1] = self.tSizes
		tab[1:1 + self.data.shape[0], 1:1 + self.data.shape[1]] = self.data
		return tab


class MeasurementFile():

	def __init__(self):
		self.file = h5py.File(os.path.join(DATA_PATH, 'Measurements.hdf5'), 'a')

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def addMeasurement(self, groupName: str, comType: CommunicationType, attributes: Dict[str, Any] = {}):
		group = self.file.require_group("%s/%s" % (comType.value, groupName))
		for name, val in attributes.items():
			group.attrs[name] = val
		return group

	def addMeasurementData(self, groupName: str, comType: CommunicationType, data, attributes: Dict[str, Any] = {}):
		group = self.file.require_group("%s/%s" % (comType.value, groupName))
		dataIndex = 1
		while "M%s" % dataIndex in group:
			dataIndex += 1
		dataSet = group.create_dataset("M%s" % dataIndex, data=data)
		for name, val in attributes.items():
			dataSet.attrs[name] = val
		dataSet.attrs["date"] = getCurDate()
		return dataSet

	def addVarianceMeasurement(self, comType: CommunicationType, opCount: int, tSize: int, data, attributes: Dict[str, Any] = {}, force: bool = False):
		group = self.file.require_group("%s/%s" % ("_VARIANCE", comType.value))
		measureName = "c%s_d%s" % (opCount, tSize)
		if measureName in group:
			if force:
				del group[measureName]
			else:
				print("Variance measurement already exists")
				return
		dataSet = group.create_dataset(measureName, data=data)
		for name, val in attributes.items():
			dataSet.attrs[name] = val
		dataSet.attrs["date"] = getCurDate()
		dataSet.attrs["opCount"] = opCount
		dataSet.attrs["tSize"] = tSize
		return dataSet

	def getAvailableVarianceMeasurements(self, comType: CommunicationType):
		if "_VARIANCE" not in self.file:
			return
		group = self.file["_VARIANCE"]
		if comType.value not in group:
			return
		variances: List[Dataset] = group[comType.value]
		varianceMeasurements = {}
		for var in variances:
			dataSet = variances[var]
			varianceMeasurements.setdefault(dataSet.attrs["opCount"], {})[dataSet.attrs["tSize"]] = dataSet[:]
		return varianceMeasurements

	def getAvailableMeasurements(self, comType: CommunicationType, groupName: str):
		group = self.file.require_group("%s/%s" % (comType.value, groupName))
		dataIndex = 1
		while "M%s" % dataIndex in group:
			dataIndex += 1
		data = group["M%s" % (dataIndex - 1)][:]
		size = data.shape
		tab = data[1:size[0], 1:size[1]]
		opCountTab, tSizeTab = data[0, 1:size[1]], data[1:size[0], 0]
		measurements = {}
		for i1, opCount in enumerate(opCountTab):
			for i2, tSize in enumerate(tSizeTab):
				measurements.setdefault(int(opCount), {})[int(tSize)] = tab[i1][i2]
		return measurements

	def getAvailableMeasurements_new(self, comType: CommunicationType, totalLoads: int):
		group = self.file.require_group("%s/%s" % (comType.value, totalLoads))
		result = {}
		for c in group:
			dataIndex = 1
			while "M%s" % dataIndex in group[c]:
				dataIndex += 1
			data = group[c]["M%s" % (dataIndex - 1)][:]
			size = data.shape
			tab = data[1:size[0], 1:size[1]]
			opCountTab, tSizeTab = data[0, 1:size[1]], data[1:size[0], 0]
			measurements = {}
			for i1, opCount in enumerate(opCountTab):
				for i2, tSize in enumerate(tSizeTab):
					measurements.setdefault(int(opCount), {})[int(tSize)] = tab[i1][i2]
			result[c] = measurements
		return result

	def addBootstrapResults(self, comType: CommunicationType, stdData, ciData1, ciData2):
		self.addMeasurement("_STD", comType, {"description": "Standard error"})
		self.addMeasurementData("_STD", comType, stdData)
		self.addMeasurement("_CI1", comType, {"description": "Lower bound of confidence interval"})
		self.addMeasurementData("_CI1", comType, ciData1)
		self.addMeasurement("_CI2", comType, {"description": "Upper bound of confidence interval"})
		self.addMeasurementData("_CI2", comType, ciData2)

	def addSimpleMeasurement(self, data: Any, mName: str, attributes: Dict[str, Any] = {}):
		group = self.file.require_group("OTHER")
		for name, val in attributes.items():
			group.attrs[name] = val
		group.create_dataset(mName, data=data)

	def getSimpleMeasurement(self, name: str):
		group = self.file.require_group("OTHER")
		return group[name][:]

	def close(self):
		self.file.close()


if __name__ == "__main__":
	pass
	# data = MeasurementTable([5, 50, 500, 5000, 50000], [50, 500, 5000, 50000, 500000])

	# data.insert(50, 5000, 200)

	# tab = data.export()

	with MeasurementFile() as mf:
		mf.addVarianceMeasurement(CommunicationType.BASIC, 100, 100, [1, 2, 3, 4, 5], force=True)
	# mf.addMeasurement("Test", CommunicationType.BASIC, {"Info": "Measurements taken with a specific amount of Testloads per device", "Count": 1})
	# mf.addMeasurementData("Test", CommunicationType.BASIC, tab)
	# mf.close()
