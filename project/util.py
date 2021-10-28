from subprocess import call
import subprocess
import os
from enum import Enum
from contextlib import contextmanager
import sys
import math


class ListEnum(Enum):
	@classmethod
	def toList(cls):
		return list(map(lambda c: c.value, cls))


def runCommand(command: str):
	subprocess.call(command)


def runRootCommand(command: str):
	os.system("sudo " + command)


def runCommandIn(command: str, location: str):
	process = subprocess.Popen(command, shell=True, cwd=location)
	process.wait()


def runRootCommandIn(command: str, location: str):
	process = subprocess.Popen("sudo " + command, shell=True, cwd=location)
	process.wait()


def runCommandWithOutput(command: str):
	process = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
	output = ""
	for c in iter(lambda: process.stdout.read1(1), b''):
		output = c.decode("utf-8")
	process.stdout.close()
	process.wait()
	return output


def printProgress(message, maxC, curC):
	if curC > maxC:
		return
	if curC % (maxC / 10000) > 1 and maxC != curC:
		return
	count = math.floor(20 * (curC / maxC))
	smallCount = int(200 * (curC / maxC)) % 10
	print(
		message + "   [" + "▉" * count + " " * (20 - count) + "]   " + ">" * smallCount + " " * (10 - smallCount) + "   (" + str(curC) + "/" + str(maxC) + ")",
		end="\r"
	)
	if maxC == curC:
		print(message + "   [" + "▉" * 20 + "]   DONE")


# source: http://thesmithfam.org/blog/2012/10/25/temporarily-suppress-console-output-in-python/
@contextmanager
def suppress_stdout():
	with open(os.devnull, "w") as devnull:
		old_stdout = sys.stdout
		sys.stdout = devnull
		try:
			yield
		finally:
			sys.stdout = old_stdout
