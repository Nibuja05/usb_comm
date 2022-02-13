from __future__ import annotations  # to make class types work inside the class itself
from functools import reduce
from typing import List, Tuple
import numpy as np
import time
from timeit import default_timer as timer  # default timer uses best timer, automatically chosen for the OS


class TestLoad():

	def __init__(self, count: int, dataLen: int) -> None:
		self.count = count
		self.dataLen = dataLen
		self.data = "a" * dataLen
		self.times = []
		self.time = 0
		self.tryCount = 0
		self.successCount = 0
		self.success = False

	def startMeasure(self):
		self.__startTime = timer()

	def cancelMeasure(self):
		self.__startTime = None

	def stopMeasure(self):
		time = timer() - self.__startTime if self.__startTime else 0
		self.times.append(time)
		self.time += time

	def addFailedTry(self):
		self.tryCount += 1

	def checkResult(self, data: str, noConfirm: bool = False):
		success = data == self.data
		if success:
			self.successCount += 1
		else:
			print("%s <-> %s" % (len(data), len(self.data)))
		self.tryCount += 1

	def getAvgTime(self):
		if self.successCount < 1:
			return -1
		timeAvg = self.time / self.successCount
		return timeAvg

	def getTotalTime(self):
		return self.time

	def getAllTimes(self):
		return self.times

	def reset(self):
		self.cancelMeasure()
		self.time = 0
		self.times = []
		self.tryCount = 0
		self.successCount = 0
		self.success = False

	# should also include steps!!!
	@staticmethod
	def createRange(countRange: Tuple[int, int], dataRange: Tuple[int, int]) -> List[TestLoad]:
		loads = []
		for c in range(countRange[0], countRange[1] + 1):
			for d in range(dataRange[0], dataRange[1] + 1):
				loads.append(TestLoad(c, d))
		return loads

	def __str__(self) -> str:
		return self.data

	def __repr__(self) -> str:
		return "TestLoad[%s, %s]" % (self.count, self.dataLen)


if __name__ == "__main__":
	tl = TestLoad(5, 10)
	tl.startMeasure()
	time.sleep(1)
	tl.checkResult(tl.count, tl.data)
	tl.startMeasure()
	time.sleep(1)
	tl.checkResult(tl.count, tl.data)
	print(tl.getAvgTime())
