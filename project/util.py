from subprocess import call
import subprocess
import os
from enum import Enum


class ListEnum(Enum):
	@classmethod
	def toList(cls):
		return list(map(lambda c: c.value, cls))


def runCommand(command):
	subprocess.call(command)


def runRootCommand(command):
	# print("[%s]" % command)
	os.system("sudo " + command)


def runCommandWithOutput(command):
	process = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
	output = ""
	for c in iter(lambda: process.stdout.read1(1), b''):
		output = c.decode("utf-8")
	return output
