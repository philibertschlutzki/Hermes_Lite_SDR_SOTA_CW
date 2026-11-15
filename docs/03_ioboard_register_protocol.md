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

## 2. Umsetzung in diesem Repo

| Teil | Stand |
|---|---|
| `pi/backend/src/sota_cw/hl2_client.py` | `i2c_write()` / `i2c_read()` über C&C 0x3D, mit RQST/ACK, höchstens eine offene Anfrage. |
| `pi/backend/src/sota_cw/ioboard.py` | 8-bit-Register, Keyer-Map (unten), `read_cw_status()` mit drei 4-Byte-Reads. |
| `pi/backend/src/sota_cw/hardware/hl2_io_board.py` | Standardregister nach `i2c_registers.h`. |
| `firmware/pico_cw_keyer` | Eigene IO-Board-Firmware: I2C-Slave (i2c1, GPIO 14 SDA / 15 SCL, 0x1D), Standardregister 0–12, Keyer 200–215. |

Der Pico zählt die Registernummer pro gelesenem oder geschriebenem Byte hoch (wie die N2ADR-Firmware). Ausnahme: Das FIFO-Register 210 zählt beim Schreiben nicht weiter.

## 3. Standardregister

Nummern wie in `i2c_registers.h` von [HL2IOBoard](https://github.com/jimahlstrom/HL2IOBoard). Die Keyer-Firmware implementiert davon:

| Register | Name | In dieser Firmware |
|---|---|---|
| 0–4 | `REG_TX_FREQ_BYTE4..0` | TX-Frequenz, Register 0 = höchstes Byte. Write auf 4 übernimmt; HPF (GPIO 0) ein über 2,55 MHz. Der Pi schreibt die Frequenz bei jedem Wechsel. |
| 5 | `REG_CONTROL` | Write 1 setzt Register 0–199 zurück. |
| 6 | `REG_INPUT_PINS` | Bit 0 EXTTR (1 = RX), Bit 1–5 In1–In5. Nur lesen. |
| 7 | `REG_ANTENNA_TUNER` | nur gespeichert, kein ATU-Treiber (G14). |
| 8 | `REG_FAULT` | gespeichert. |
| 9 / 10 | `REG_FIRMWARE_MAJOR/MINOR` | 2 / 0 |
| 11 | `REG_RF_INPUTS` | 0 = normal, 1 = J9, 2 = J9 RX / J10 TX (INTTR GPIO 3, RF3 GPIO 2). |
| 12 | `REG_FAN_SPEED` | 0–255, PWM auf GPIO 4. |

## 4. CW-Keyer-Registermap (200–215)

Definiert in `firmware/pico_cw_keyer/src/ioboard_regs.h`, gespiegelt in `ioboard.py`. Alle Werte 8 bit.

| Reg | Name | R/W | Bedeutung |
|---|---|---|---|
| 200 | `REG_CW_CMD` | W | 0 idle, 1 START, 2 ABORT (Taste sofort los, FIFO leer), 3 CLEAR (FIFO leer, Fehler löschen) |
| 201 | `REG_CW_STATUS` | R | 0 idle, 1 läuft, 2 fertig, 3 abgebrochen, 4 Fehler, 5 Tune |
| 202 | `REG_CW_WPM` | RW | 5–60 |
| 203 | `REG_PTT_LEAD_MS` | RW | PTT-Vorlauf 0–255 ms (Default 80) |
| 204 | `REG_PTT_TAIL_MS` | RW | PTT-Nachlauf 0–255 ms (Default 120) |
| 205 | `REG_FARNSWORTH_WPM` | RW | 0 = wie WPM; sonst werden nur die Abstände gedehnt (ARRL-Verfahren) |
| 206 | `REG_WEIGHT_PCT` | RW | 50 = nominal, 25–75; Key-down länger, Pause gleich viel kürzer |
| 207 | `REG_CW_ERROR` | R | 0 ok, 1 FIFO voll, 2 Host-Watchdog, 3 Tune-Zeit überschritten |
| 208 | `REG_CW_PROGRESS` | R | gesendete Zeichen seit START (mod 256) |
| 209 | `REG_CW_FIFO_LEVEL` | R | Zeichen im FIFO (max. 255) |
| 210 | `REG_CW_FIFO_DATA` | W | ASCII-Zeichen anhängen (auch während des Sendens) |
| 211 | `REG_CW_HEARTBEAT` | W | beliebiger Wert; jeder I2C-Write zählt als Lebenszeichen |
| 212 | `REG_CW_WATCHDOG_S` | RW | 1–30 s ohne Write → Taste und PTT los, Fehler 2 (Default 3) |
| 213 | `REG_CW_KEY_DIRECT` | RW | 1 = Dauerträger (Tune), 0 = aus; max. 15 s |
| 214 | `REG_CW_API_VERSION` | R | 1 |
| 215 | `REG_CW_MAGIC` | R | 0xC5 (Erkennung der Keyer-Firmware) |

Ablauf eines Auftrags (`cw_jobs.submit_job`): CMD=3, Parameter, Zeichen nach 210, CMD=1. Während des Sendens schreibt der Pi alle 0,5 s Register 211 und liest den Status.

Geschwindigkeit: Jeder Write ist ein C&C-Frame mit RQST und wird vom HL2 bestätigt. Bei 48 kHz sind das etwa 190 Writes/s, ein Text mit 50 Zeichen ist in rund 0,3 s im Pico.

## Weiterführende Links

- HL2 Repo: https://github.com/softerhardware/Hermes-Lite2
- HL2 Protocol Wiki: https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol
- HL2 IO Board: https://github.com/jimahlstrom/HL2IOBoard
