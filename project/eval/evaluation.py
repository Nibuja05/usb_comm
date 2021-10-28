import __init__
from typing import List
import math
from functools import reduce
import numpy as np
import statsmodels.api as sm
import pylab
import matplotlib.pyplot as plt

from eval.storage import MeasurementFile
from core.usb_util import CommunicationType


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


def showTheoreticalDistribution(values: List[float]):
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


if __name__ == "__main__":
	with MeasurementFile() as mf:
		variances = mf.getAvailableVarianceMeasurements(CommunicationType.ASYNCIO)
		v = variances[10][10]

		# showTheoreticalDistribution(v)
		showValuePlot(v)
		showQQPlot(v)
