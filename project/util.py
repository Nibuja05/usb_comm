from subprocess import call
import subprocess
import os

def runCommand(command: str):
	subprocess.call(command)


def runRootCommand(command: str):
	# print("[%s]" % command)
	os.system("sudo " + command)

def runCommandWithOutput(command: str):
	process = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
	output = ""
	for c in iter(lambda: process.stdout.read1(1), b''):
		output = c.decode("utf-8")
	return output