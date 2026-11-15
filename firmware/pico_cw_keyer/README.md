# pico_cw_keyer (IO-Board-Firmware)

Firmware für den Raspberry Pi Pico auf dem HL2-IO-Board (N2ADR). Sie ersetzt die Standardfirmware und macht den Pico zum CW-Keyer, der vom Raspberry Pi **nur über das Netzwerkkabel** gesteuert wird:

```
Pi --Protocol 1 (C&C 0x3D)--> HL2 --I2C2, Adresse 0x1D--> Pico --J6 Out7/Out8--> HL2 CN4 Tip/Ring
```

- I2C-Slave an `i2c1` (GPIO 14 SDA, GPIO 15 SCL), Adresse 0x1D, 400 kHz
- Standardregister 0–12 (TX-Frequenz, Eingänge, Lüfter, RF-Eingänge, HPF), Nummern wie `i2c_registers.h` der N2ADR-Firmware
- Keyer ab Register 200: Text-FIFO (255 Zeichen), WPM, Farnsworth, Gewichtung, PTT-Vor-/Nachlauf, Tune
- Sicherheit: ABORT lässt die Taste sofort im I2C-Interrupt los; Host-Watchdog (Standard 3 s ohne I2C-Write); Tune max. 15 s; Hardware-Watchdog 200 ms; beim Start sind alle Ausgänge aus

Registermap: [docs/03_ioboard_register_protocol.md](../../docs/03_ioboard_register_protocol.md). Verdrahtung: [docs/01_hardware_wiring.md](../../docs/01_hardware_wiring.md).

Nicht enthalten (gegenüber der N2ADR-Firmware): ATU-Treiber, Bandausgänge für Endstufen, Band-Spannung auf J4 Pin 8.

## Aufbau

| Datei | Inhalt |
|---|---|
| `src/keyer.c/.h` | Plattformunabhängig: Registerbank, I2C-Ereignisse, Morse-Zustandsautomat |
| `src/cw_morse.c/.h` | Zeichentabelle |
| `src/main.c` | Pico-Anbindung: Pins, I2C-Slave, PWM, Watchdog, Hauptschleife |
| `src/ioboard_regs.h` | Registermap (gespiegelt in `pi/backend/src/sota_cw/ioboard.py`) |
| `test/test_keyer.c` | Host-Tests (Timing PARIS, Wortabstand, ABORT, Watchdog, Tune, FIFO) |

## Bauen

Host-Tests (ohne Pico SDK):

```bash
make -C test test
```

Firmware (Pico SDK ≥ 2.0, `arm-none-eabi-gcc`):

```bash
export PICO_SDK_PATH=/pfad/zum/pico-sdk
cmake -S . -B build -G Ninja      # optional: -DKEY_GPIO=22 -DPTT_GPIO=8
cmake --build build
# Ergebnis: build/pico_cw_keyer.uf2
```

Die CI baut die UF2 bei jedem Push (Artefakt `pico_cw_keyer-uf2`).

## Flashen

BOOTSEL gedrückt halten, Pico per USB an einen Rechner, `pico_cw_keyer.uf2` auf das Laufwerk `RPI-RP2` kopieren. Danach USB wieder abziehen.

Kontrolle im Betrieb: `GET /hardware/ioboard/status` → `keyer_present: true`, `firmware_version: 2`.
