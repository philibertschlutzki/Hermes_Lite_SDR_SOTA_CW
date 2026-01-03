# Überblick

Dieses Projekt stellt ein schlankes, portables Bedienkonzept für den **Hermes Lite 2 (HL2)** bereit: Raspberry Pi als "Control-Plane" (API/Web) und HL2 IO-Board (RP2040/Pico) als "Realtime-Plane" (CW-Keying). [file:1]

## Architektur

- Raspberry Pi: REST API (FastAPI) + statische Web-UI (Smartphone). [file:1]
- HL2: HF-Frontend/SDR; Kommunikation typischerweise über HL2-UDP-Protokoll (z. B. via `hermeslite.py`). [file:1]
- HL2 IO-Board: Schaltet PTT/KEY über Low-Side-Switch-Ausgänge und führt CW-Timing lokal aus (Pico-Firmware). [file:1]

## Designprinzipien

- CW-Timing **nicht** auf dem Pi (Jitter/Latency), sondern als Job/Parameter an das IO-Board (Register) übergeben. [file:1]
- Keine Third-Party-Quelltexte in dieses Repo kopieren; stattdessen referenzieren/einbinden. [file:1]
