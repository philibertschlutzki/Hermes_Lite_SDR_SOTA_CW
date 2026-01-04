# Third-party

Dieses Projekt erwartet eine externe HL2-Library für HL2-UDP und IO-Board Register Read/Write (z. B. die Python-Referenz `hermeslite.py`).

## Empfehlung: Submodule

Beispiel (als Submodule, Pfad frei wählbar):

```bash
git submodule add https://github.com/softerhardware/Hermes-Lite2.git third_party/Hermes-Lite2
```

Danach kann aus der jeweiligen Referenz die passende Python-Komponente eingebunden werden (ohne Copy/Paste) und in `pi/backend/src/sota_cw/hl2_control.py` / `ioboard.py` verdrahtet werden.

## HL2 Gateware (Envelope Shaping)

Für **Envelope Shaping / Key-Click-Reduktion** wird eine HL2-interne TX-Amplitudensteuerung benötigt (Multiplikation der TX-I/Q-Samples mit einer Amplitudenrampe statt hartem TX-Gating).

Dieses Repo implementiert dafür die Register-/Backend-Seite (IO-Board Register 270+; Default `env_rise_us=3000`, `env_fall_us=3000`).

Die eigentliche Gateware/DSP-Implementierung ist im HL2-Projekt zu machen und wird hier nur referenziert:
- GitHub: https://github.com/softerhardware/Hermes-Lite2
- Protocol/IO-Board Kontext: https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol
