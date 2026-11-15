# Systemarchitektur: Hermes-Lite 2 SOTA CW & Digital Modes

Diese Seite beschreibt, wie das System aufgebaut sein soll (**Ziel**) und was davon im Code dieses Repos heute tatsächlich umgesetzt ist (**Ist-Stand**). Jede Aussage ist so markiert:

- ✅ **umgesetzt**: im Code vorhanden und gegen das HL2-Protokoll plausibel
- ⚠️ **teilweise**: Code vorhanden, aber unvollständig oder mit bekannter Abweichung
- ❌ **fehlt**: nur Ziel, noch kein funktionierender Code

Die Detailbefunde und ihr Bearbeitungsstand stehen in [07_known_gaps.md](07_known_gaps.md). Stand: 2026-11-15, nach Umsetzung der Code-Korrekturen (noch ohne Test am Gerät).

---

## 1. Ziel des Systems

Headless-Betrieb eines **Hermes-Lite 2 (HL2)** über einen **Raspberry Pi 4B** (Linux ARM64), bedient über einen Browser auf einem **Android-Tablet**. Schwerpunkt ist SOTA-Portabelbetrieb in CW, ergänzt um Digitalmodi.

| Betriebsart | Weg im System | Status |
|---|---|---|
| CW TX (Text → Morse) | Backend → HL2 (C&C 0x3D, I2C2) → Pico-Keyer → ACC (Out7/Out8) → Keying-Kabel → HL2 CN4 | ⚠️ Code fertig und getestet (Host-Tests, Fake-HL2), Gerätetest offen |
| CW RX (Decoder) | HL2 IQ (24 bit) → Demodulator → 22 050 Hz → `multimon-ng` | ⚠️ Code fertig, Gerätetest offen |
| FT8, FT4, WSPR, JT9, JT65, FST4/FST4W | WSJT-X ↔ PipeWire ↔ Backend-Demodulator/Modulator ↔ HL2 | ⚠️ Audio- und TX-Pfad vorhanden, Gerätetest offen |
| PSK31/PSK63 (BPSK/QPSK), RTTY 45,45 Bd / 170 Hz | fldigi ↔ PipeWire / XML-RPC 7362 ↔ Backend ↔ HL2 | ⚠️ wie oben |

Hinweise zur Einordnung:
- PSK63 ist als `BPSK63` hinterlegt.
- FST4/FST4W sind für LF/MF (2200 m, 630 m) und KW gedacht. Senden ist mit HL2 + N2ADR-Filterboard nur ab 160 m sinnvoll, weil das Filterboard keinen LF/MF-Tiefpass hat.
- WSJT-X und fldigi sind GUI-Programme. Sie laufen hier unter `xvfb-run` (virtueller X-Server), nicht als echte Daemons.

---

## 2. Schichten im Überblick

```
┌──────────────────────────────────────────────────────────────┐
│ Android-Tablet (Browser)                                     │
│  - Web-Cockpit (statisches HTML/JS, Web-App-Manifest)        │
│  - RX-Audio per WebSocket (PCM 16 bit) → Web Audio API       │
└───────────────────────────▲──────────────────────────────────┘
                            │ WLAN: HTTP + WebSocket (nginx :80 → uvicorn :8000)
┌───────────────────────────▼──────────────────────────────────┐
│ Raspberry Pi 4B                                              │
│  FastAPI-Backend (sota_cw.api)                               │
│   ├─ rigctld-kompatibler CAT-Server (eigene Implementierung, │
│   │   TCP 127.0.0.1:4532, nur Teilmenge der Befehle)         │
│   ├─ WSJT-X UDP-Client (UDP 2237)                            │
│   ├─ fldigi XML-RPC-Client (HTTP 7362)                       │
│   ├─ Audio-Streamer (WebSocket /ws/audio)                    │
│   ├─ RX-Demodulator / SSB-Modulator (numpy, 48 kHz)          │
│   └─ HL2-Client (Protocol 1, ein UDP-Socket, EP2/EP6)        │
│  PipeWire: Null-Sinks SDR_RX_Sink / Digital_TX_Sink (48 kHz) │
│  Zeit: chrony + gpsd (USB-GPS), optional RTC                 │
└───────────────────────────▲──────────────────────────────────┘
                            │ Ethernet, openHPSDR Protocol 1 (UDP)
┌───────────────────────────▼──────────────────────────────────┐
│ Hermes-Lite 2                                                │
│  - AD9866 (12-bit ADC/DAC), FPGA mit DDC/DUC                 │
│  - N2ADR-Filterboard (I2C2, Adresse 0x20)                    │
│  - IO-Board mit RP2040/Pico (I2C2, Adresse 0x1D)             │
│  - CN4 (3,5 mm): Tip = Key, Ring = PTT ← Kabel vom IO-ACC    │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Hardware-Integration

### 3.1 Verbindung Pi ↔ HL2 (openHPSDR Protocol 1)

Fakten laut [HL2-Protokoll-Wiki](https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol) und openHPSDR-Protocol-1-Spezifikation:

- Discovery `EF FE 02`, Start/Stop `EF FE 04 <cmd>` auf UDP 1024. `cmd` Bit 0 startet den Radio-Stream, Bit 1 den Wideband-Stream, **Bit 7 schaltet beim HL2 den Watchdog ab**. ✅ `hl2_protocol.py`. Das Backend lässt den Watchdog an, damit der HL2 bei einem Absturz des Pi aufhört.
- Datenpakete `EF FE 01`, Endpoint (EP2 = Host → HL2, EP6 = HL2 → Host), 32-bit-Sequenznummer, danach **zwei 512-Byte-Frames**. Jeder Frame beginnt mit Sync `7F 7F 7F`, dann C0–C4, dann Samples.
- C0 vom Host: Bit 7 = RQST (HL2-Erweiterung), Bits 6:1 = Adresse, Bit 0 = MOX. ✅ so umgesetzt.
- RX-Samples in EP6: pro Sample 24 bit I, 24 bit Q (Big Endian) und 16 bit Mikrofon.

✅ **Umsetzung:** `hl2_protocol.py` baut und zerlegt die Pakete (zwei Frames mit `7F 7F 7F`, 24/24/16-bit-Samples). `HL2Client` besitzt den einzigen Socket: Er sendet pro empfangenem EP6-Paket ein EP2-Paket (ohne RX-Daten alle 20 ms), plant die C&C-Slots (Einmal-Befehle zuerst, sonst die Zustandsregister 0x00, 0x01, 0x02, 0x09, 0x10, 0x17 reihum) und hält höchstens eine RQST-Anfrage offen.

Wichtige C&C-Adressen (Host → HL2):

| Adresse | Inhalt |
|---|---|
| 0x00 | Samplerate, **Open-Collector-Ausgänge (C2 Bits 7:1)**, Anzahl RX, Duplex u. a. |
| 0x01 | TX-NCO-Frequenz (Hz) |
| 0x02 | RX1-NCO-Frequenz (Hz) |
| 0x03–0x08 | RX2…RX7-NCO-Frequenz (0x08 = RX7) |
| 0x09 | TX-Drive, PA ein/aus, Tune-Request |
| 0x0F / 0x10 | CWX-Enable / CW-Hang-Time |
| 0x17 | PTT-Hang-Time, TX-Buffer-Latenz |
| 0x39 | Misc, u. a. Watchdog ein/aus |
| 0x3C / 0x3D | I2C1 / I2C2-Zugriff |

### 3.2 N2ADR-Filterboard

- 6 Tiefpässe (160 m, 80 m, 60/40 m, 30/20 m, 17/15 m, 12/10 m) und ein 3-MHz-Hochpass. Kein Filter für 6 m.
- **Ansteuerung:** Der Host setzt die 7 Open-Collector-Bits in **C&C-Adresse 0x00, C2 Bits 7:1**. Die HL2-Gateware schreibt daraus das Byte für das Filterboard an I2C2-Adresse 0x20 (Bit 7 = RX-Antenne, Bits 6:0 = OC-Bits).
- Bitbelegung (wie in `n2adr_filter.py`): Bit 0…5 = ein Tiefpass, Bit 6 = 3-MHz-Hochpass (aus auf 160 m). ✅ Die Belegung stimmt.
- ✅ `HL2Control` legt das Relaiswort in die OC-Bits von Adresse 0x00 (DATA[23:17]). `set_ptt()` ändert nur das MOX-Bit in C0; das Wort 0x00 wird immer vollständig gesendet.
- ✅ 6 m (und alles über 30 MHz) ist nur Empfang; TX wird abgelehnt, der CAT-Server meldet TX bis 29,7 MHz.

**SWR / Leistung:**
- Der HL2 meldet Telemetrie in den EP6-Antwortframes: RADDR 0x01 = Temperatur + Vorwärtsleistung, RADDR 0x02 = Rückwärtsleistung + Strom.
- ✅ `hl2_protocol.Telemetry` wertet die Antwortframes aus. Bei jedem Senden (MOX oder PTT-Bit des HL2, also auch bei CW über CN4) berechnet `HL2Control` das SWR. Liegt es `swr_trip_count` Messungen in Folge über `max_vswr_threshold`, wird MOX abgeschaltet, Drive auf 0 gesetzt und der Pico-Keyer abgebrochen. Rücksetzen mit `POST /hl2/swr/reset`.
- ✅ Γ wird aus dem Leistungsverhältnis berechnet (|Γ| = √(P_rev/P_fwd)), das Detektorgesetz ist einstellbar (`power_detector_law`). ⚠️ `power_cal_factor` und das Detektorgesetz müssen am Gerät mit Dummy-Load und Wattmeter kalibriert werden.

### 3.3 IO-Board (RP2040/Pico) und CW-Keyer

Fakten:
- Das IO-Board hängt am **I2C2-Bus des HL2, Adresse 0x1D** ([Thetis-I2C-Control-Wiki](https://github.com/softerhardware/Hermes-Lite2/wiki/Thetis-I2C-Control)).
- Zugriff erfolgt über **C&C-Adresse 0x3D**: `[31:24]` Cookie (0x06 = Write, 0x07 = Read), `[23]` Stop, `[22:16]` I2C-Adresse, `[15:8]` **8-bit-Registernummer**, `[7:0]` ein Datenbyte. Lesen mit RQST, Antwort in C1–C4 mit ACK.
- Das HL2-Wiki erwähnt einen Extended-Write über Adresse 0x3F + EADDR, die Extended-Memory-Map ist aber nicht definiert. Es gibt keinen dokumentierten Weg, darüber das IO-Board zu erreichen.

✅ **Umsetzung:** `ioboard.py` spricht das IO-Board nur noch über C&C 0x3D an: 8-bit-Register, ein Byte pro Write, Reads liefern 4 Bytes ab der Registernummer. Die Keyer-Registermap liegt in 200–215 ([03_ioboard_register_protocol.md](03_ioboard_register_protocol.md)).

✅ **Firmware:** `firmware/pico_cw_keyer` ist eine vollständige IO-Board-Firmware: I2C-Slave an i2c1 (GPIO 14/15, Adresse 0x1D), Standardregister 0–12 (Frequenz, Eingänge, Lüfter, RF-Eingänge, HPF) und der Keyer. Sie ersetzt die N2ADR-Standardfirmware; Bandausgänge für eine Endstufe und der ATU-Treiber sind **nicht** enthalten.

**CW-Pfad:** Der Pi schreibt den Text in ein FIFO-Register des Pico. Der Pico erzeugt das Morse-Timing und schaltet zwei Low-Side-Schalter (Out7 = KEY, Out8 = PTT) am ACC-Anschluss (D-Sub) des IO-Boards. Ein externes Keying-Kabel (D-Sub-Stecker ↔ 3,5-mm-Klinke) führt sie auf die Key-Buchse **CN4** des HL2: Out7 → Tip, Out8 → Ring, GND → Sleeve. Es wird nichts gelötet oder im Gehäuse verändert. Der HL2 erzeugt daraus ein geformtes CW-Signal. Zwischen Pi und HL2 bleibt das Netzwerkkabel die einzige Verbindung. Schutz: Host-Heartbeat (Pico lässt nach 3 s ohne I2C-Write los), Tune-Begrenzung 15 s, Hardware-Watchdog des Pico.

**Envelope-Shaping:** Die Adressen 0x18/0x19 (`set_cw_envelope`) gibt es in der Standard-HL2-Gateware nicht. Sie existieren nur im eigenen Gateware-Fork ([Hermes-Lite2_DSP PR #1](https://github.com/philibertschlutzki/Hermes-Lite2_DSP/pull/1)). Mit Standard-Gateware greift die eingebaute CW-Formung des HL2.

---

## 4. Audio- und Modulationspfad

### 4.1 Empfang (RX)

Ziel: HL2-IQ → Demodulator auf dem Pi → PipeWire `SDR_RX_Sink` → WSJT-X / fldigi / Tablet.

Ist-Stand:
- ✅ PipeWire-Null-Sinks `SDR_RX_Sink` und `Digital_TX_Sink` (48 kHz) aus `deploy/setup_pipewire_audio.sh`.
- ✅ `dsp.Demodulator` (CWU/CWL/USB/LSB/DIGU/DIGL/AM) läuft im Thread `rx-audio` und schreibt per `pacat` in `SDR_RX_Sink`, an `/ws/audio` und (in CW) an den Decoder. Der Decoder bekommt 22 050 Hz.
- ⚠️ Kein Opus/WebRTC; `/ws/audio` überträgt PCM 16 bit, 48 kHz, mono (ca. 768 kbit/s).

### 4.2 Senden (TX) für Digitalmodi

- ✅ `TxAudioPipeline` liest per `parec` den Monitor von `Digital_TX_Sink`, `dsp.SSBModulator` erzeugt USB/LSB-IQ, `HL2Client` sendet es bei MOX in EP2. PTT kommt von WSJT-X/fldigi über den CAT-Server (`T 1`).
- ⚠️ Pegel (`tx_audio_gain`, Drive) und Unterdrückung des Gegenseitenbands am Gerät prüfen.

---

## 5. Zeitsynchronisation im SOTA-Betrieb

- WSJT-X verlangt laut Handbuch eine Uhr innerhalb von **±1 s** zu UTC. Besser als ±0,1 s ist ein sinnvolles Ziel, aber keine Voraussetzung.
- Der Pi 4B hat keine eingebaute RTC.
- ✅ `deploy/setup_sota_timesync.sh`: GPS-NMEA (SHM 0) ist wählbar, PPS (SHM 1) wird nur bevorzugt, wenn vorhanden. `makestep 1 -1` erlaubt Sprünge jederzeit. Ein USB-GPS ohne PPS reicht für ±1 s; der NMEA-Offset (`SOTA_GPS_OFFSET`) lässt sich anpassen.
- ✅ DS3231 wird per `dtoverlay=i2c-rtc,ds3231` eingerichtet, `fake-hwclock` entfernt, chrony mit `rtcsync`.

---

## 6. Netzwerk und Ports

| Dienst | Port | Bindung |
|---|---|---|
| nginx (WebUI + Proxy) | TCP 80 | alle Interfaces |
| FastAPI (uvicorn) | TCP 8000 | 0.0.0.0 |
| CAT (rigctld-kompatibel) | TCP 4532 | 127.0.0.1 |
| WSJT-X UDP | UDP 2237 | 127.0.0.1 |
| fldigi XML-RPC | TCP 7362 | 127.0.0.1 |
| HL2 | UDP 1024 (HL2), ein beliebiger lokaler Port (Pi) | Ethernet |

Die API kann mit `SOTA_CW_API_TOKEN` geschützt werden (Header `X-API-Token` oder `?token=`; die WebUI merkt sich den Token nach einmaligem Aufruf mit `?token=…`). Ohne Token ist sie offen; das Tablet-WLAN sollte dann ein eigenes, geschütztes Netz sein.
