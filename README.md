# Hermes Lite 2 SOTA CW (HL2 + Raspberry Pi + HL2 IO Board)

Ziel dieses Repos ist ein leichtgewichtiges Setup für SOTA/portable Betrieb mit **Hermes Lite 2** (HL2):
- Smartphone/Web-UI im WLAN zur Band-/Frequenz-/Mode-Steuerung und CW-Makros.
- CW-Timing lokal auf dem IO-Board (RP2040/Pico), während der Raspberry Pi nur Jobs/Parameter setzt.

## Projektstatus

- Dieses Repository ist als Bau-/Bring-up-Paket aufgebaut: Hardware-Verdrahtung, Checklisten, sowie Code-Skeletons für Firmware und Raspberry‑Pi‑Software.
- Die eigentliche HL2-UDP/IO-Board-Kommunikation ist bewusst als "Third-Party" Referenz/Einbindung vorgesehen (kein Copy/Paste fremder Quelltexte im Repo).

## Ordnerstruktur

```text
README.md
docs/                  Anleitungen (Wiring, Bring-up, Troubleshooting)
firmware/pico_cw_keyer  RP2040/Pico Firmware: CW-Keyer + Register-Interface
pi/backend              FastAPI Backend (REST) für WebUI/Automatisierung
pi/webui                Statische Weboberfläche (HTML/JS/CSS)
deploy/                 systemd/nginx/install Skripte
third_party/            Hinweise zur Einbindung externer HL2-Libs
```

## Quickstart (Überblick)

1. **Hardware aufbauen & verdrahten**: siehe `docs/01_hardware_wiring.md`.
2. **Bring-up**: HL2 erreichbar machen, IO-Board Read/Write testen, erst dann CW-Jobs: siehe `docs/02_bringup_checklist.md`.
3. **Firmware bauen/flashen**: siehe `firmware/pico_cw_keyer/README.md`.
4. **Backend starten**: siehe `pi/backend/README.md`.
5. **WebUI öffnen**: siehe `pi/webui/README.md`.

## Lizenz / Third-Party

Siehe `third_party/README.md` für die empfohlene Einbindung der HL2-Python-Referenz (z. B. als Submodule oder vendor import).
