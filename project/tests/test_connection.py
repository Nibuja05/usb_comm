import usb.core as core


def main():
	testUSBConnections()


def testUSBConnections():
	print("Teste USB Verbindungen...")
	devs = core.find(idVendor=0x1d6b, idProduct=0x0104, find_all=True)
	count = 0
	for dev in devs:
		count += 1
		# print(dev.is_kernel_driver_active(0))
	print("Verbinding zu %s Geräten möglich!" % count)
	return count


if __name__ == '__main__':
	main()
