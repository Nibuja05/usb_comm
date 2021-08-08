
default: status

status:
	python3.8 project/setup/create_devices.py status

test:
	sudo python3.8 project/tests/test_all.py

start:
	sudo python3.8 project/setup/create_devices.py create
	sudo python3.8 project/setup/create_devices.py start

clear:
	sudo python3.8 project/setup/create_devices.py clear