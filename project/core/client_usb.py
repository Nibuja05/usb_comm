import os
import io


class USB_Client:

	def __init__(self, id):
		self.id = id
		self.active = False
		self.deviceFile = "/dev/ttyGS%s" % self.id

	def activate(self):
		if self.active:
			print("Already active!")
			return
		self.active = True
		self.listen()

	def deactivate(self):
		self.active = False
		raise Exception("DEACTIVATE")

	def listen(self):
		try:
			f = io.TextIOWrapper(io.FileIO(os.open(self.deviceFile, os.O_RDWR), "r+"))
			for line in iter(f.readline, None):
				print(line.strip())
		except Exception as e:
			print(e)
		finally:
			f.close()



# def echo():
# 	deviceFile = "/dev/ttyGS0"
# 	f = io.TextIOWrapper(io.FileIO(os.open(deviceFile, os.O_RDWR), "r+"))

# 	for line in iter(f.readline, None):
# 		print(line.strip())
# 		f.write("T\n")

	# while True:
	# 	print("Test")
	# 	content = f.read(1)
	# 	print(content)
	# 	time.sleep(0.1)
	
	# for i in range(1000):
	# 	f.write("T%s\n" % i)
	# 	time.sleep(0.5)
		

# echo()
