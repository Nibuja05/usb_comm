import __init__
from typing import List, Tuple
import math
from functools import reduce
from itertools import product
import numpy as np
import statsmodels.api as sm
import pylab
import matplotlib.pyplot as plt

from eval.storage import MeasurementFile, MeasurementTable
from core.usb_util import CommunicationType
from eval.measurement import OPERATION_COUNTS, TRANSFER_SIZES


# from https://stackoverflow.com/questions/37765197/darken-or-lighten-a-color-in-matplotlib
def lighten_color(color, amount=0.5):
	"""
	Lightens the given color by multiplying (1-luminosity) by the given amount.
	Input can be matplotlib color string, hex string, or RGB tuple.

	Examples:
	>> lighten_color('g', 0.3)
	>> lighten_color('#F034A3', 0.6)
	>> lighten_color((.3,.55,.1), 0.5)
	"""
	import matplotlib.colors as mc
	import colorsys
	try:
		c = mc.cnames[color]
	except Exception as e:
		c = color
	c = colorsys.rgb_to_hls(*mc.to_rgb(c))
	return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])


def calculateStatisticValues(values: List[float]) -> float:
	count = len(values)
	average = sum(values) / count
	cases = sum(map(lambda v: (v - average)**2, values))
	variance = cases / (count - 1)
	values.sort()
	middle = values[int(count / 2)]
	prob = 1 / count
	ev = sum(map(lambda v: v * prob, values))
	return variance, variance**0.5, middle, ev


def showValuePlot(values: List[float], comType: CommunicationType):
	values.sort()
	plt.plot(values)
	plt.title("Sortierte Messwerte %s" % comType.value)
	plt.ylabel("Messwerte")
	plt.xlabel("Index")
	plt.show()


def showQQPlot(values: List[float], comType: CommunicationType):
	sm.qqplot(values, line='q')
	pylab.title("QQPlot (n = %d) %s" % (len(values), comType.value))
	pylab.show()


def showTheoreticalDistribution(values: List[float]) -> Tuple[float, Tuple[float, float]]:
	variance, sigma, median, mu = calculateStatisticValues(values)

	xValues = np.linspace(mu - 3 * sigma, mu + 3 * sigma, len(values))
	yValues = []
	for x in xValues:
		y = (1 / ((2 * math.pi * sigma)**0.5)) * math.exp(-((x - mu) ** 2 / (2 * variance)))
		yValues.append(y)

	fig, ax = plt.subplots()
	textstr = '\n'.join((
		"$\\mu=%.5f$" % mu,
		"median=%.5f" % median,
		"$\\sigma=%.8f$" % sigma))
	boxProperties = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
	ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14, verticalalignment='top', bbox=boxProperties)

	ax.plot(xValues, yValues)
	plt.title("Theoretische Normalverteilung (n = %d)" % len(values))
	plt.ylabel("Anzahl")
	plt.xlabel("Verteilung (Messwerte)")
	plt.show()


def bootstrap(samples: List[float], confidence: float = 2.5, repeats: int = 10000, showGraph: bool = False, getData: bool = False):
	npSamples = np.array(samples)
	bootMeans = []
	for _ in range(10000):
		bootSample = np.random.choice(npSamples, replace=True, size=1000)
		bootMean = np.mean(bootSample)
		bootMeans.append(bootMean)

	npBootMeans = np.array(bootMeans)

	bootMeans = np.mean(npBootMeans)

	stdError = np.std(npBootMeans)
	confidenceInterval = np.percentile(npBootMeans, [confidence, 100 - confidence])

	if getData:
		return npBootMeans, confidenceInterval

	if showGraph:
		fig, ax = plt.subplots()
		textstr = '\n'.join((
			"std=%.8f" % stdError,
			"interval=[",
			"  %.7f," % confidenceInterval[0],
			"  %.7f]" % confidenceInterval[1]))
		boxProperties = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
		ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14, verticalalignment='top', bbox=boxProperties)

		plt.hist(npBootMeans)
		plt.axvline(confidenceInterval[0], color="red", linewidth=2)
		plt.axvline(confidenceInterval[1], color="red", linewidth=2)
		plt.title("Bootstrap Verteilung (n = %d)" % repeats)
		plt.ylabel("Anzahl")
		plt.xlabel("Verteilung (Messwerte)")
		plt.show()

	return stdError, confidenceInterval


def bootstrapAll(comType: CommunicationType, confidence: float = 2.5, repeats: int = 10000):
	with MeasurementFile() as mf:
		variances = mf.getAvailableVarianceMeasurements(CommunicationType.MULTIPROCESSING)

		stdTab = MeasurementTable(OPERATION_COUNTS, TRANSFER_SIZES)
		ci1Tab = MeasurementTable(OPERATION_COUNTS, TRANSFER_SIZES)
		ci2Tab = MeasurementTable(OPERATION_COUNTS, TRANSFER_SIZES)
		for opCount, tSize in product(OPERATION_COUNTS, TRANSFER_SIZES):
			variance = variances[opCount][tSize]
			std, ci = bootstrap(variance, confidence, repeats)

			stdTab.insert(opCount, tSize, std)
			ci1Tab.insert(opCount, tSize, ci[0])
			ci2Tab.insert(opCount, tSize, ci[1])

		mf.addBootstrapResults(comType, stdTab.export(), ci1Tab.export(), ci2Tab.export())


class DataVisualizer:

	def __init__(self):
		self.data = {}
		self.count = 0

	def addData(self, comType: CommunicationType):
		self.count += 1
		propCycle = plt.rcParams['axes.prop_cycle']
		colors = propCycle.by_key()['color']
		indeces = {
			CommunicationType.BASIC: 0,
			CommunicationType.THREADING: 1,
			CommunicationType.ASYNCIO: 2,
			CommunicationType.MULTIPROCESSING: 3,
		}
		with MeasurementFile() as mf:
			variances = mf.getAvailableVarianceMeasurements(comType)
			measurements = mf.getAvailableMeasurements(comType, "Final")
			self.data[comType] = {
				"measurements": measurements,
				"variances": variances,
				"color": colors[indeces[comType]],
			}

	def showHist(self, opCount: int, tSize: int, showLine: bool = False):
		index = 0
		for comType, data in self.data.items():
			bootMeans, confidence = bootstrap(data["variances"][opCount][tSize], getData=True)

			plt.hist(bootMeans, label=comType.value, color=data["color"])
			if showLine:
				plt.axvline(confidence[0], color=data["color"], linewidth=2)
				# plt.axvline(confidence[1], color="red", linewidth=2)
			index += 1

		plt.title("Bootstrap Verteilung (%s, %s)" % (opCount, tSize))
		plt.ylabel("Anzahl")
		plt.xlabel("Messzeit in s (Verteilung)")
		plt.legend(loc='upper right')
		plt.show()

	def showBars(self, opCount: int = None, tSize: int = None):
		fig, ax = plt.subplots()
		print(opCount, tSize)
		count = len(OPERATION_COUNTS) * len(TRANSFER_SIZES)
		if opCount:
			count = len(OPERATION_COUNTS)
		elif tSize:
			count = len(TRANSFER_SIZES)
		X = np.arange(count)
		width = 0.8 / self.count
		index = 0
		for comType, data in self.data.items():
			plotData = []
			if opCount:
				for s in TRANSFER_SIZES:
					plotData.append(data["measurements"][opCount][s])
			elif tSize:
				for c in OPERATION_COUNTS:
					plotData.append(data["measurements"][c][tSize])
			else:
				for s, c in product(TRANSFER_SIZES, OPERATION_COUNTS):
					plotData.append(data["measurements"][c][s])

			ax.bar(X + width * index, plotData, width=width, label=comType.value, color=data["color"])
			index += 1

		xTicks = []
		letterMap = {}
		letter, index = 65, 1
		for c in OPERATION_COUNTS:
			index = 1
			if opCount is not None and opCount != c:
				continue
			for s in TRANSFER_SIZES:
				if tSize is not None and tSize != s:
					continue
				name = "%s%s" % (chr(letter), index)
				xTicks.append(name)
				letterMap[name] = (s, c)
				index += 1
			letter += 1

		letterText = "Name\tDatengröße\tBerechnungen\n"
		for name, (tSize, opCount) in letterMap.items():
			letterText += "%s:\t%s\t\t%s\n" % (name, tSize, opCount)
		print(letterText)

		plt.xticks(X + (width / 2) * (self.count - 1), xTicks)
		plt.ylabel("Messzeit in s")
		plt.title("Messergebnisse")
		plt.legend(loc='best')
		plt.show()

	def show3dBars(self):
		fig = plt.figure(figsize=(5, 6))
		# fig = plt.figure()
		ax = fig.add_subplot(111, projection='3d')

		width = 0.8 / min(self.count, 2)

		index = 0
		legendNames = []
		legendColors = []
		for comType, data in self.data.items():
			values = []
			for s, c in product(TRANSFER_SIZES, OPERATION_COUNTS):
				values.append(data["measurements"][c][s])

			_x = np.arange(len(OPERATION_COUNTS))
			_y = np.arange(len(TRANSFER_SIZES))
			_xx, _yy = np.meshgrid(_x, _y)
			x, y = _xx.ravel(), _yy.ravel()

			top = np.array(values)
			bottom = np.zeros_like(top)
			depth = width

			xOffset = 0
			if index == 1 or index == 3:
				xOffset = width
			yOffset = 0
			if index > 1:
				yOffset = width

			ax.bar3d(x + xOffset, y + yOffset, bottom, width * 0.6, depth * 0.6, top, shade=True, color=data["color"])
			legendNames.append(comType.value)
			legendColors.append(plt.Rectangle((0, 0), 1, 1, fc=data["color"]))
			index += 1

		plt.yticks(np.arange(0.5, 4, 1), range(1, 5))
		plt.ylabel("Berechnungen")
		plt.xticks(np.arange(0.5, 4, 1), ["A", "B", "C", "D"])
		plt.xlabel("Datengröße")
		plt.title("Messergebnisse")
		plt.legend(legendColors, legendNames, loc='upper right', bbox_to_anchor=(1, 0))
		plt.show()


def showOperationProgression():
	opCounts = np.linspace(10**4, 10**7, 25)

	for comType in [CommunicationType.BASIC, CommunicationType.THREADING, CommunicationType.MULTIPROCESSING]:

		with MeasurementFile() as mf:
			data = mf.getSimpleMeasurement("CountProgress [%s]" % comType.value)

			plt.plot(opCounts, data, label=comType.value)

	for x in OPERATION_COUNTS:
		plt.axvline(x, color="red", linewidth=2)

	plt.xlabel("Berechnungen")
	plt.ylabel("Messzeit in s")
	plt.title("Unterschiedliche Berechnungen bei gleicher Größe (100)")
	plt.legend(loc='best')
	plt.show()


def showDeviceCountProgression(opCount: int = 10000, tSize: int = 100):
	fig = plt.figure(figsize=(8, 6))
	ax = fig.add_subplot(111)
	propCycle = plt.rcParams['axes.prop_cycle']
	colors = propCycle.by_key()['color']
	indeces = {
		CommunicationType.BASIC: 0,
		CommunicationType.THREADING: 1,
		CommunicationType.ASYNCIO: 2,
		CommunicationType.MULTIPROCESSING: 3,
	}
	width = 0.8 / (3)
	X = np.arange(5)

	xTicks = None

	with MeasurementFile() as mf:
		for i, comType in enumerate([CommunicationType.THREADING]):
			for index, totalLoad in enumerate([1, 10, 50]):
				result = mf.getAvailableMeasurements_new(comType, totalLoad)
				xList = []
				yList = []
				for deviceCount, data in result.items():
					xList.append(deviceCount)
					# yList.append(data[opCount][tSize])

				xList = list(map(lambda x: int(x), xList))
				xList.sort()
				for x in xList:
					yList.append(result[str(x)][opCount][tSize])

				if xTicks is None:
					xTicks = xList

				offset = i * (0.8 / 3)
				color = lighten_color(colors[indeces[comType]], 0.4 + index * 0.3)
				# color = colors[indeces[comType]]
				ax.bar(X + offset + width * index, yList, width=width, label="%s [%s]" % (comType.value, totalLoad), color=color)

	# plt.xticks(X + width * 4, xTicks)
	plt.xticks(X + (width / 2) * 2, xTicks)
	plt.xlabel("Geräteanzahl")
	plt.ylabel("Messzeit in s")
	plt.title("Abhängigkeit von Geräteanzahl und insgesammter Prüflast")

	plt.figtext(0.81, 0.86, "Typ und Gesammte Prüflast", fontsize=12, ha="center")
	plt.figtext(0.81, 0.3, "Operationen: %s\nDatengröße: %s" % (opCount, tSize), ha="center", fontsize=12, bbox={"facecolor": "gray", "alpha": 0.5, "pad": 5})
	plt.subplots_adjust(left=0.1, bottom=0.1, right=0.65, top=0.9)
	plt.legend(loc='best', bbox_to_anchor=(1, 0.95))
	plt.show()


if __name__ == "__main__":
	# showDeviceCountProgression()
	# showDeviceCountProgression(10000000, 100000)
	showOperationProgression()

	vis = DataVisualizer()
	vis.addData(CommunicationType.MULTIPROCESSING)
	vis.addData(CommunicationType.ASYNCIO)
	vis.addData(CommunicationType.THREADING)
	vis.addData(CommunicationType.BASIC)

	vis.showBars(opCount=10000000)
	# vis.show3dBars()

	# vis.showHist(10000, 100, True)
	# vis.showHist(10000000, 100000, True)

	# bootstrapAll(CommunicationType.MULTIPROCESSING)
	# with MeasurementFile() as mf:
	# 	comType = CommunicationType.THREADING
	# 	variances = mf.getAvailableVarianceMeasurements(comType)
	# 	v = variances[10000][100]

	# 	# print(len(v))
	# 	# bootstrap(v)

	# 	# showTheoreticalDistribution(v)
	# 	showValuePlot(v, comType)
	# 	showQQPlot(v, comType)
