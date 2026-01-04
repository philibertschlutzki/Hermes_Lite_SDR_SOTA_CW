# IO-Board Register/Protokoll (Entwickler & Debug)

Diese Seite ist für alle, die verstehen wollen, wie das IO-Board per Register angesprochen wird, oder die Backend/WebUI erweitern möchten.

## Kontext: HL2 Protokoll
Der Hermes-Lite-2 ist kompatibilitätsorientiert aufgebaut und lehnt sich an openHPSDR „protocol1“/Metis an; Details inkl. Board_ID und Paketstruktur stehen im HL2-Wiki.

## Registermodell (typisches Muster)
Viele IO-Board-Firmwares nutzen ein statisches Register-Array (z. B. 256 Bytes), in das geschrieben und aus dem gelesen werden kann; ohne Zusatzlogik liefert ein Read oft einfach den zuletzt geschriebenen Wert zurück.

## Register-Namensraum / Kollisionen vermeiden
Wenn mehrere Tools/Backends Register nutzen, ist es sinnvoll, „höhere“ Register (z. B. ab 200) für projektspezifische Features zu verwenden und die Nutzung zu dokumentieren, um Kollisionen zu vermeiden.

## CW Registermap (dieses Repo)

CW-Registerbasis ist `CW_REG_BASE=200` (siehe `firmware/pico_cw_keyer/src/ioboard_regs.h`).

### Basis-Register (200..)
- 200: `REG_CW_CMD` (0=IDLE, 1=START, 2=ABORT)
- 201: `REG_CW_STATUS` (0=IDLE, 1=RUNNING, 2=DONE, 3=ABORTED, 4=ERROR)
- 202: `REG_CW_WPM`
- 203: `REG_PTT_LEAD_MS`
- 204: `REG_PTT_TAIL_MS`
- 205: `REG_TEXT_LEN`
- 206: `REG_PROGRESS`
- 207: `REG_ERROR_CODE`
- 208: `REG_FARNSWORTH_WPM`
- 209: `REG_WEIGHT_PCT`

### Textpuffer (210..)
`REG_TEXT_BUF=210`, 2 ASCII pro 16-bit Register, Länge: `TEXT_MAX_CHARS=120` → 60 Register (210..269).

### Envelope Shaping (270..)
Diese Register sind für Key-Click-Reduktion gedacht. Dieses Repo schreibt sie; die HL2-Gateware muss sie auswerten.

- 270: `REG_CW_RISE_US` – Rise-Time in µs (Default 3000)
- 271: `REG_CW_FALL_US` – Fall-Time in µs (Default 3000)
- 272: `REG_CW_ENV_SHAPE` – 0=linear (Default 0)
- 273: `REG_CW_ENV_MAX_AMP_Q15` – Max-Amplitude (Q1.15; Default 32767)

## Weiterführende Links
- HL2 Repo: https://github.com/softerhardware/Hermes-Lite2
- HL2 Protocol Wiki: https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol
- Diskussion/Best-Practice zu IO-Board-Registerarrays und Registerbereichen: https://groups.google.com/g/hermes-lite/c/zVF4yR1VyjA
