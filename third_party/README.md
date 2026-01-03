# Third-party

Dieses Projekt erwartet eine externe HL2-Library für HL2-UDP und IO-Board Register Read/Write (z. B. die Python-Referenz `hermeslite.py`). [file:1]

## Empfehlung: Submodule

Beispiel (als Submodule, Pfad frei wählbar):

```bash
git submodule add https://github.com/softerhardware/Hermes-Lite2.git third_party/Hermes-Lite2
```

Danach kann aus der jeweiligen Referenz die passende Python-Komponente eingebunden werden (ohne Copy/Paste) und in `pi/backend/src/sota_cw/hl2_control.py` / `ioboard.py` verdrahtet werden. [file:1]
