# Überblick: Hermes Lite SDR SOTA CW

Dieses Projekt betreibt einen **Hermes-Lite 2 (HL2)** headless über einen **Raspberry Pi 4B** und bedient ihn per Browser von einem **Android-Tablet**. Schwerpunkt ist CW im SOTA-Portabelbetrieb, dazu kommen Digitalmodi über WSJT-X und fldigi.

> **Projektstand:** Mehrere Teile sind noch nicht funktionsfähig (u. a. Filterumschaltung, SWR-Schutz, Audio-Pfad, IO-Board-Anbindung). Was umgesetzt ist und was fehlt, steht in [06_architecture.md](06_architecture.md) und [07_known_gaps.md](07_known_gaps.md). Bitte vor dem ersten Sendeversuch lesen.

## Komponenten

- **HL2** mit N2ADR-Filterboard (Tiefpässe 160–10 m, 3-MHz-Hochpass)
- **IO-Board** mit Raspberry Pi Pico (RP2040), optional
- **Raspberry Pi 4B** mit FastAPI-Backend, nginx, PipeWire, WSJT-X und fldigi
- **Android-Tablet** mit Browser als Bedienoberfläche

## Dokumente

| Datei | Inhalt | Für wen |
|---|---|---|
| [01_hardware_wiring.md](01_hardware_wiring.md) | Verkabelung HL2, IO-Board, Pi, Key/PTT | alle |
| [02_bringup_checklist.md](02_bringup_checklist.md) | Inbetriebnahme Schritt für Schritt | alle |
| [04_webui_user_guide.md](04_webui_user_guide.md) | Bedienung am Tablet | alle |
| [05_troubleshooting.md](05_troubleshooting.md) | Fehlerbilder und Checks | alle |
| [03_ioboard_register_protocol.md](03_ioboard_register_protocol.md) | IO-Board-Zugriff und CW-Registermap | Entwickler |
| [06_architecture.md](06_architecture.md) | Systemarchitektur, Ziel vs. Ist-Stand | Entwickler |
| [07_known_gaps.md](07_known_gaps.md) | Liste der bekannten Abweichungen | Entwickler |
| [tx_quality_nanovna_h4.md](tx_quality_nanovna_h4.md) | TX-Qualitätstest mit NanoVNA-H4 | Messung |
| [test_reports/](test_reports/README.md) | Messprotokolle und CSV-Schema | Messung |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Änderungsbericht vom 2026-01-04 (historisch) | Entwickler |

## Empfohlene Leseroute

1. [01_hardware_wiring.md](01_hardware_wiring.md)
2. [02_bringup_checklist.md](02_bringup_checklist.md)
3. [04_webui_user_guide.md](04_webui_user_guide.md)
4. [05_troubleshooting.md](05_troubleshooting.md)
5. [06_architecture.md](06_architecture.md) und [03_ioboard_register_protocol.md](03_ioboard_register_protocol.md), wenn du am Backend oder an der Firmware arbeitest

## Begriffe

- **PTT** (Push To Talk): schaltet den Sender ein/aus.
- **KEY**: CW-Tastung. Am HL2 über die 3,5-mm-Buchse CN4 (Tip).
- **MOX**: Sendebit im openHPSDR-Protokoll (C0 Bit 0), per Software gesetzt.
- **Low-Side-Switching**: Ein Ausgang schaltet gegen Masse (GND), nicht gegen +V.
- **C&C**: Command & Control, die Steuerbytes C0–C4 im openHPSDR-Protocol-1-Frame.
- **EP2 / EP6**: Datenkanäle Host → HL2 (TX-IQ + C&C) bzw. HL2 → Host (RX-IQ + Telemetrie).

## Weiterführende Links

- HL2 Protokoll: https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol
- HL2 I2C (Filterboard, IO-Board): https://github.com/softerhardware/Hermes-Lite2/wiki/Thetis-I2C-Control
- HL2 IO-Pins: https://github.com/softerhardware/Hermes-Lite2/wiki/IO
- Thetis mit HL2 (PDF, nützlich zum Gegentest am PC): https://raw.githubusercontent.com/wiki/softerhardware/Hermes-Lite2/docs/Hermes_Lite_2_Thetis_Installation_and_3rd_Party_Apps.pdf
