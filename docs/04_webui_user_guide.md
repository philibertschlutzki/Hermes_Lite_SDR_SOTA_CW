# WebUI Benutzerhandbuch

Die WebUI ist bewusst minimal und smartphone-tauglich: Frequenz/Mode setzen und CW-Text/Makros senden. [file:1]

## Funktionen

- Frequency: Setzt die HL2-Frequenz (Hz). [file:1]
- Mode: Setzt Betriebsart (z. B. CWU/CWL/USB/LSB – je nach angebundener HL2-Library). [file:1]
- CW Send: Übergibt Text + WPM an das IO-Board als Job (Register-Protokoll). [file:1]
- Status: Zeigt Running/Done/Abort + Progress. [file:1]

## Bedienung

1. Backend muss laufen (Standard: `http://<pi>:8000`). [file:1]
2. WebUI öffnen (direkt statisch oder via nginx). [file:1]
3. "CW Send" drücken und Status beobachten. [file:1]
