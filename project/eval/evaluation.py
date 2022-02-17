import __init__
from typing import Dict, List, Tuple
import math
import sys
from functools import reduce
from itertools import product
import numpy as np
import statsmodels.api as sm
import scipy.stats as stats
import pylab
import matplotlib.pyplot as plt

from eval.storage import MeasurementFile, MeasurementTable
from core.usb_util import CommunicationType
from eval.measurement import OPERATION_COUNTS, TRANSFER_SIZES, DEVICE_COUNTS, LOADS_PER_DEVICE


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


def getFirstDictValue(dict: Dict):
	return list(dict.values())[0]


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

	def addData(self, comType: CommunicationType, useOld = False):
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
			newMeasurements = {}

			for deviceCount, loadPerDevice in product(DEVICE_COUNTS, LOADS_PER_DEVICE):
				totalLoads = deviceCount * loadPerDevice
				newMeasurements[totalLoads] = mf.getAvailableMeasurements_new(comType, totalLoads, useOld and comType==CommunicationType.ASYNCIO)
			newMeasurements[50] = mf.getAvailableMeasurements_new(comType, 50)
			newMeasurements[10] = mf.getAvailableMeasurements_new(comType, 10)

			self.data[comType] = {
				"measurements": measurements,
				"newMeasurements": newMeasurements,
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

	def showBars(self, opCount: int = None, tSize: int = None, logScale = True, showTable = False):
		fig, ax = plt.subplots()
		count = len(OPERATION_COUNTS) * len(TRANSFER_SIZES)
		if opCount:
			count = len(TRANSFER_SIZES)
		elif tSize:
			count = len(OPERATION_COUNTS)
		X = np.arange(count)
		width = 0.8 / self.count
		index = 0
		for comType, data in self.data.items():
			plotData = []
			if opCount:
				for s in TRANSFER_SIZES:
					plotData.append(data["newMeasurements"][32][32][opCount][s])
			elif tSize:
				for c in OPERATION_COUNTS:
					plotData.append(data["newMeasurements"][32][32][c][tSize])
			else:
				for s, c in product(TRANSFER_SIZES, OPERATION_COUNTS):
					plotData.append(data["newMeasurements"][32][32][c][s])

			ax.bar(X + width * index, plotData, width=width, label=comType.value, color=data["color"])
			index += 1

		xTicks = []
		letterMap = {}
		index1, index2 = 1, 1
		tableData = []
		for c in OPERATION_COUNTS:
			index2 = 1
			if opCount is not None and opCount != c:
				continue
			for s in TRANSFER_SIZES:
				if tSize is not None and tSize != s:
					continue
				name = "%s_%s" % (index1, index2)
				xTicks.append(name)
				letterMap[name] = (s, c)
				index2 += 1

				tableData.append((name, c, s))
			index1 += 1

		letterText = "Name\tDatengröße\tBerechnungen\n"
		for name, (tSize, opCount) in letterMap.items():
			letterText += "%s:\t%s\t\t%s\n" % (name, tSize, opCount)

		if logScale:
			ax.set_yscale("log")
		plt.xticks(X + (width / 2) * (self.count - 1), xTicks, rotation=45)
		plt.ylabel("Messzeit in s")
		plt.title("Messergebnisse (Berechnungsanzahl, Datengröße)")
		plt.legend(loc='best')
		plt.show()

		if not showTable:
			return

		print(letterText)

		ig, ax = plt.subplots()

		# hide axes
		fig.patch.set_visible(False)
		ax.axis('off')
		ax.axis('tight')

		ax.table(cellText=tableData, colLabels=["Benennung", "Berechnungsanzahl", "Datengröße"], loc='center')

		# fig.tight_layout()

		plt.show()

	
	def showLoadCountBars(self, opCount=None, tSize=None):
		fig, ax = plt.subplots()

		if not opCount:
			opCount = OPERATION_COUNTS[0]
		if not tSize:
			tSize = TRANSFER_SIZES[0]

		totalLoads = list(dict.fromkeys([d * l for d,l in product(DEVICE_COUNTS, LOADS_PER_DEVICE)]))

		count = len(totalLoads)
		X = np.arange(count)
		width = 0.8
		index = 0
		for comType, data in self.data.items():
			plotData = []
			
			for totalLoad in totalLoads:
				plotData.append(getFirstDictValue(data["newMeasurements"][totalLoad])[opCount][tSize])

			ax.bar(X + width * index, plotData, width=width, label=comType.value, color=data["color"])
			index += 1

		plt.xticks(X + (width / 2) * (self.count - 1), totalLoads)
		plt.xlabel("Anzahl von Prüflasten")
		plt.ylabel("Messzeit in s")
		plt.title("Messergebnisse bei unterschiedlicher Anzahl von Prüflasten")
		plt.show()

	def showDeviceCountBars(self, opCount=None, tSize=None):
		fig, ax = plt.subplots()

		if not opCount:
			opCount = OPERATION_COUNTS[0]
		if not tSize:
			tSize = TRANSFER_SIZES[0]

		count = len(DEVICE_COUNTS)
		X = np.arange(count)
		width = 0.8
		index = 0
		for comType, data in self.data.items():
			plotData = []
			
			for count in DEVICE_COUNTS:
				plotData.append(data["newMeasurements"][count][count][opCount][tSize])

			ax.bar(X + width * index, plotData, width=width, label=comType.value, color=data["color"])
			index += 1

		plt.xticks(X + (width / 2) * (self.count - 1), DEVICE_COUNTS)
		plt.xlabel("Anzahl von Geräten")
		plt.ylabel("Messzeit in s")
		plt.title("Messergebnisse (Berechnungsanzahl=%s, Datengröße=%s)" % (opCount, tSize))
		plt.show()

	def showDeviceCountBars_all(self):
		fig, ax = plt.subplots()

		count = len(DEVICE_COUNTS)
		X = np.arange(4)
		width = 0.8 / count

		for _, data in self.data.items():
			index = 0
			
			for count in DEVICE_COUNTS:
				plotData = []
				for opCount, tSize in product([OPERATION_COUNTS[0], OPERATION_COUNTS[-1]],[TRANSFER_SIZES[0], TRANSFER_SIZES[-1]]):
					plotData.append(data["newMeasurements"][count][count][opCount][tSize])

				color = lighten_color(data["color"], 1 - index * 0.12)
				ax.bar(X + width * index, plotData, width=width, label="%s Geräte" % count, color=color)
				index += 1

		ticks = []
		for opCount, tSize in product([OPERATION_COUNTS[0], OPERATION_COUNTS[-1]],[TRANSFER_SIZES[0], TRANSFER_SIZES[-1]]):
			ticks.append("c=%s\nn=%s" % (opCount, tSize))

		plt.xticks(X + (width / 2) * (4 - 1), ticks)
		plt.yscale("log")
		# plt.xlabel("Anzahl von Prüflasten")
		plt.ylabel("Messzeit in s")
		plt.title("Messergebnisse (Berechnungsanzahl c, Datengröße n)")
		plt.legend(loc="best")
		plt.show()

	def showScatterPlot(self, deviceCount: int = None, loadsPerDevice: int = None, opCount: int = None, tSize: int = None):
		fig, ax = plt.subplots()

		mode = "operations"
		if opCount and not tSize:
			mode = "size"

		minArea = 3
		maxArea = 20

		opCountAreaTable = {
			10000: minArea, 
			100000: minArea * 5, 
			1000000: minArea * 10, 
			10000000: minArea * 20,
		}
		transferSizeAreaTable = {
			100: minArea,
			1000: minArea * 5,
			10000: minArea * 10,
			100000: minArea *20,
		}


		index = 0
		scatter = None

		for comType, data in self.data.items():
			offsetMult = 0.03
			if not deviceCount:
				offsetMult = 0.15
			slightOffset = (-1.5 + index) * offsetMult
			index += 1

			x = []
			y = []
			areas = []
			colors = []
			color = data["color"]

			if not deviceCount:
				if not loadsPerDevice:
					loadsPerDevice = 1
				for d in DEVICE_COUNTS:
					totalLoad = d * loadsPerDevice

					if not opCount:
						if not tSize:
							tSize = TRANSFER_SIZES[-1]
						for c in OPERATION_COUNTS:
							x.append(d + slightOffset)
							y.append(data["newMeasurements"][totalLoad][d][c][tSize])
							colors.append(color)
							areas.append(opCountAreaTable[c])

					elif not tSize:
						if not opCount:
							opCount = OPERATION_COUNTS[-1]
						for t in TRANSFER_SIZES:
							# if totalLoad == 128:
							# 	print(comType.value, t, data["newMeasurements"][totalLoad][d][opCount][t])
							x.append(d + slightOffset)
							y.append(data["newMeasurements"][totalLoad][d][opCount][t])
							colors.append(color)
							areas.append(transferSizeAreaTable[t])

			elif not loadsPerDevice:
				if not deviceCount:
					deviceCount = 32
				for l in LOADS_PER_DEVICE:
					totalLoad = deviceCount * l

					if not opCount:
						if not tSize:
							tSize = TRANSFER_SIZES[-1]
						for c in OPERATION_COUNTS:
							x.append(l + slightOffset)
							y.append(data["newMeasurements"][totalLoad][deviceCount][c][tSize])
							colors.append(color)
							areas.append(opCountAreaTable[c])

					elif not tSize:
						if not opCount:
							opCount = OPERATION_COUNTS[0]
						for t in TRANSFER_SIZES:
							x.append(l + slightOffset)
							y.append(data["newMeasurements"][totalLoad][deviceCount][opCount][t])
							colors.append(color)
							areas.append(transferSizeAreaTable[t])

			scatter = ax.scatter(x,y, s=areas, c=colors, label=comType.value)

		legend1 = plt.legend(loc="upper right", framealpha=0.4, bbox_to_anchor=(0.9, 1))
		ax.add_artist(legend1)

		mod2 = ""
		comTypeCount = self.count

		if scatter:
			handles, _ = scatter.legend_elements(prop="sizes", alpha=0.6)
			if mode == "operations":
				labels = OPERATION_COUNTS
				plt.legend(handles, labels, loc="upper right", title="Operationsanzahl", framealpha=0.4, bbox_to_anchor=(0.9, 0.95 - comTypeCount * 0.05))
				mod2 = "Datengröße: %s" % tSize
			else:
				labels = TRANSFER_SIZES
				plt.legend(handles, labels, loc="upper right", title="Datengröße", framealpha=0.4, bbox_to_anchor=(0.9, 0.95 - comTypeCount * 0.05))
				mod2 = "%s Operationen" % opCount

		mod1 = ""
		if not deviceCount:
			plt.xlabel("Geräteanzahl")
			plt.xticks(DEVICE_COUNTS)
			mod1 = "pro Gerät: %s" % loadsPerDevice
		else:
			plt.xlabel("Prüflasten pro Gerät")
			plt.xticks(LOADS_PER_DEVICE)
			mod1 = "für %s Geräte" % deviceCount
		plt.ylabel("Messzeit in s")
		plt.title("Messergebnisse (%s; %s)" % (mod1, mod2))
		plt.show()

	def showVarCoefs(self):
		fig,ax  = plt.subplots()

		for comType, data in self.data.items():
			color = data["color"]
			x = []
			y = []
			areas = []

			for opCount, tSize in product(OPERATION_COUNTS, TRANSFER_SIZES):
				variances = data["variances"][opCount][tSize]

				# Varianzkoeffizient
				std = np.std(variances)
				mean = np.mean(variances)
				varCoef = std / mean
				x.append(mean)
				y.append(varCoef)

				area = OPERATION_COUNTS.index(opCount) * TRANSFER_SIZES.index(tSize) * 6
				areas.append(area)

			ax.scatter(x, y, c=[color] * len(x), s=areas, label=comType.value)
		
		plt.legend(loc="best", framealpha=0.6)
		plt.xlabel("Mittelwert")
		plt.ylabel("Varianzkoeffizient")
		plt.title("Durchschnittliche Abweichung von Messwerten")
		plt.show()

	def showTotalLoadScatter(self, totalLoads = 50):
		fig,ax  = plt.subplots()

		index = 0

		for comType, data in self.data.items():
			offsetMult = 0.15
			slightOffset = (-1.5 + index) * offsetMult
			index += 1

			color = data["color"]
			x = []
			y = []
			areas = []

			for d in DEVICE_COUNTS:
				if d == 2:
					continue
				measurements = data["newMeasurements"][totalLoads][d]

				for opCount, tSize in product(OPERATION_COUNTS, TRANSFER_SIZES):
					x.append(d + slightOffset)
					y.append(measurements[opCount][tSize])

					area = OPERATION_COUNTS.index(opCount) * TRANSFER_SIZES.index(tSize) * 6
					areas.append(area)

			ax.scatter(x, y, c=[color] * len(x), s=areas, label=comType.value)
		
		# plt.legend(loc="best")
		plt.legend(loc="upper right", framealpha=0.4, bbox_to_anchor=(0.93, 1))
		plt.xlabel("Geräteanzahl")
		plt.xticks([1,4,8,16,32])
		plt.ylabel("Messzeit in s")
		plt.title("Messergebnisse für %s Prüflasten" % totalLoads)
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

	def generateSpeedupTable(self):

		lines = {}

		if not CommunicationType.BASIC in self.data:
			print("No basic data found for comparison!")
			return

		for comType, data in self.data.items():
			if comType is CommunicationType.BASIC:
				continue

			for d in DEVICE_COUNTS:
				measurement = data["newMeasurements"][d][d]

				for opCount, tSize in product(OPERATION_COUNTS, TRANSFER_SIZES):
					
					# syntax: ... & ... & ... \\
					# \hline
					value = measurement[opCount][tSize]
					origValue = self.data[CommunicationType.BASIC]["newMeasurements"][d][d][opCount][tSize]
					lines.setdefault((opCount, tSize), {}).setdefault(d, []).append(origValue / value)

		markCell = lambda x: '\cellcolor{green!35}%s' % x
		best = {}
		for (opCount, tSize), devices in lines.items():
			for d, (mVal, tVal) in devices.items():
				curVal,_,_,_ = best.setdefault(d, (0, opCount, tSize, ""))
				if mVal > tVal:
					if mVal > curVal:
						best[d] = (mVal, opCount, tSize, 0)
				else:
					if tVal > curVal:
						best[d] = (tVal, opCount, tSize, 1)

		for (opCount, tSize), devices in lines.items():
			# curVal = best.setdefault()
			line = "%s & %s & " % (opCount, tSize)
			line += " & ".join(
				[" & ".join(
					[markCell("%.1f" % y) if 
						best[d][1] == opCount and 
						best[d][2] == tSize and 
						best[d][3] == i 
					else "%.1f" % y for i,y in enumerate(x)]
				) for d, x in devices.items()]
			)
			line += r" \\"
			print(line)


def showOperationProgression(showLog=False):
	opCounts = np.linspace(10**4, 10**7, 25)
	fig, ax = plt.subplots()

	propCycle = plt.rcParams['axes.prop_cycle']
	colors = propCycle.by_key()['color']
	indeces = {
		CommunicationType.BASIC: 0,
		CommunicationType.THREADING: 1,
		CommunicationType.ASYNCIO: 2,
		CommunicationType.MULTIPROCESSING: 3,
	}

	for comType in [CommunicationType.BASIC]:

		with MeasurementFile() as mf:
			data = mf.getSimpleMeasurement("CountProgress [%s]" % comType.value)
			
			ax.plot(opCounts, data, label=comType.value, color=colors[indeces[comType]])

	for x in OPERATION_COUNTS:
		ax.axvline(x, color="black", linewidth=1, linestyle=":")

	if showLog:
		ax.set_xscale("log")
	plt.xlabel("Berechnungen")
	plt.ylabel("Messzeit in s")
	plt.title("Unterschiedliche Berechnungsanzahl bei gleicher Größe (=100)")
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


def showBoxplot():
	with MeasurementFile() as mf:
		dataList = []
		# for comType in CommunicationType:
		# 	data = mf.getAvailableVarianceMeasurements(comType)[100000][1000]
		# 	dataList.append(data)
		for count in OPERATION_COUNTS:
			data = mf.getAvailableVarianceMeasurements(CommunicationType.MULTIPROCESSING)[count][1000]
			dataList.append(data)
		fig, ax = plt.subplots()
		ax.set_title('Basic Plot')
		ax.boxplot(dataList)
		ax.set_yscale("log")
		# ax.set_xticklabels(CommunicationType.toList())
		ax.set_xticklabels(OPERATION_COUNTS)
		plt.show()

	
def checkIdentical_T(type1: CommunicationType, type2: CommunicationType, alpha=0.01, altAsyncio=False):
	with MeasurementFile() as mf:
		measure1 = mf.getAvailableVarianceMeasurements(type1, altAsyncio and type1 == CommunicationType.ASYNCIO)
		measure2 = mf.getAvailableVarianceMeasurements(type2, altAsyncio and type2 == CommunicationType.ASYNCIO)

		# data = []
		maxCount = 0
		rejectCount = 0

		for opCount, tSize in product(OPERATION_COUNTS, TRANSFER_SIZES):
			# tSize = TRANSFER_SIZES[0]
			# opCount = OPERATION_COUNTS[0]

			# print(measure1.keys(), tSize)
			data1 = measure1[opCount][tSize]
			data2 = measure2[opCount][tSize]

			# Varianzkoeffizient
			var1 = np.var(data1)
			var2 = np.var(data2)
			mean1 = np.mean(data1)
			mean2 = np.mean(data2)
			varCoef1 = var1 / mean1
			varCoef2 = var2 / mean2

			res = stats.ttest_ind(a=data1, b=data2, equal_var=False)
			# res = stats.ks_2samp(data1, data2)
			maxCount += 1

			if res.pvalue >= alpha / len(data1):
				rejectCount += 1
				# print("\n%s,%s: %s" % (opCount, tSize, res.pvalue))

				# data.append(data1)
				# data.append(data2)
				# fig, ax = plt.subplots()
				# ax.boxplot([data1, data2])
				# plt.show()
		
		print("%s / %s abgelehnt" % (rejectCount, maxCount))
		# ax.boxplot(data)
		# plt.show()




if __name__ == "__main__":
	# checkIdentical_T(CommunicationType.THREADING, CommunicationType.MULTIPROCESSING, alpha=0.05)
	# checkIdentical_T(CommunicationType.BASIC, CommunicationType.ASYNCIO, alpha=0.01, altAsyncio=True)
	# checkIdentical_T(CommunicationType.THREADING, CommunicationType.ASYNCIO, alpha=0.01, altAsyncio=False)
	# sys.exit()

	# showDeviceCountProgression()
	# showDeviceCountProgression(10000000, 100000)
	# showOperationProgression()

	vis = DataVisualizer()
	# vis.addData(CommunicationType.BASIC)
	# vis.addData(CommunicationType.THREADING)
	vis.addData(CommunicationType.MULTIPROCESSING)
	# vis.addData(CommunicationType.ASYNCIO, True)

	# vis.generateSpeedupTable()
	# vis.showLoadCountBars()
	# vis.showVarCoefs()
	# vis.showDeviceCountBars(opCount=OPERATION_COUNTS[0], tSize=TRANSFER_SIZES[0])
	# vis.showDeviceCountBars_all()
	# vis.showBars(logScale=False)
	# vis.showTotalLoadScatter(1)
	# vis.showTotalLoadScatter(10)
	# vis.showTotalLoadScatter(50)

	vis.showBars(logScale=False)
	# vis.showScatterPlot(tSize=100000)
	# vis.showScatterPlot(opCount=10000000)
	# vis.showScatterPlot(loadsPerDevice=4, opCount=10000000, comTypes=[CommunicationType.BASIC, CommunicationType.ASYNCIO])
	# vis.showScatterPlot(loadsPerDevice=4, opCount=10000000, comTypes=[CommunicationType.THREADING, CommunicationType.ASYNCIO])
	# vis.showScatterPlot(loadsPerDevice=4, opCount=10000)
	# vis.showScatterPlot(loadsPerDevice=4, opCount=100000)
	# vis.showScatterPlot(loadsPerDevice=4, opCount=1000000)
	# vis.showScatterPlot(loadsPerDevice=4, opCount=10000000)
	# vis.showScatterPlot(deviceCount=1)
	# vis.showScatterPlot(deviceCount=4)
	# vis.showScatterPlot(deviceCount=8)
	# vis.showScatterPlot(deviceCount=16)
	# vis.showScatterPlot(deviceCount=32)
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
