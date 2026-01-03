# Raspberry Pi Backend (FastAPI)

Dieses Backend stellt eine kleine REST-API bereit, um:
- HL2 Parameter (Frequenz/Mode) zu setzen (über eine HL2-Library, siehe `third_party/`).
- CW-Jobs über das IO-Board Register-Protokoll zu starten/abzubrechen und Status zu lesen.
- **NEU:** Headless IQ-Streamer & Decoder für den direkten Empfang ohne externe SDR-Software.

## Installation

```bash
cd pi/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Hinweis**: Für den internen Streamer wird `numpy` benötigt (in requirements.txt enthalten).

## Konfiguration (Environment)

Beispiele:
```bash
export SOTA_CW_HL2_IP=192.168.1.50
export SOTA_CW_HL2_PORT=1024
export SOTA_CW_IO_REG_BASE=200
```

## Nutzung des Headless Streamers

Das Backend enthält nun ein Modul `hl2_stream`, das IQ-Daten direkt vom HL2 empfängt, demoduliert und ausgibt.

**Testen (CW Audio hören):**
```bash
# Gibt Audio (CW Sidetone) auf stdout aus -> aplay
python -m sota_cw.hl2_stream --out - --demod cw --pitch 600 | aplay -r 48000 -f S16_LE -c 1
```

**Verwendung mit multimon-ng (Decoder):**
```bash
python -m sota_cw.hl2_stream --out - --demod cw --pitch 600 | multimon-ng -a MORSE_CW -t raw -
```

**IQ-Recording (Raw Data):**
```bash
python -m sota_cw.hl2_stream --out my_capture.iq
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
