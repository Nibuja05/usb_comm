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


def showValuePlot(values: List[float]):
	values.sort()
	plt.plot(values)
	plt.title("Sortierte Messwerte")
	plt.ylabel("Messwerte")
	plt.xlabel("Index")
	plt.show()


def showQQPlot(values: List[float]):
	sm.qqplot(values, line='q')
	pylab.title("QQPlot (n = %d)" % len(values))
	pylab.show()


def showTheoreticalDistribution(values: List[float]) -> Tuple[float, Tuple[float, float]]:
	variance, sigma, median, mu = calculateStatisticValues(v)

	xValues = np.linspace(mu - 3 * sigma, mu + 3 * sigma, len(v))
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


def bootstrap(samples: List[float], confidence: float = 2.5, repeats: int = 10000, showGraph: bool = False):
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


if __name__ == "__main__":
	bootstrapAll(CommunicationType.MULTIPROCESSING)
	# with MeasurementFile() as mf:
	# 	variances = mf.getAvailableVarianceMeasurements(CommunicationType.MULTIPROCESSING)
	# 	v = variances[1000000][10000]

		# print(len(v))
		# bootstrap(v)

		# showTheoreticalDistribution(v)
		# showValuePlot(v)
		# showQQPlot(v)
