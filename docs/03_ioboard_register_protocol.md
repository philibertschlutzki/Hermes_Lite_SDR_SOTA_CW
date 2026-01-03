# IO-Board Register-Protokoll (CW Jobs)

Dieses Dokument definiert ein **reserviertes Register-Fenster** (ab 200), damit CW-Job-Funktionalität nicht mit vorhandenen IO-Board-Features kollidiert. [file:1]

## Registerbereich

- Basisadresse: `200` (dezimal). [file:1]
- Register sind 16-bit (0..65535) gedacht; Text wird als ASCII in 16-bit Wörtern gepackt (2 Zeichen pro Register). [file:1]

## Kommandos

- `CW_CMD = 0`: Idle
- `CW_CMD = 1`: Start Job (Firmware liest Parameter & Textbuffer)
- `CW_CMD = 2`: Abort (Firmware stoppt sofort, setzt Status)

## Register Map

| Register | Name | R/W | Bedeutung |
|---:|---|:---:|---|
| 200 | CW_CMD | R/W | 0=Idle, 1=Start, 2=Abort. |
| 201 | CW_STATUS | R | 0=Idle, 1=Running, 2=Done, 3=Aborted, 4=Error. |
| 202 | CW_WPM | R/W | Words per minute (typ. 5..40). |
| 203 | PTT_LEAD_MS | R/W | PTT Vorlaufzeit in ms. |
| 204 | PTT_TAIL_MS | R/W | PTT Nachlaufzeit in ms. |
| 205 | TEXT_LEN | R/W | Anzahl ASCII-Zeichen (max. `TEXT_MAX_CHARS`). |
| 206 | PROGRESS | R | Fortschritt: index in Zeichen (0..TEXT_LEN). |
| 207 | ERROR_CODE | R | 0=ok, sonst Fehlercode. |
| 208.. | TEXT_BUF | R/W | Textbuffer (2 ASCII pro Register, HighByte/LowByte). |

## Text Packing

- `TEXT_BUF[i]` enthält zwei Zeichen: High-Byte = Zeichen `2*i`, Low-Byte = Zeichen `2*i+1`. [file:1]
- Bei ungerader Länge wird das letzte Low-Byte mit `0x00` gepaddet. [file:1]

## Ablauf (State Machine)

1. Host schreibt Parameter + Textbuffer, dann `CW_CMD=1`. [file:1]
2. Firmware setzt `CW_STATUS=Running`, toggelt PTT/KEY gemäss Timing, aktualisiert `PROGRESS`. [file:1]
3. Am Ende setzt Firmware `CW_STATUS=Done` und `CW_CMD=0`. [file:1]
4. Bei Abort: Host setzt `CW_CMD=2`, Firmware stoppt, `CW_STATUS=Aborted`, `CW_CMD=0`. [file:1]
