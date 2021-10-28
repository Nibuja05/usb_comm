
default: status

status:
	python3.8 project/setup/create_devices.py status

test:
	python3.8 project/tests/test_all.py

start:
	python3.8 project/setup/create_devices.py create
	python3.8 project/setup/create_devices.py start

create:
	python3.8 project/setup/create_devices.py create

restart:
	python3.8 project/setup/create_devices.py clear
	python3.8 project/setup/create_devices.py create
	python3.8 project/setup/create_devices.py start

clear:
	sudo python3.8 project/setup/create_devices.py clear