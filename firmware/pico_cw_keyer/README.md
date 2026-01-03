# pico_cw_keyer (IO-Board Firmware)

Diese Firmware ist ein **Code-Skeleton** für ein RP2040/Pico-basiertes IO-Board: CW-Timing als lokale State-Machine, gesteuert über ein Register-Job-Protokoll ab Register 200. [file:1]

## Build (Pico SDK)

Voraussetzungen:
- Raspberry Pi Pico SDK installiert (`PICO_SDK_PATH`).
- CMake + Ninja/Make.

Beispiel:
```bash
mkdir -p build
cd build
cmake ..
cmake --build .
```

## Integration auf dem HL2 IO-Board

- Die Datei `src/ioboard_regs.h` kapselt den Zugriff auf Register (read/write). [file:1]
- In dieser Repo-Version ist ein "mock"/Platzhalter implementiert; für echtes IO-Board muss der Registerzugriff an das jeweilige HL2/IO-Board Interface angepasst werden. [file:1]

## Pins / Ausgänge

Default-Mapping (anpassen in `src/outputs.c`):
- PTT_OUT: GPIO 2
- KEY_OUT: GPIO 3

Für das echte IO-Board sollen diese Ausgänge die Low-Side-Switches (z. B. OUT1/OUT2) ansteuern. [file:1]
