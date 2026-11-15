# Systemarchitektur: Hermes-Lite 2 SOTA CW & Digital Modes

Diese Seite beschreibt, wie das System aufgebaut sein soll (**Ziel**) und was davon im Code dieses Repos heute tatsächlich umgesetzt ist (**Ist-Stand**). Jede Aussage ist so markiert:

- ✅ **umgesetzt**: im Code vorhanden und gegen das HL2-Protokoll plausibel
- ⚠️ **teilweise**: Code vorhanden, aber unvollständig oder mit bekannter Abweichung
- ❌ **fehlt**: nur Ziel, noch kein funktionierender Code

Die Detailbefunde mit Datei- und Zeilenbezug stehen in [07_known_gaps.md](07_known_gaps.md). Stand der Prüfung: 2026-11-15.

---

## 1. Ziel des Systems

Headless-Betrieb eines **Hermes-Lite 2 (HL2)** über einen **Raspberry Pi 4B** (Linux ARM64), bedient über einen Browser auf einem **Android-Tablet**. Schwerpunkt ist SOTA-Portabelbetrieb in CW, ergänzt um Digitalmodi.

| Betriebsart | Weg im System | Status |
|---|---|---|
| CW TX (Text → Morse) | Backend → Pico-Keyer → KEY/PTT-Leitung → HL2 | ⚠️ Keyer-Logik vorhanden, Registerzugriff ist nur ein Mock (siehe 3.3) |
| CW RX (Decoder) | HL2 IQ → Python-Demodulator → `multimon-ng` | ⚠️ IQ-Parsing und Samplerate passen nicht zum HL2 (siehe 4.1) |
| FT8, FT4, WSPR, JT9, JT65, FST4/FST4W | WSJT-X (unter Xvfb) ↔ UDP 2237 ↔ Backend | ⚠️ UDP-Steuerung vorhanden, Audio- und TX-Pfad zum HL2 fehlen |
| PSK31 (BPSK/QPSK), RTTY 45,45 Bd / 170 Hz | fldigi (unter Xvfb) ↔ XML-RPC 7362 ↔ Backend | ⚠️ XML-RPC vorhanden, Audio- und TX-Pfad zum HL2 fehlen |

Hinweise zur Einordnung:
- PSK63 ist im Backend nicht als Modem hinterlegt (`FldigiModem` kennt nur BPSK31, QPSK31, RTTY, CW).
- FST4/FST4W sind für LF/MF (2200 m, 630 m) und KW gedacht. Senden ist mit HL2 + N2ADR-Filterboard nur ab 160 m sinnvoll, weil das Filterboard keinen LF/MF-Tiefpass hat.
- WSJT-X und fldigi sind GUI-Programme. Sie laufen hier unter `xvfb-run` (virtueller X-Server), nicht als echte Daemons.

---

## 2. Schichten im Überblick

```
┌──────────────────────────────────────────────────────────────┐
│ Android-Tablet (Browser)                                     │
│  - Web-Cockpit (statisches HTML/JS, kein PWA-Manifest)       │
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
│   └─ HL2-Client (openHPSDR Protocol 1, UDP 1024)             │
│  PipeWire: Null-Sinks SDR_RX_Sink / Digital_TX_Sink (48 kHz) │
│  Zeit: chrony + gpsd (USB-GPS), optional RTC                 │
└───────────────────────────▲──────────────────────────────────┘
                            │ Ethernet, openHPSDR Protocol 1 (UDP)
┌───────────────────────────▼──────────────────────────────────┐
│ Hermes-Lite 2                                                │
│  - AD9866 (12-bit ADC/DAC), FPGA mit DDC/DUC                 │
│  - N2ADR-Filterboard (I2C2, Adresse 0x20)                    │
│  - IO-Board mit RP2040/Pico (I2C2, Adresse 0x1D)             │
│  - CN4 (3,5 mm): Tip = CW-Key, Ring = PTT                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Hardware-Integration

### 3.1 Verbindung Pi ↔ HL2 (openHPSDR Protocol 1)

Fakten laut [HL2-Protokoll-Wiki](https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol) und openHPSDR-Protocol-1-Spezifikation:

- Discovery `EF FE 02`, Start/Stop `EF FE 04 <cmd>` auf UDP 1024. `cmd` Bit 0 startet den Radio-Stream, Bit 1 den Wideband-Stream, **Bit 7 schaltet beim HL2 den Watchdog ab**. ✅ so umgesetzt in `hl2_client.py`.
- Datenpakete `EF FE 01`, Endpoint (EP2 = Host → HL2, EP6 = HL2 → Host), 32-bit-Sequenznummer, danach **zwei 512-Byte-Frames**. Jeder Frame beginnt mit Sync `7F 7F 7F`, dann C0–C4, dann Samples.
- C0 vom Host: Bit 7 = RQST (HL2-Erweiterung), Bits 6:1 = Adresse, Bit 0 = MOX. ✅ so umgesetzt.
- RX-Samples in EP6: pro Sample 24 bit I, 24 bit Q (Big Endian) und 16 bit Mikrofon.

⚠️ **Abweichung im Code:** `HL2Client` baut die Frames ohne `7F 7F 7F`-Sync und ohne Aufteilung in zwei 512-Byte-Frames. `hl2_stream.py` liest IQ als 16-bit-Paare statt 24/24/16. Siehe [07_known_gaps.md](07_known_gaps.md), G1 und G5.

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
- ❌ **Abweichung im Code:** `HL2Control.set_frequency_hz()` schreibt das Relaiswort nach **Adresse 0x08**. Das ist die RX7-NCO-Frequenz, nicht das Filterboard. Die Filter schalten so nicht um. Zusätzlich sendet `set_ptt()` ein Frame an Adresse 0x00 mit Daten 0 und löscht damit OC-Bits, Samplerate und RX-Anzahl.
- 6 m ist im Code auf den 12/10-m-Tiefpass gemappt. Damit wäre 50 MHz stark gedämpft; 6 m sollte für TX gesperrt sein.

**SWR / Leistung:**
- Der HL2 meldet Telemetrie in den EP6-Antwortframes: RADDR 0x01 = Temperatur + Vorwärtsleistung, RADDR 0x02 = Rückwärtsleistung + Strom.
- ❌ Dieses Parsing fehlt im Code. `measure_swr()` wird nirgends mit Messwerten aufgerufen, `last_measurement` bleibt leer. Die WebUI zeigt deshalb immer SWR 1,0.
- ❌ Ein SWR-Interlock (TX-Stopp bei VSWR > 3,0) existiert nur als Konfigurationswert `max_vswr_threshold`. Es gibt keine Abschaltlogik.
- Zur Formel: VSWR = (1 + Γ) / (1 − Γ) mit Γ = U_rev / U_fwd gilt nur für Spannungswerte. Der Code-Kommentar geht von einem quadratischen Detektor aus (P ∝ U²); dann wäre Γ = √(U_rev / U_fwd). Die Kalibrierung muss am echten Gerät erfolgen.

### 3.3 IO-Board (RP2040/Pico) und CW-Keyer

Fakten:
- Das IO-Board hängt am **I2C2-Bus des HL2, Adresse 0x1D** ([Thetis-I2C-Control-Wiki](https://github.com/softerhardware/Hermes-Lite2/wiki/Thetis-I2C-Control)).
- Zugriff erfolgt über **C&C-Adresse 0x3D**: `[31:24]` Cookie (0x06 = Write, 0x07 = Read), `[23]` Stop, `[22:16]` I2C-Adresse, `[15:8]` **8-bit-Registernummer**, `[7:0]` ein Datenbyte. Lesen mit RQST, Antwort in C1–C4 mit ACK.
- Das HL2-Wiki erwähnt einen Extended-Write über Adresse 0x3F + EADDR, die Extended-Memory-Map ist aber nicht definiert. Es gibt keinen dokumentierten Weg, darüber das IO-Board zu erreichen.

❌ **Abweichung im Code:** `HL2IOBoard` und `IOBoard` sprechen das IO-Board über 0x3F + EADDR mit **16-bit-Werten und Registern bis 273** an. Über I2C2 sind nur Registernummern 0–255 und Einzelbytes möglich. Die Keyer-Registermap (200–273, 16 bit) ist so nicht übertragbar.

❌ **Firmware:** `firmware/pico_cw_keyer` nutzt eine Mock-Registerbank im RAM (`g_regs[512]`) und hat **keinen I2C-Slave**. Sie schaltet zwei GPIOs (PTT = GPIO 2, KEY = GPIO 3). Sie ersetzt außerdem die Standard-IO-Board-Firmware; deren Funktionen (Bandausgänge, ATU, Lüfter) wären dann nicht mehr vorhanden.

Die Standard-Register des IO-Boards (0x00–0x04 TX-Frequenz, 0x05 Control, 0x06 Eingänge, 0x07 ATU, 0x08 Fault, 0x09 Firmware) sind im Code so angenommen. Sie sind im HL2-Wiki nicht dokumentiert und müssen gegen die IO-Board-Firmware von N2ADR geprüft werden. Das gilt auch für die ATU-Statuswerte (0xEE, ≥ 0xF0).

**Realistischer CW-Pfad:** Der HL2 hat keinen internen Keyer, erzeugt aber selbst ein **geformtes CW-Signal**, wenn am CN4-Tip getastet wird (Ring = PTT). Der Pico-Keyer sollte deshalb KEY/PTT über Low-Side-Schalter an **CN4** legen. Alternativ gibt es CWX (Adresse 0x0F, Keydown in I[0] des EP2-IQ-Streams).

**Envelope-Shaping:** Die Adressen 0x18/0x19 (`set_cw_envelope`) gibt es in der Standard-HL2-Gateware nicht. Sie existieren nur im eigenen Gateware-Fork ([Hermes-Lite2_DSP PR #1](https://github.com/philibertschlutzki/Hermes-Lite2_DSP/pull/1)). Mit Standard-Gateware greift die eingebaute CW-Formung des HL2.

---

## 4. Audio- und Modulationspfad

### 4.1 Empfang (RX)

Ziel: HL2-IQ → Demodulator auf dem Pi → PipeWire `SDR_RX_Sink` → WSJT-X / fldigi / Tablet.

Ist-Stand:
- ✅ PipeWire-Null-Sinks `SDR_RX_Sink` und `Digital_TX_Sink` (48 kHz, Stereo) werden von `deploy/setup_pipewire_audio.sh` angelegt.
- ❌ Es gibt keinen SSB/DIGU-Demodulator und keinen Code, der Audio in `SDR_RX_Sink` schreibt.
- ⚠️ `hl2_stream.py` hat einen einfachen CW-Mischer. Er liest das IQ-Format falsch (siehe 3.1), liefert 48 kHz an `multimon-ng`, das für Rohdaten 22 050 Hz erwartet, und bindet Port 1024 parallel zum Steuer-Socket auf 1025. Der HL2 bedient nur einen Host-Stream.
- ❌ `AudioStreamer.broadcast_pcm()` wird nirgends aufgerufen. Der WebSocket `/ws/audio` liefert deshalb aktuell kein Audio. Es gibt kein Opus und kein WebRTC; eine Latenzangabe ist noch nicht messbar.

### 4.2 Senden (TX) für Digitalmodi

Der HL2 hat keinen eigenen Modulator für Audio. Der Host muss TX-IQ-Samples kontinuierlich in EP2 senden.

- ❌ Es gibt keinen Code, der Audio aus `Digital_TX_Sink` liest, zu IQ moduliert und an den HL2 schickt. FT8/PSK/RTTY können so noch nicht senden.

---

## 5. Zeitsynchronisation im SOTA-Betrieb

- WSJT-X verlangt laut Handbuch eine Uhr innerhalb von **±1 s** zu UTC. Besser als ±0,1 s ist ein sinnvolles Ziel, aber keine Voraussetzung.
- Der Pi 4B hat keine eingebaute RTC.
- ✅ `deploy/setup_sota_timesync.sh` installiert chrony und gpsd und trägt GPS (SHM 0) und PPS (SHM 1) ein.
- ⚠️ GPS ist dort mit `noselect` eingetragen. Die meisten USB-GPS-Sticks liefern **kein PPS**. Dann hat chrony keine wählbare Quelle und stellt die Uhr nicht. Ohne PPS muss `noselect` beim GPS entfallen.
- ❌ Eine DS3231-RTC ist im Repo nicht konfiguriert (kein `dtoverlay=i2c-rtc,ds3231`).

---

## 6. Netzwerk und Ports

| Dienst | Port | Bindung |
|---|---|---|
| nginx (WebUI + Proxy) | TCP 80 | alle Interfaces |
| FastAPI (uvicorn) | TCP 8000 | 0.0.0.0 |
| CAT (rigctld-kompatibel) | TCP 4532 | 127.0.0.1 |
| WSJT-X UDP | UDP 2237 | 127.0.0.1 |
| fldigi XML-RPC | TCP 7362 | 127.0.0.1 |
| HL2 | UDP 1024 (HL2), 1025 (Pi, Steuerung) | Ethernet |

Die API hat keine Authentifizierung. Das Tablet-WLAN sollte deshalb ein eigenes, geschütztes Netz sein.
