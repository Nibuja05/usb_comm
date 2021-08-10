# Evaluierung von parallelem Zugriff auf mehrere USB-Geräte in Python

Git-Projekt zur Bachelorarbeit

## How To

Die wichtigsten Funktionen können direkt über `make` ausgeführt werden:

- `make status`: Status report über maximale Anzahl von dummy_hcd Geräten und derzeitige Anzahl von aktiven Geräten
- `make test`: Testdurchlauf für USB-Geräte
- `make start`: Erstellt USB-Geräte
- `make clear`: Entfernt erstelle Geräte

## Anderes

Benutzt command-line tool `gt`.

Falls nicht vorhanden, muss dies zunächst installiert werden:
```
git clone https://github.com/kopasiak/gt.git
cd gt/source
cmake -DCMAKE_INSTALL_PREFIX= .
make
make install
```

Sollte es Berechtigungsprobleme bei der Benutzung mit pyUSB geben, kann folgdende *udev* Regel helfen:

```
SUBSYSTEM=="usb", SUBSYSTEMS=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{idVendor}=="1d6b", ATTRS{idProduct}=="0104", GROUP="plugdev", MODE="0666"
```
