# Überblick: Hermes Lite SDR SOTA CW

Diese Dokumentation beschreibt, wie dieses Projekt mit einem Hermes-Lite-2 (HL2) und (optional) einem IO-Board so eingerichtet wird, dass CW/Keying/PTT und die Bedienung reproduzierbar funktionieren.

## Für wen ist das?
- Anfänger: Schritt-für-Schritt bis zum ersten Test.
- Fortgeschrittene: Protokoll-/Registerdetails und Debug-Hinweise.

## Was wird hier dokumentiert?
- Hardware-Verdrahtung (HL2 ↔ IO-Board ↔ Key/PTT/Peripherie)
- Bring-up Checkliste (Strom, Netzwerk, Firmware, Funktionstests)
- Register-/Protokollkonzept des IO-Boards (für Entwickler/Debug)
- WebUI: typische Bedienabläufe
- Troubleshooting: typische Fehlerbilder + Checks

## Voraussetzungen (Minimum)
- Ein funktionsfähiger Hermes-Lite-2 (Netzwerk erreichbar, RX/TX grundsätzlich möglich)
- Ein PC im selben Netzwerk (für WebUI/SDR-Software)
- Optional: IO-Board, falls PTT/KEY/GPIO über Register gesteuert werden

## Empfohlene Leseroute
1. 01_hardware_wiring.md
2. 02_bringup_checklist.md
3. 04_webui_user_guide.md
4. 05_troubleshooting.md
5. 03_ioboard_register_protocol.md (nur wenn du Register/Backend debuggen oder erweitern willst)

## Begriffsklärung (kurz)
- PTT: „Push To Talk“, schaltet Senden ein/aus.
- KEY: CW-Tastung (Morsetaste/Keyer-Signal).
- Low-Side Switching: Ausgang schaltet gegen Masse (GND), nicht gegen +V.

## Weiterführende Links
- HL2 Protokoll (Wiki, Hintergrund/Details): https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol
- Thetis Installation (HL2 + 3rd Party Apps, PDF): https://raw.githubusercontent.com/wiki/softerhardware/Hermes-Lite2/docs/Hermes_Lite_2_Thetis_Installation_and_3rd_Party_Apps.pdf
- Thetis Benutzerhandbuch (allgemein): https://saure.org/cq-nrw/wp-content/uploads/2020/02/Thetis-manual-v0_2.pdf
- Praxis-Guide (Beispiel-Setup mit Thetis): https://gw3jvb.uk/amateur-radio/a-guide-to-hermes-lite-2-mac-parallels-thetis/
