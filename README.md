# Hermes Lite 2 SDR SOTA & Digital Modes (HL2 + Raspberry Pi 4B + Android Tablet)

Vollständiges, headless betriebenes SDR-Transceiver-System für den portablen SOTA- und Stationseinsatz mit dem **Hermes-Lite 2 (HL2)**, gesteuert über ein **Android Tablet**.

---

## 1. Systemübersicht & Features

- **Hardware-Basis:**
  - **Transceiver:** Hermes-Lite 2 (DDC/DUC SDR, 160m–10m, ~5 W QRP).
  - **N2ADR Filter Board:** Automatische Relaissteuerung (6x LPF, 1x 3MHz HPF) und Live-SWR-/Leistungsmessung via OpenHPSDR C&C.
  - **HL2 IO-Board (RP2040 Pico):** Hardware-Timing für CW-Tastung, Band-Data-Umschaltung, Lüftersteuerung und Icom AH-4 / Elecraft ATU-Interface.
  - **Host:** Raspberry Pi 4B (8 GB RAM, Linux ARM64, Headless).
  - **Client:** Android Tablet (Touch-Bedienung, On-Screen-Texteingabe, Audio-Streaming auf interne Lautsprecher).

- **Unterstützte Betriebsarten (RX & TX):**
  - **CW (Morse):** 100 % textbasiert über Hardware-Keyer und integrierte Decoder (keine physische Morsetaste/Paddle nötig).
  - **PSK31 / RTTY:** Volle Unterstützung über integrierten Headless-fldigi-Client.
  - **WSJT-X Familie:** FT8, FT4, WSPR, JT9, JT65, FST4 und FST4W mit bidirektionalem UDP-Status und One-Touch-QSO-Antwort.

- **Audio-Routing & Streaming:**
  - Internes, verlustfreies Audio-Routing auf dem Raspberry Pi via **PipeWire** (virtuelle Null-Sinks).
  - Direkte, verzögerungsarme Audioausgabe (< 80 ms) im Tablet-Browser über **HTML5 Web Audio API / WebSockets**.

---

## 2. Repository-Struktur

```
.
├── docs/                      # Detaillierte Dokumentation
│   ├── 00_overview.md         # Übersicht
│   ├── 01_hardware_wiring.md  # Verdrahtungs-Leitfaden
│   ├── 02_bringup_checklist.md# Inbetriebnahmeprüfung
│   ├── 03_ioboard_register_protocol.md # I2C- und Registerprotokolle
│   ├── 04_webui_user_guide.md # Anleitung für das Android Tablet Cockpit
│   ├── 05_troubleshooting.md  # Fehlerbehebung
│   └── 06_architecture.md     # Detaillierte Systemarchitektur
├── firmware/                  # IO-Board Firmware (RP2040)
│   └── pico_cw_keyer/         # Deterministischer Hardware CW-Keyer
├── pi/
│   ├── backend/               # Python FastAPI Backend & Subsysteme
│   │   ├── src/sota_cw/
│   │   │   ├── hardware/      # N2ADR Filter Board, IO-Board, Hamlib rigctld
│   │   │   ├── modems/        # WSJT-X UDP & fldigi XML-RPC Clients
│   │   │   ├── audio/         # Audio Streamer für Tablet Playback
│   │   │   ├── api.py         # REST & WebSocket Endpunkte
│   │   │   ├── cw_jobs.py     # CW Job Manager & Timing
│   │   │   ├── cw_rx.py       # CW Empfangsdecoder
│   │   │   └── qso_bot.py     # Automatisierter SOTA QSO-Bot
│   │   └── requirements.txt
│   └── webui/                 # Touch-optimiertes Frontend für Android Tablet
│       └── static/            # HTML5 / CSS3 (PWA) / Vanilla JS Cockpit
└── deploy/                    # Automatisierte Installationsskripte
    ├── install_full_stack.sh  # Master-Installer für Raspberry Pi OS ARM64
    ├── setup_pipewire_audio.sh# PipeWire Virtual Audio Sinks Setup
    ├── setup_sota_timesync.sh # Chrony + GPS/RTC Offline Time-Sync
    ├── nginx-site.conf        # Nginx Reverse Proxy & WebSocket Config
    └── systemd/               # Systemd Service-Dateien (Backend, WSJT-X, fldigi)
```

---

## 3. Schnelle Inbetriebnahme auf dem Raspberry Pi 4B

```bash
# 1. Repository auf den Raspberry Pi klonen
git clone https://github.com/philibertschlutzki/Hermes_Lite_SDR_SOTA_CW.git
cd Hermes_Lite_SDR_SOTA_CW

# 2. Vollständige Installation ausführen
chmod +x deploy/*.sh
sudo ./deploy/install_full_stack.sh
```

Anschließend das Android Tablet mit dem WLAN des Raspberry Pi verbinden und im Browser öffnen:
```text
http://<raspberry-pi-ip>/
```
