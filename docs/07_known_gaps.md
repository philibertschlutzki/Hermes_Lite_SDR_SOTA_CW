# Bekannte Lücken: Code vs. HL2-Hardware

Diese Liste ist das Ergebnis eines Abgleichs von [06_architecture.md](06_architecture.md) mit dem Code und der HL2-Dokumentation (Stand 2026-11-15). Sie ist als Arbeitsliste gedacht: Ein Punkt wird gestrichen, wenn der Code korrigiert und am Gerät getestet ist.

Quellen für HL2-Fakten:
- [HL2 Protocol Wiki](https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol)
- [HL2 Thetis I2C Control](https://github.com/softerhardware/Hermes-Lite2/wiki/Thetis-I2C-Control)
- openHPSDR Protocol 1 (Metis/USB-Frame-Format), auf dem das HL2-Protokoll aufbaut

Priorität: **P1** = verhindert Funktion oder ist sicherheitsrelevant, **P2** = falsches Verhalten, **P3** = Doku/Komfort.

## Protokoll und Hardware

| ID | Prio | Befund | Ort |
|---|---|---|---|
| G1 | P1 | C&C-Frames ohne `7F 7F 7F`-Sync und nicht in zwei 512-Byte-Frames aufgeteilt. Der HL2 wird diese Frames voraussichtlich nicht als gültige C&C-Daten erkennen. | `hl2_client.py:77` |
| G2 | P1 | N2ADR-Relaiswort wird an C&C-Adresse 0x08 (= RX7-NCO) geschrieben. Richtig ist Adresse 0x00, C2 Bits 7:1 (Open-Collector-Ausgänge). Filter schalten nicht. | `hl2_control.py:79` |
| G3 | P1 | `set_ptt()` sendet Adresse 0x00 mit Daten 0. Das überschreibt Samplerate, OC-Bits (Filter) und RX-Anzahl. Adresse 0x00 muss immer mit dem vollständigen aktuellen Zustand gesendet werden. | `hl2_control.py:104` |
| G4 | P1 | Kein SWR-Schutz: EP6-Telemetrie (RADDR 0x01 Vorwärts-, 0x02 Rückwärtsleistung) wird nicht ausgewertet, `measure_swr()` erhält nie Messwerte, es gibt keine TX-Abschaltung. | `hl2_control.py:118`, `api.py` |
| G5 | P1 | `hl2_stream.py` liest IQ als 16-bit-Paare. HL2/Protocol 1 liefert pro Sample 24 bit I, 24 bit Q, 16 bit Mic, nach Sync und C0–C4 in jedem 512-Byte-Frame. | `hl2_stream.py:106` |
| G6 | P2 | Zwei Sockets (1025 Steuerung, 1024 Streamer) starten jeweils den HL2. Protocol 1 kennt nur einen Host-Stream; Steuerung und IQ müssen über denselben EP2/EP6-Kanal laufen. | `hl2_client.py`, `hl2_stream.py:73` |
| G7 | P1 | IO-Board-Zugriff über 0x3F + EADDR mit 16-bit-Werten. Dokumentiert ist I2C2 über Adresse 0x3D, I2C-Adresse 0x1D, 8-bit-Registernummer, ein Datenbyte. Register > 255 (Textpuffer-Ende, Envelope 270–273) sind so nicht erreichbar. | `hl2_client.py:132`, `ioboard.py`, `hardware/hl2_io_board.py` |
| G8 | P1 | Pico-Firmware hat nur eine Mock-Registerbank (`g_regs[512]`) und keinen I2C-Slave. Sie würde außerdem die Standard-IO-Board-Firmware ersetzen. | `firmware/pico_cw_keyer/src/main.c:19` |
| G9 | P2 | KEY/PTT des Pico (GPIO 3/2) sind nicht mit dem HL2 verbunden. Der HL2 tastet über CN4 (Tip = Key, Ring = PTT) oder über CWX (Adresse 0x0F). | `firmware/pico_cw_keyer/src/outputs.c` |
| G10 | P2 | `set_cw_envelope()` nutzt Adressen 0x18/0x19. Die gibt es nur im eigenen Gateware-Fork, nicht in der Standard-Gateware. | `hl2_control.py:97` |
| G11 | P2 | 6 m auf den 12/10-m-Tiefpass gemappt; das N2ADR-Board hat keinen 6-m-Filter. TX auf 6 m sperren. CAT `dump_state` meldet TX bis 54 MHz. | `hardware/n2adr_filter.py:39`, `hardware/cat_server.py` |
| G12 | P3 | IO-Board-Standardregister (0x00–0x09) und ATU-Statuswerte sind nicht durch HL2-Doku belegt. Gegen die N2ADR-IO-Board-Firmware prüfen. | `hardware/hl2_io_board.py` |
| G13 | P3 | SWR-Formel: Kommentar nimmt quadratischen Detektor an (P ∝ U²), rechnet Γ aber linear als U_rev/U_fwd. | `hardware/n2adr_filter.py` |

## Audio und Modems

| ID | Prio | Befund | Ort |
|---|---|---|---|
| A1 | P1 | Kein SSB/DIGU-Demodulator und keine Ausgabe nach `SDR_RX_Sink`. WSJT-X/fldigi bekommen kein Empfangsaudio. | – |
| A2 | P1 | Kein TX-Pfad: Audio aus `Digital_TX_Sink` wird nicht zu IQ moduliert und nicht per EP2 gesendet. | – |
| A3 | P2 | `AudioStreamer.broadcast_pcm()` wird nirgends aufgerufen; `/ws/audio` sendet nichts. | `audio/audio_streamer.py` |
| A4 | P2 | `multimon-ng -t raw` erwartet 22 050 Hz, der interne Streamer liefert 48 kHz. | `config.py:97`, `hl2_stream.py:66` |
| A5 | P3 | PSK63 wird in der Doku genannt, ist aber kein `FldigiModem`. | `modems/fldigi_client.py` |
| A6 | P3 | fldigi-Service nutzt `--daemon --xmlrpc-server --xmlrpc-port`. fldigi kennt nach bisherigem Kenntnisstand `--xmlrpc-server-port`; `--daemon` gegen `fldigi --help` prüfen. Beide Services nutzen Xvfb-Display 99. | `deploy/systemd/sota-fldigi.service:10`, `sota-wsjtx.service:11` |

## Betrieb

| ID | Prio | Befund | Ort |
|---|---|---|---|
| B1 | P2 | chrony: GPS mit `noselect`, nur PPS wählbar. USB-GPS ohne PPS → keine Zeitquelle. | `deploy/setup_sota_timesync.sh:20` |
| B2 | P3 | DS3231-RTC wird nirgends eingerichtet. | – |
| B3 | P3 | WebUI hat kein Web-App-Manifest; „PWA“ ist nur ein Startbildschirm-Lesezeichen. | `pi/webui/static/` |
| B4 | P3 | API ohne Authentifizierung auf 0.0.0.0. | `deploy/systemd/sota-sdr-backend.service` |
