import __init__
import psutil
import os
from math import floor
from subprocess import PIPE
from typing import List

# from stress_cpu import stress

CLIENT_CORE_PERCENTAGE = 0.5
HOST_CORE_PERCENTAGE = 0.5


def limitToCores(start: int, end: int):
	coreList = createCoreList(start, end)
	p = psutil.Process(os.getpid())
	p.cpu_affinity(coreList)


def runCommandInCores(cmd: str, start: int, end: int):
	coreList = createCoreList(start, end)
	p = psutil.Popen(cmd.split(" "), stdout=PIPE)
	p.cpu_affinity(coreList)


def createCoreList(start: int, end: int = -1) -> List[int]:
	endIndex = (start if end < 0 else end) + 1
	endIndex = min(endIndex, getCpuCoreCount())
	return list(range(start, endIndex))


def getCpuCoreCount() -> int:
	return psutil.cpu_count()


def SetClientCores():
	maxClientCores = floor(getCpuCoreCount() * CLIENT_CORE_PERCENTAGE - 1)
	limitToCores(0, maxClientCores)


def SetHostCores():
	maxClientCores = floor(getCpuCoreCount() * CLIENT_CORE_PERCENTAGE - 1)
	maxHostCores = floor(getCpuCoreCount() * HOST_CORE_PERCENTAGE - 1)
	limitToCores(maxClientCores + 1, maxClientCores + maxHostCores + 1)


# Use carefully! (will also terminate itself)
def KillAllPythonProcesses():
	for p in psutil.process_iter(["pid", "name"]):
		print(p.info)
		if p.info["name"] == "python3.8":
			p.kill()


if __name__ == "__main__":
	print("Memory Manager!")
	# limitToCores(2, 3)
	# stress()
	KillAllPythonProcesses()
