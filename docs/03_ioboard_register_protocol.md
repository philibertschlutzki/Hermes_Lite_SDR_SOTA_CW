# IO-Board Register/Protokoll (Entwickler & Debug)

Diese Seite ist für alle, die verstehen wollen, wie das IO-Board angesprochen wird, oder die Backend und Firmware erweitern.

## 1. Wie der Host das IO-Board erreicht (HL2-Fakten)

Das IO-Board hat keine eigene Netzwerkverbindung. Der Pi spricht mit dem HL2 per openHPSDR Protocol 1, und der HL2 leitet Befehle über seinen **I2C2-Bus** an das IO-Board weiter.

- I2C2, 7-bit-Adresse **0x1D** = IO-Board ([Thetis-I2C-Control-Wiki](https://github.com/softerhardware/Hermes-Lite2/wiki/Thetis-I2C-Control)).
- Auf demselben Bus: N2ADR-Filterboard (0x20) und das PA-Bias-Poti.
- Befehl über C&C-Adresse **0x3D** (I2C1 wäre 0x3C), Datenwort C1–C4:

| Bits | Inhalt |
|---|---|
| `[31:24]` | Cookie: `0x06` = Write, `0x07` = Read |
| `[23]` | Stop (1 = Stop-Condition) |
| `[22:16]` | I2C-Geräteadresse (0x1D) |
| `[15:8]` | Registernummer (8 bit, 0–255) |
| `[7:0]` | Datenbyte (nur bei Write) |

- **Lesen:** C0 Bit 7 (RQST) setzen, Cookie 0x07. Der HL2 antwortet mit ACK und liefert die Bytes in C1–C4. Ein Fehler kommt als Antwort mit RADDR 0x3F.
- **Schreiben:** ein Byte pro Befehl, optional mit RQST als Bestätigung.

Folge: Register sind **8 bit breit und 0–255 adressiert**. 16-bit-Werte müssen als zwei Bytes in zwei Registern liegen.

Das HL2-Wiki erwähnt einen Extended-Write über Adresse 0x3F + EADDR, die zugehörige Memory-Map ist aber nicht definiert. Er ist kein dokumentierter Weg zum IO-Board.

## 2. Ist-Stand in diesem Repo

| Teil | Stand |
|---|---|
| `pi/backend/src/sota_cw/hl2_client.py` | Schreibt/liest 16-bit-Werte über 0x3F + EADDR. Passt nicht zu Abschnitt 1. |
| `pi/backend/src/sota_cw/ioboard.py`, `hardware/hl2_io_board.py` | Nutzen diesen Weg für Standard- und CW-Register. |
| `firmware/pico_cw_keyer` | Mock-Registerbank im RAM, kein I2C-Slave. Läuft eigenständig auf einem Pico, ist aber nicht vom HL2 aus erreichbar. |

Was zu tun ist, steht in [07_known_gaps.md](07_known_gaps.md) (G7–G9, G12).

## 3. Standard-Register des IO-Boards (Annahme im Code)

Diese Belegung nutzt `hardware/hl2_io_board.py`. Sie ist im HL2-Wiki nicht dokumentiert und muss gegen die Firmware des IO-Boards (N2ADR) geprüft werden.

| Register | Inhalt laut Code |
|---|---|
| 0x00–0x04 | TX-Frequenz in Hz, 5 Byte, MSB zuerst. Das Schreiben des LSB (Register 0x04) löst die Bandberechnung aus. |
| 0x05 | Control (Lüfter) |
| 0x06 | Eingänge (EXTTR, In1–In5, PTT) |
| 0x07 | ATU: Write 1 = Tune, 2 = Bypass; Status 0x00 fertig, 0xEE Träger angefordert, ≥ 0xF0 Fehler |
| 0x08 | Fault-Code |
| 0x09 | Firmware-Version |

Wichtig: Wird die Pico-Firmware des IO-Boards durch `pico_cw_keyer` ersetzt, fallen diese Standardfunktionen weg, solange der Keyer sie nicht mit übernimmt.

## 4. CW-Registermap (dieses Repo)

Basis `CW_REG_BASE = 200` (`firmware/pico_cw_keyer/src/ioboard_regs.h`). Werte sind in der Firmware als 16-bit-Register angelegt.

### Steuerung (200–209)

| Reg | Name | Bedeutung |
|---|---|---|
| 200 | `REG_CW_CMD` | 0 = IDLE, 1 = START, 2 = ABORT |
| 201 | `REG_CW_STATUS` | 0 = IDLE, 1 = RUNNING, 2 = DONE, 3 = ABORTED, 4 = ERROR |
| 202 | `REG_CW_WPM` | Tempo |
| 203 | `REG_PTT_LEAD_MS` | PTT-Vorlauf (Default 80) |
| 204 | `REG_PTT_TAIL_MS` | PTT-Nachlauf (Default 120) |
| 205 | `REG_TEXT_LEN` | Textlänge (max. 120) |
| 206 | `REG_PROGRESS` | Fortschritt |
| 207 | `REG_ERROR_CODE` | Fehlercode |
| 208 | `REG_FARNSWORTH_WPM` | 0 = wie WPM |
| 209 | `REG_WEIGHT_PCT` | 50 = nominal |

### Textpuffer (210–269)

2 ASCII-Zeichen pro 16-bit-Register (High-Byte zuerst), `TEXT_MAX_CHARS = 120` → 60 Register.

### Envelope-Parameter (270–273)

| Reg | Name | Default |
|---|---|---|
| 270 | `REG_CW_RISE_US` | 3000 |
| 271 | `REG_CW_FALL_US` | 3000 |
| 272 | `REG_CW_ENV_SHAPE` | 0 = linear |
| 273 | `REG_CW_ENV_MAX_AMP_Q15` | 32767 |

Der Pico selbst nutzt diese Werte nicht; er schaltet KEY nur hart ein und aus. Die Formung des HF-Signals macht der HL2. Mit Standard-Gateware greift dessen eingebaute CW-Formung; die einstellbaren Werte (C&C 0x18/0x19) gibt es nur im eigenen Gateware-Fork ([third_party/README.md](../third_party/README.md)).

### Konflikt mit Abschnitt 1

Mit 8-bit-Registern bis 255 passt diese Map nicht über I2C: Register 256–273 sind nicht adressierbar, und jeder 16-bit-Wert braucht zwei Register. Für eine echte Umsetzung muss die Map neu geschnitten werden, z. B. 8-bit-Steuerregister ab 200 und der Text als Bytestrom in ein einzelnes FIFO-Register.

## Weiterführende Links

- HL2 Repo: https://github.com/softerhardware/Hermes-Lite2
- HL2 Protocol Wiki: https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol
- Diskussion zu IO-Board-Registerbereichen: https://groups.google.com/g/hermes-lite/c/zVF4yR1VyjA
