# Third-party

Dieses Projekt erwartet eine externe HL2-Library für HL2-UDP (IQ Stream) sowie Write/Read von Control/Command-Frames.

## Empfehlung: Submodule

Beispiel (als Submodule, Pfad frei wählbar):

```bash
git submodule add https://github.com/softerhardware/Hermes-Lite2.git third_party/Hermes-Lite2
```

Danach kann aus der jeweiligen Referenz die passende Python-Komponente eingebunden werden (ohne Copy/Paste) und in `pi/backend/src/sota_cw/hl2_control.py` / `ioboard.py` verdrahtet werden.

## HL2 Gateware (Envelope Shaping)

Für **Envelope Shaping / Key-Click-Reduktion** wird eine TX-Amplitudenrampe benötigt (Soft-Keying), d. h. die CW-TX-Amplitude wird nicht hart ge-gated, sondern per Rampe hoch/runter gefahren.

### Implementierung (Gateware/DSP)

Die Gateware/DSP-Seite ist in diesem Fork umgesetzt:
- Gateware/DSP Repo: [philibertschlutzki/Hermes-Lite2_DSP](https://github.com/philibertschlutzki/Hermes-Lite2_DSP)
- PR: [CW envelope shaping: configurable rise/fall/max amplitude](https://github.com/philibertschlutzki/Hermes-Lite2_DSP/pull/1)

### Schnittstelle (Control/Command)

Die Parameter werden im FPGA im `radio`-Modul (`gateware/rtl/radio_openhpsdr1/radio.v`) über die bestehende Command-Schnittstelle gesetzt:

- `cmd_addr = 0x18` (`ENV_CFG0`)
  - `cmd_data[15:0]`  = `env_rise_us` (µs)
  - `cmd_data[31:16]` = `env_fall_us` (µs)
- `cmd_addr = 0x19` (`ENV_CFG1`)
  - `cmd_data[15:0]`  = `env_max_amp_q15` (Q1.15; `0x7FFF` = 1.0)

Defaults:
- `env_rise_us=3000`
- `env_fall_us=3000`
- `env_max_amp_q15=0x7FFF`

### Upstream-Kontext

- Upstream HL2 Projekt: [softerhardware/Hermes-Lite2](https://github.com/softerhardware/Hermes-Lite2)
- Protokoll/IO-Kontext: [Hermes-Lite2 Wiki / Protocol](https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol)
