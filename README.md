# Hermes Lite 2 SOTA CW (HL2 + Raspberry Pi + HL2 IO Board)

Ziel dieses Repos ist ein leichtgewichtiges Setup für SOTA/portable Betrieb mit **Hermes Lite 2** (HL2):
- Smartphone/Web-UI im WLAN zur Band-/Frequenz-/Mode-Steuerung und CW-Makros.
- **Automatische CW-Dekodierung** und **Automatisierter QSO-Betrieb** (Bot).
- CW-Timing lokal auf dem IO-Board (RP2040/Pico), während der Raspberry Pi nur Jobs/Parameter setzt.

## Neue Features (QSO Automatisierung & Headless RX)
Das System kann nun nicht nur senden, sondern auch empfangen und selbstständig QSOs führen:
*   **CW RX Decoder**: Nutzt `multimon-ng` im Hintergrund, um Audiosignale in Text zu wandeln.
*   **Headless IQ Streamer**: Integriertes Python-Modul `hl2_stream` empfängt IQ-Daten direkt vom HL2, demoduliert CW und füttert den Decoder – keine externen SDR-Tools (wie Quisk/SDR++) mehr nötig!
*   **FIR-Filtering**: Integrierte Signalverarbeitung für saubere CW-Töne und besseres SNR.
*   **QSO Bot**: Eine State-Machine, die CQ ruft, auf Antworten wartet, Rapporte (599) austauscht und das QSO loggt.

## Repository Struktur

```
.
├── docs/                   # Dokumentation
│   └── 01_hardware_wiring.md
├── firmware/              # IO-Board Firmware (RP2040)
│   └── pico_cw_keyer/
├── pi/
│   ├── backend/           # Python FastAPI Backend
│   │   ├── src/sota_cw/
│   │   │   ├── api.py           # REST Endpoints
│   │   │   ├── cw_jobs.py       # TX Job Management
│   │   │   ├── cw_rx.py         # RX Decoder Integration (Multimon-ng)
│   │   │   ├── hl2_stream.py    # Headless IQ Receiver & Demodulator
│   │   │   ├── qso_bot.py       # QSO State Machine
│   │   │   └── ...
│   │   ├── requirements.txt
│   │   └── README.md
│   └── webui/             # HTML/JS Frontend
└── third_party/           # Externe Referenzen/Libs
```

## Quickstart (Überblick)

1.  **Hardware aufbauen & verdrahten**: siehe `docs/01_hardware_wiring.md`.
2.  **Software Voraussetzungen**:
    ```bash
    sudo apt update
    sudo apt install multimon-ng alsa-utils
    # Backend dependencies installieren (inkl. numpy für DSP)
    cd pi/backend && pip install -r requirements.txt
    ```
3.  **Firmware bauen/flashen**: siehe `firmware/pico_cw_keyer/README.md`.
4.  **Backend starten**: siehe `pi/backend/README.md`.
    *   Standardmäßig ist nun der interne Streamer aktiviert (`USE_INTERNAL_STREAMER=True`).
5.  **WebUI öffnen**: siehe `pi/webui/README.md`.

## Feature Roadmap

### Phase 1: Basics (Abgeschlossen)
- [x] Hardware-Setup & IO-Board Firmware
- [x] Grundlegendes Web-Interface
- [x] Manuelles Senden von CW-Texten

### Phase 2: RX & Automation (Abgeschlossen)
- [x] Integration von `multimon-ng` als CW-Decoder
- [x] Backend API für RX-Text Stream
- [x] Basis QSO-Bot (CQ -> Antwort -> 599 -> Log)
- [x] **Headless IQ Streamer**: Native Python Integration für IQ-Empfang.
- [x] **DSP Filter**: FIR Lowpass Filterung für verbesserten Empfang.

### Phase 3: Verfeinerung (Laufend)
- [ ] **Web-UI Integration**: GUI-Elemente für Bot-Start/Stop und RX-Text-Anzeige fertigstellen.
- [ ] **SOTA CSV Export**: Download des Logs direkt über das Web-UI.
- [ ] **Erweiterte Bot-Logik**: Umgang mit "QRL?", "QRS" und RBN-Spotting.

## Lizenz / Third-Party

Siehe `third_party/README.md` für die empfohlene Einbindung der HL2-Python-Referenz.
