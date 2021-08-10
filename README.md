# Evaluierung von parallelem Zugriff auf mehrere USB-Geräte in Python

Git-Projekt zur Bachelorarbeit

## How To

Die wichtigsten Funktionen können direkt über `make` ausgeführt werden:

- `make status`: Status report über maximale Anzahl von dummy_hcd Geräten und derzeitige Anzahl von aktiven Geräten
- `make test`: Testdurchlauf für USB-Geräte
- `make start`: Erstellt USB-Geräte
- `make clear`: Entfernt erstelle Geräte

### Verwenung der Geräte

Um die simulierten Geräte außerhalb des Tests zu verwenden, müssen folgende Schritte beachtet werden:
- Geräte erstellen und aktivieren (`make start`)
- Host und Clients verwenden (siehe `core/usb_manager.py TestClientCommunication`)
  - Host und entsprechende Anzahl an Clients erstellen
  - Clients aktivieren
  - Befehle ausführen
  - Clients deaktivieren
- Geräte entfernen (`make clear`)

### Befehle

Jeder Befehl wird standartmäßg an alle Clients gesendet, es kann jedoch immer auch eine `id` angegeben werden um den Befehl nur für das angegebene Gerät auszuführen.

Zum Testen der Kommunikation existiert der Befehl `ping()`, welcher dann wahr ist, wenn alle Geräte (oder angegebenes) erfolgreich erreicht werden konnten.

Jegliche Kommunikation läuft über den Hauptbefehl `sendMessage(MsgCode)`. Alle anderen Befehle führen ebenfalls diesen Befehl aus und sind nur verkürzte Versionen. Das Gerät antwortet im Normalfall auf jeden Befehl mit einem Statuscode, welcher von `sendMessage` zurückgegeben wird. Sollen beliebige Daten an den Client gesendet werden, so muss *MsgCode.SEND* verwendet werden und die zu sendende Nachricht als zusätzlicher Parameter übergeben werden. Der Client verarbeitet dabei die erhaltenen Daten in `handleInput()`. Die Ausgabe des Clients kann jederzeit mit *MsgCode.RECV* erhalten werden und wird anstelle eines Statuscodes vom Client übertragen (und ist somit der Output von `sendMessage`).

Jeder Client hat seinen eigenen Thread, um Anfragen unabhängig voneinander zu empfangen und verarbeiten zu können. Gestoppt werden können die Clients entweder mit *MsgCode.STOP* oder einfacher mit dem Befehl `deactivate()`.

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
