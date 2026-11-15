# Bekannte Lücken: Code vs. HL2-Hardware

Diese Liste ist das Ergebnis eines Abgleichs von [06_architecture.md](06_architecture.md) mit dem Code und der HL2-Dokumentation (Stand 2026-11-15). Sie ist als Arbeitsliste gedacht: Ein Punkt wird gestrichen, wenn der Code korrigiert **und** am Gerät getestet ist.

Status:
- **Code** = im Code behoben und mit Unit-/Host-Tests (inkl. Fake-HL2 über UDP) geprüft, Test am Gerät offen
- **offen** = noch nicht behoben

Quellen für HL2-Fakten:
- [HL2 Protocol Wiki](https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol)
- [HL2 Thetis I2C Control](https://github.com/softerhardware/Hermes-Lite2/wiki/Thetis-I2C-Control)
- [HL2 IO Board (N2ADR)](https://github.com/jimahlstrom/HL2IOBoard): `i2c_registers.h`, `hl2ioboard.h`, `n2adr_lib/i2c_slave_handler.c`
- openHPSDR Protocol 1 (Metis/USB-Frame-Format), auf dem das HL2-Protokoll aufbaut

Priorität: **P1** = verhindert Funktion oder ist sicherheitsrelevant, **P2** = falsches Verhalten, **P3** = Doku/Komfort.

## Protokoll und Hardware

| ID | Prio | Befund | Status | Umsetzung / Gerätetest |
|---|---|---|---|---|
| G1 | P1 | C&C-Frames ohne `7F 7F 7F`-Sync, nicht in zwei 512-Byte-Frames. | Code | `hl2_protocol.build_ep2_packet()`. Test: HL2 nimmt Frequenz an. |
| G2 | P1 | N2ADR-Relaiswort an Adresse 0x08 statt OC-Bits in 0x00. | Code | `HL2Control._apply_frequency()` → `general_word(oc_bits=…)`. Test: Relais klicken beim Bandwechsel. |
| G3 | P1 | `set_ptt()` überschrieb Adresse 0x00. | Code | PTT setzt nur das MOX-Bit in C0; 0x00 wird zyklisch vollständig gesendet. |
| G4 | P1 | Kein SWR-Schutz. | Code | `Telemetry` (RADDR 0x01/0x02), `HL2Control._on_telemetry()`, Abschaltung: MOX aus, Drive 0, Pico-ABORT. Test: Leistung und SWR mit Dummy-Load/Fehlanpassung kalibrieren (`power_cal_factor`, `power_detector_law`). |
| G5 | P1 | IQ als 16 bit statt 24/24/16 gelesen. | Code | `hl2_protocol.parse_ep6_packet()`. |
| G6 | P2 | Zwei Sockets starteten den HL2. | Code | Ein Socket in `HL2Client`; Decoder, Audio und Steuerung hängen als Callbacks daran. |
| G7 | P1 | IO-Board über 0x3F + EADDR mit 16-bit-Werten, Register > 255. | Code | `ioboard.py` nutzt C&C 0x3D (I2C2, 0x1D), 8-bit-Register; neue Keyer-Map 200–215. |
| G8 | P1 | Pico-Firmware ohne I2C-Slave, nur Mock-Register. | Code | `firmware/pico_cw_keyer`: I2C-Slave (i2c1, GPIO 14/15), Keyer-Automat, Watchdogs. Baut gegen Pico SDK 2.1.1 (CI). Test: Firmware flashen, `GET /hardware/ioboard/status` zeigt `keyer_present`. |
| G9 | P2 | KEY/PTT des Pico nicht mit dem HL2 verbunden. | Code | Firmware schaltet J6 Out7 (KEY) und Out8 (PTT); Verdrahtung zu CN4 in [01_hardware_wiring.md](01_hardware_wiring.md). Test: Verdrahtung und Polarität am Gerät prüfen. |
| G10 | P2 | `set_cw_envelope()` mit Adressen 0x18/0x19 der eigenen Gateware. | Code | Nur noch aktiv mit `SOTA_CW_HL2_CUSTOM_GATEWARE_ENVELOPE=true`. |
| G11 | P2 | 6 m TX möglich, CAT meldete TX bis 54 MHz. | Code | `BandInfo.tx_allowed`, TX-Sperre in `HL2Control`/`CWJobManager`, CAT-TX-Bereich bis 29,7 MHz. |
| G12 | P3 | IO-Board-Standardregister nicht belegt. | Code | Registernummern aus `i2c_registers.h` übernommen (Lüfter jetzt Register 12, Firmware 9/10). |
| G13 | P3 | SWR-Formel passte nicht zum Kommentar. | Code | Γ aus Leistungsverhältnis, Detektorgesetz wählbar. |
| G14 | P2 | Die Keyer-Firmware ersetzt die N2ADR-Standardfirmware: kein ATU-Treiber (Icom AH-4), keine Bandausgänge für Endstufen. | offen | Bei Bedarf in `main.c` ergänzen. Register 7 wird nur gespeichert. |

## Audio und Modems

| ID | Prio | Befund | Status | Umsetzung / Gerätetest |
|---|---|---|---|---|
| A1 | P1 | Kein SSB/DIGU-Demodulator, keine Ausgabe nach `SDR_RX_Sink`. | Code | `dsp.Demodulator`, `audio/radio_audio.RxAudioPipeline` (`pacat`). Test: WSJT-X dekodiert. |
| A2 | P1 | Kein TX-Pfad für Digitalmodi. | Code | `TxAudioPipeline` (`parec` von `Digital_TX_Sink.monitor`) → `SSBModulator` → EP2-IQ bei MOX. Test: Spektrum, Gegenseitenband, Pegel. |
| A3 | P2 | `broadcast_pcm()` nie aufgerufen. | Code | `AudioStreamer.feed_audio()` hängt an der RX-Pipeline; Thread→Event-Loop-Übergabe korrigiert. |
| A4 | P2 | `multimon-ng` bekam 48 kHz statt 22 050 Hz. | Code | `dsp.Resampler` im Decoder. |
| A5 | P3 | PSK63 fehlte. | Code | `FldigiModem.BPSK63`, WebUI-Auswahl. |
| A6 | P3 | fldigi-Service mit `--daemon --xmlrpc-server --xmlrpc-port`, beide Dienste auf Display 99. | Code | `--xmlrpc-server-address/-port`, fldigi auf Display 98. Test: `systemctl status sota-fldigi`. |

## Betrieb

| ID | Prio | Befund | Status | Umsetzung / Gerätetest |
|---|---|---|---|---|
| B1 | P2 | chrony: GPS mit `noselect`. | Code | NMEA wählbar, PPS optional bevorzugt, `makestep 1 -1`. Test: `chronyc sources` zeigt `*NMEA`; Offset gegen bekannte Zeit prüfen. |
| B2 | P3 | DS3231 nicht eingerichtet. | Code | `dtoverlay=i2c-rtc,ds3231`, `fake-hwclock` entfernt, `rtcsync`. |
| B3 | P3 | Kein Web-App-Manifest. | Code | `manifest.webmanifest`, `icon.svg`. |
| B4 | P3 | API ohne Authentifizierung. | Code | Optionaler Token `SOTA_CW_API_TOKEN` (Header `X-API-Token` oder `?token=`). |
| B5 | P3 | Backend, WSJT-X und fldigi als Systemdienste brauchen die PipeWire-Sitzung des Benutzers. | Code | `loginctl enable-linger`, `XDG_RUNTIME_DIR` in den Units. Test nach Neustart ohne Login. |
