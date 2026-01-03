# Bring-up Checkliste (Inbetriebnahme)

Diese Seite ist absichtlich als Checkliste geschrieben: Jeder Punkt soll eindeutig „OK“ oder „nicht OK“ sein.

## 0) Vorbereitung
- Notiere dir: HL2 IP-Adresse, PC IP-Adresse, Subnetzmaske.
- Lege fest: Welche Software nutzt du als SDR-Frontend (z. B. Thetis) und welche Rolle hat die WebUI.

## 1) Stromversorgung
- Versorgungsspannung stabil.
- Keine Resets beim Umschalten RX/TX.

## 2) Netzwerk
- HL2 ist im Netzwerk erreichbar (Ping/ARP sichtbar).
- Keine Paketverluste im lokalen Netz.

## 3) Basis-Funktion (ohne IO-Board)
- RX funktioniert (Wasserfall/Audio).
- TX funktioniert in einem kontrollierten Test (kurz, geringe Leistung).

## 4) IO-Board (wenn genutzt)
- Firmware ist geflasht.
- Ein „Testregister“ oder Minimal-Read/Write funktioniert (nur dann weiter machen).

Hinweis: Bei IO-Boards im HL2-Umfeld ist es üblich, dass Register in einem 256-Byte-Array abgebildet werden und Lesen/Schreiben prinzipiell möglich ist; Details variieren je Firmware.

## 5) PTT/KEY Funktionstest
- PTT: TX geht sicher an/aus.
- KEY: CW-Keying ist zuverlässig.
- Wenn etwas invertiert wirkt: Logikpegel/„active low“ prüfen.

## 6) Software-Setup (Thetis)
- Thetis Installation/HL2-spezifische Hinweise: siehe PDF aus HL2-Wiki.
- Für Bedienkonzepte/Begriffe: Thetis Manual.

## Nächster Schritt
- Wenn alles läuft: 04_webui_user_guide.md
- Wenn etwas hakt: 05_troubleshooting.md
