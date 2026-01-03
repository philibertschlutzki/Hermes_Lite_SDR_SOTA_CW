# Raspberry Pi Backend (FastAPI)

Dieses Backend stellt eine kleine REST-API bereit, um:
- HL2 Parameter (Frequenz/Mode) zu setzen (über eine HL2-Library, siehe `third_party/`).
- CW-Jobs über das IO-Board Register-Protokoll zu starten/abzubrechen und Status zu lesen. [file:1]

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
export SOTA_CW_IO_REG_BASE=200
```

## Start

```bash
uvicorn sota_cw.api:app --host 0.0.0.0 --port 8000
```

Dann WebUI öffnen oder Endpunkte testen:
- `GET /health`
- `POST /cw/send`
- `POST /cw/abort`
- `GET /cw/status`
