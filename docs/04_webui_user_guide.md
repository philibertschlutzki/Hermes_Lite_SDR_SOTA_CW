# WebUI Benutzeranleitung

Ziel: Einsteiger sollen typische Aufgaben „blind“ erledigen können (Starten, Konfigurieren, Testen, Logs ansehen).

## Typische Aufgaben
- Verbindung zum HL2 prüfen (IP/Port/Erreichbarkeit).
- PTT/KEY testen (mit klarer Rückmeldung).
- Statusanzeigen interpretieren (verbunden/nicht verbunden, Fehlerstatus).

## Debug bei „UI tut nichts“
- Backend-Logs ansehen (systemd/journalctl o. ä.).
- Netzwerk prüfen: richtige HL2-IP, kein VLAN/Firewall dazwischen.

## Wenn du Thetis parallel nutzt
- Installations- und HL2-spezifische Hinweise stehen im HL2-Wiki-PDF.
- Für die Bedienlogik (AGC, Filter, Audio): Thetis Manual.

## Nächster Schritt
Wenn etwas nicht wie erwartet läuft: 05_troubleshooting.md
