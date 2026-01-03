# Hermes Lite 2 SOTA CW (HL2 + Raspberry Pi + HL2 IO Board)

Ziel dieses Repos ist ein leichtgewichtiges Setup für SOTA/portable Betrieb mit **Hermes Lite 2** (HL2):
- Smartphone/Web-UI im WLAN zur Band-/Frequenz-/Mode-Steuerung und CW-Makros.
- **Automatische CW-Dekodierung** und **Automatisierter QSO-Betrieb** (Bot).
- CW-Timing lokal auf dem IO-Board (RP2040/Pico), während der Raspberry Pi nur Jobs/Parameter setzt.

## Neue Features (QSO Automatisierung & Headless RX)
Das System kann nun nicht nur senden, sondern auch empfangen und selbstständig QSOs führen:
*   **CW RX Decoder**: Nutzt `multimon-ng` im Hintergrund, um Audiosignale in Text zu wandeln.
*   **Headless IQ Streamer**: Integriertes Python-Modul `hl2_stream` empfängt IQ-Daten direkt vom HL2, demoduliert CW und füttert den Decoder – keine externen SDR-Tools (wie Quisk/SDR++) mehr nötig!
*   **QSO Bot**: Eine State-Machine, die CQ ruft, auf Antworten wartet, Rapporte (599) austauscht und das QSO loggt.

## Architektur

*   **Frontend**: Web-UI (HTML/JS) zur Steuerung von Frequenz, Bot-Config und Anzeige des RX-Textes.
*   **Backend**: Python FastAPI.
    *   `cw_jobs.py`: Steuert den RP2040 für perfektes Sende-Timing.
    *   `cw_rx.py`: Wrappt `multimon-ng` für den Empfang.
    *   `hl2_stream.py`: **NEU** Direkter UDP IQ-Empfang und Demodulation.
    *   `qso_bot.py`: Logik für den QSO-Ablauf.
*   **Hardware**: HL2 + IO-Board + Raspberry Pi.

## Quickstart (Überblick)

1.  **Hardware aufbauen & verdrahten**: siehe `docs/01_hardware_wiring.md`.
2.  **Software Voraussetzungen**:
    ```bash
    sudo apt update
    sudo apt install multimon-ng alsa-utils
    # Für den neuen Streamer:
    # (wird via pip install -r requirements.txt installiert: numpy)
    ```
3.  **Firmware bauen/flashen**: siehe `firmware/pico_cw_keyer/README.md`.
4.  **Backend starten**: siehe `pi/backend/README.md`.
5.  **WebUI öffnen**: siehe `pi/webui/README.md`.

## Feature Roadmap

### Phase 1: Basics (Abgeschlossen)
- [x] Hardware-Setup & IO-Board Firmware
- [x] Grundlegendes Web-Interface
- [x] Manuelles Senden von CW-Texten

### Phase 2: RX & Automation (Aktuell)
- [x] Integration von `multimon-ng` als CW-Decoder
- [x] Backend API für RX-Text Stream
- [x] Basis QSO-Bot (CQ -> Antwort -> 599 -> Log)

### Phase 3: Verfeinerung (Laufend)
- [x] **Audio-Pipeline**: Integration eines headless SDR-Empfängers (`hl2_stream.py`) direkt in das Startskript, um IQ-Daten ohne externe Tools zu verarbeiten.
- [ ] **Web-UI Integration**: GUI-Elemente für Bot-Start/Stop und RX-Text-Anzeige fertigstellen.
- [ ] **SOTA CSV Export**: Download des Logs direkt über das Web-UI.
- [ ] **Erweiterte Bot-Logik**: Umgang mit "QRL?", "QRS" und RBN-Spotting.

## Lizenz / Third-Party

Siehe `third_party/README.md` für die empfohlene Einbindung der HL2-Python-Referenz.
