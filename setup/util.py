from subprocess import call
import subprocess
import os


def runCommand(command: str):
    subprocess.call(command)


def runRootCommand(command: str):
    print("[%s]" % command)
    os.system("sudo " + command)
