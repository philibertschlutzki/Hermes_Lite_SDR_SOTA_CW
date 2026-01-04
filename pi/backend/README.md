# Raspberry Pi Backend (FastAPI)

Dieses Backend stellt eine kleine REST-API bereit, um:
- HL2 Parameter (Frequenz/Envelope) über den **integrierten** HL2 UDP Client zu setzen.
- CW-Jobs über das IO-Board Register-Protokoll zu starten/abzubrechen und Status zu lesen.
- Headless IQ-Streamer & Decoder für den direkten Empfang ohne externe SDR-Software.

## Installation

```bash
cd pi/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Konfiguration (Environment)

Beispiele:
```bash
export SOTA_CW_HL2_IP=192.168.1.50
export SOTA_CW_HL2_PORT=1024
export SOTA_CW_HL2_LOCAL_PORT=1025
export SOTA_CW_IO_REG_BASE=200

# Envelope Shaping defaults (optional)
export SOTA_CW_ENV_RISE_US=3000
export SOTA_CW_ENV_FALL_US=3000
export SOTA_CW_ENV_MAX_AMP_Q15=32767
```

Hinweis: `SOTA_CW_HL2_LOCAL_PORT` ist getrennt von 1024 gehalten, damit der Streamer weiterhin Port 1024 binden kann.

## Envelope Shaping (HL2 Gateware)

Das Backend setzt vor jedem CW-Job die HL2-Gateware-Parameter:
- `cmd_addr=0x18`: Rise/Fall (µs)
- `cmd_addr=0x19`: Max-Amplitude (Q1.15)

Die Gateware/DSP-Seite dazu ist im Repo [philibertschlutzki/Hermes-Lite2_DSP](https://github.com/philibertschlutzki/Hermes-Lite2_DSP) umgesetzt.

## Nutzung des Headless Streamers

**Testen (CW Audio hören):**
```bash
python -m sota_cw.hl2_stream --out - --demod cw --pitch 600 | aplay -r 48000 -f S16_LE -c 1
```

**Verwendung mit multimon-ng (Decoder):**
```bash
python -m sota_cw.hl2_stream --out - --demod cw --pitch 600 | multimon-ng -a MORSE_CW -t raw -
```

## Start der API

```bash
uvicorn sota_cw.api:app --host 0.0.0.0 --port 8000
```

Endpunkte testen:
- `GET /health`
- `POST /cw/send`
- `POST /cw/abort`
- `GET /cw/status`
