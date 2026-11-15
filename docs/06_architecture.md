# Hermes Lite 2 SOTA & Digital Modes - Technische Systemarchitektur

## 1. Systemübersicht

Dieses System ermöglicht den vollständigen, **headless Remote-Betrieb** des Software Defined Radios **Hermes-Lite 2 (HL2)** über einen **Raspberry Pi 4B (8 GB RAM, Linux ARM64)**, gesteuert durch ein **Android Tablet**.

### Unterstützte Betriebsarten (RX & TX)
- **Narrowband / Text-Modi:**
  - **CW (Morse):** Ausschliesslich textbasiert über Hardware-Keyer (RP2040 Pico) und automatische DSP-Decoder (kein physisches Paddle erforderlich).
  - **PSK31 / PSK63:** BPSK- und QPSK-Modulation via fldigi Headless-Daemon.
  - **RTTY:** Baudot 45.45 Baud / 170 Hz Shift via fldigi.
- **Weak-Signal (WSJT-X Familie):**
  - **FT8, FT4:** Automatisiertes Schnell-QSO-Handling.
  - **WSPR:** Bakenbetrieb für Ausbreitungsstudien.
  - **JT9, JT65:** Ultra-Weak-Signal Modi.
  - **FST4, FST4W:** Niederfrequenz- und Kurzwellen-Spezialmodi.

---

## 2. Architektur-Schichten

```
┌────────────────────────────────────────────────────────┐
│            Android Tablet (Client Endgerät)            │
│  - Touch-Optimiertes Web Cockpit (PWA)                 │
│  - Integrierte Audio-Wiedergabe via Web Audio API      │
│  - One-Touch QSO Steuerung (FT8/FT4/CW/PSK/RTTY)       │
└───────────────────────────▲────────────────────────────┘
                            │ (WLAN: HTTP, WebSocket, WebRTC)
┌───────────────────────────▼────────────────────────────┐
│         Raspberry Pi 4B (Headless Linux ARM64)         │
│                                                        │
│  [ FastAPI Gateway & Telemetrie-Pumpe ]                │
│    ├── Hamlib rigctld CAT Server (TCP 4532)            │
│    ├── WSJT-X UDP Handler (UDP 2237)                   │
│    ├── fldigi XML-RPC Client (HTTP 7362)               │
│    └── Audio Streamer (PCM/Opus -> Tablet)             │
│                                                        │
│  [ PipeWire Virtuelle Audio-Matrix ]                   │
│    ├── SDR_RX_Sink (48 kHz)                            │
│    └── Digital_TX_Sink (48 kHz)                        │
│                                                        │
│  [ HL2 Hardware-Treiber & OpenHPSDR C&C ]              │
│    ├── N2ADR Filter Relais & SWR Bridge                │
│    ├── IO-Board I2C (RP2040: Freq, ATU, PTT, PureSig)  │
│    └── SOTA Pico Keyer (Reg 200..273)                  │
└───────────────────────────▲────────────────────────────┘
                            │ (Ethernet / OpenHPSDR Prot. 1)
┌───────────────────────────▼────────────────────────────┐
│             Hermes Lite 2 Transceiver HW               │
│  - DDC/DUC 12-Bit ADC / DAC Mainboard                  │
│  - N2ADR Filter Board (6x LPF, 1x HPF 3MHz, SWR-Brücke) │
│  - HL2 IO Board (RP2040 Pico via I2C2 Addr 0x1D)       │
└────────────────────────────────────────────────────────┘
```

---

## 3. Hardware-Integration & Registerprotokolle

### 3.1 N2ADR Filter Board
- **Relais-Steuerung via OpenHPSDR Register 0x08 (7-Bit):**
  - `Bit 6`: 3 MHz Hochpassfilter (1 = aktiv bei $\ge 80\,\text{m}$, 0 = Bypass bei $160\,\text{m}$).
  - `Bits 0–5`: 1-aus-6 Tiefpassfilter-Auswahl (160m, 80m, 60/40m, 30/20m, 17/15m, 12/10m).
- **SWR- und Leistungsmessung:**
  - Richtkoppler auf dem Filterboard liefert analoge Spannungen an `AIN1` (Vorwärtsleistung) und `AIN2` (Rückwärtsleistung).
  - Der HL2-ADC überträgt diese Werte in den zyklischen **EP6-Rückmelderahmen**.
  - Berechnung:
    $$\Gamma = \frac{V_{\text{rev}}}{V_{\text{fwd}}}, \quad \text{VSWR} = \frac{V_{\text{fwd}} + V_{\text{rev}}}{V_{\text{fwd}} - V_{\text{rev}}}$$
  - **Schutz-Interlock:** Bei $\text{VSWR} > 3{,}0$ erfolgt ein automatischer Sendestopp.

### 3.2 HL2 IO-Board (RP2040 Pico)
- **Kommunikation:** Über internen I2C-Bus des HL2 (Adresse `0x1D`), getunnelt über HL2 Extended Registers (`0x3F` + EADDR).
- **Standard-Register (`0x00–0x09`):**
  - `0x00–0x04`: 5-Byte Frequenz in Hz (Big Endian). Das Schreiben von Byte 0 triggert die interne Bandcode-Berechnung.
  - `0x05`: Steuerung (Lüfter / Pegel).
  - `0x06`: Hardware-Eingänge (EXTTR, In1..In5, PTT in).
  - `0x07`: Antenna Tuner (ATU) Interface:
    - Write 1: Start Tune; Write 2: Bypass.
    - Status: 0x00 (Fertig), 0xEE (Tuner fordert HF-Träger an), $\ge 0\text{xF0}$ (Fehler).
- **CW Keyer Register (`200–273`):**
  - Bietet mikrosekundengenaues Dit/Dah-Timing, Farnsworth-Spacing, Weighting und HL2 Envelope Shaping (Rise/Fall Zeit zur Vermeidung von Tastklicks).

---

## 4. Audio-Routing & Streaming-Pipeline

1. **Internes Linux-Routing via PipeWire:**
   - Zwei persistente Null-Sinks (`SDR_RX_Sink` und `Digital_TX_Sink`) verbinden das SDR-Backend mit den Digital-Modems (WSJT-X, fldigi) vollkommen verlustfrei und ohne physische Soundkarte.
2. **Audio-Streaming zum Tablet:**
   - WebSocket-Streaming von 16-Bit 48 kHz PCM-Audio direkt in die HTML5 Web Audio API des Browsers auf dem Android Tablet.
   - Latenz im lokalen WLAN: $< 80\,\text{ms}$.

---

## 5. Zeit-Synchronisation im SOTA-Betrieb

WSJT-X (FT8/FT4) erfordert eine Systemzeit-Genauigkeit von besser als $\pm 100\,\text{ms}$.
Im SOTA-Portabelbetrieb ohne Internet wird dies gewährleistet durch:
- **USB-GPS Dongle:** Synchronisiert über `gpsd` und `chrony` mit NMEA- und PPS-Referenztakt.
- **Hardware-RTC (DS3231):** Pufferung der Systemzeit am I2C-Header des Pi 4B.
