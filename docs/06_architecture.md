# SOTA CW HL2 Backend - Technical Architecture

## Overview

The SOTA CW HL2 backend provides a REST API for controlling the Hermes Lite 2 SDR for portable SOTA CW operation. It includes automated QSO handling, CW decoding, and TX quality testing infrastructure.

## Architecture Layers

### 1. Transport Layer
- **HL2Client** (`hl2_client.py`): Low-level UDP communication with HL2
  - Metis protocol implementation
  - Command & Control (C&C) register access
  - Extended register addressing for IO board

### 2. Radio Control Layer
- **HL2Control** (`hl2_control.py`): Radio-level abstractions
  - Frequency control (TX/RX NCOs)
  - Mode management (CW/USB/LSB)
  - CW envelope shaping parameters
- **IOBoard** (`ioboard.py`): IO board register interface
  - CW keyer control (via registers)
  - Status monitoring
  - No HL2-specific side effects (clean separation)

### 3. Business Logic Layer
- **CWJobManager** (`cw_jobs.py`): TX job lifecycle
  - Job submission and sequencing
  - Parameter validation and defaults
  - HL2 envelope programming
- **CWDecoder** (`cw_rx.py`): RX pipeline
  - multimon-ng integration
  - Internal streamer (hl2_stream) or external audio
  - Text buffer management
- **QSOBot** (`qso_bot.py`): Automated QSO state machine
  - State transitions (IDLE → CQ → LISTEN → REPORT → LOG)
  - Callsign extraction
  - Timeout handling

### 4. API Layer
- **FastAPI app** (`api.py`): REST endpoints
  - TX routes (`/cw/send`, `/cw/abort`, `/cw/status`)
  - RX routes (`/cw/rx/start`, `/cw/rx/stop`, `/cw/rx/text`)
  - Bot routes (`/bot/configure`, `/bot/start`, `/bot/cq`)
  - Diagnostics (`/health`, `/healthz`, `/diag`)
  - Log export (`/log/export/csv`, `/log/export/adif`)

## Configuration Management

### Centralized Settings (`config.py`)
Uses Pydantic Settings for type-safe configuration:

```python
from sota_cw.config import settings

# Access configuration
hl2_ip = settings.hl2_ip
log_level = settings.log_level
```

**Environment Variables** (prefix: `SOTA_CW_`):
- `SOTA_CW_HL2_IP` - HL2 IP address (default: 192.168.1.50)
- `SOTA_CW_HL2_PORT` - HL2 port (default: 1024)
- `SOTA_CW_LOG_LEVEL` - Logging level (default: INFO)
- See `.env.example` for full list

### Configuration Profiles
Future enhancement: Load different profiles for:
- SOTA/portable: Minimal CPU, offline mode, fixed bands
- Lab/bench: Full features, debug logging
- Contest: Quick macros, efficient logging

## Logging

### Unified Logging (`logging_config.py`)
Structured logging with consistent format:

```
2026-01-04 19:00:00 - sota_cw.api - INFO - Starting SOTA CW HL2 Backend
2026-01-04 19:00:01 - sota_cw.qso_bot - INFO - QSO Bot started
```

**Features**:
- Configurable log level via `SOTA_CW_LOG_LEVEL`
- Optional request ID for API calls
- Module-level logger instances

## Error Handling

### Current State
- Basic HTTP exceptions (HTTPException with status codes)
- Module-specific error handling (try/except in critical paths)

### Future Improvements
Define unified exception hierarchy:

```python
class SOTACWError(Exception):
    """Base exception for SOTA CW errors"""
    pass

class HL2CommunicationError(SOTACWError):
    """HL2 communication failed"""
    http_code = 503
    
class IOBoardError(SOTACWError):
    """IO board communication failed"""
    http_code = 503
    
class InvalidJobError(SOTACWError):
    """Invalid CW job parameters"""
    http_code = 400
```

## Dependency Injection

### Current Implementation
Modules create their own dependencies at import time:

```python
# api.py
hl2_client = HL2Client(settings.hl2_ip, settings.hl2_port)
hl2 = HL2Control(..., client=hl2_client)
io_board = IOBoard(hl2_client, ...)
cw_manager = CWJobManager(io_board, hl2=hl2)
```

**Pros**: Simple, works for single-instance application  
**Cons**: Hard to test, tight coupling

### Future Improvements
Use dependency injection for better testability:

```python
from fastapi import Depends

def get_hl2_client() -> HL2Client:
    return HL2Client(settings.hl2_ip, settings.hl2_port)

@app.post("/cw/send")
def send_cw(req: CWSendRequest, hl2: HL2Client = Depends(get_hl2_client)):
    # Use injected hl2
    pass
```

## State Management

### Current State
- Bot state: In-memory (QSOBot instance)
- CW job state: IO board registers (persistent across restarts)
- RX buffer: In-memory deque (lost on restart)
- QSO log: File-based (sota_log.csv)

### Future Improvements
- **Persistent bot state**: Save/restore bot config and QSO history
- **Database integration**: Optional SQLite for logs and state
- **Redis/cache layer**: For distributed deployments (future)

## Testing Strategy

### Unit Tests (31 tests passing)
- **QSO Bot** (12 tests): State transitions, callsign extraction
- **CW Jobs** (11 tests): Job creation, scheduling, IO board writes
- **HL2 Stream** (8 tests): FIR filter, DSP, synthetic IQ

### Integration Tests (planned)
- FastAPI endpoints with TestClient
- Full TX/RX pipeline with mocked hardware
- Bot end-to-end QSO sequence

### System Tests (manual)
- Hardware-in-loop with actual HL2
- Real CW decoding with multimon-ng
- TX quality measurements (NanoVNA-H4)

## Deployment

### Development
```bash
cd pi/backend
pip install -r requirements.txt -r requirements-dev.txt
make run
```

### Production (Headless)
```bash
# Create .env file with configuration
cp .env.example .env
nano .env

# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn sota_cw.api:app --host 0.0.0.0 --port 8000

# Or use systemd (see docs/deployment.md for systemd unit file)
```

### Docker (future)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ src/
CMD ["uvicorn", "sota_cw.api:app", "--host", "0.0.0.0"]
```

## Performance Considerations

### CPU Usage
- **DSP (hl2_stream)**: FIR filtering is CPU-intensive
  - Optimized with NumPy (BLAS/LAPACK)
  - Acceptable on Raspberry Pi 3B+ or newer
- **Decoder (multimon-ng)**: External process, moderate CPU
- **Bot**: Minimal CPU (sleep-based polling)

### Memory Usage
- IQ buffer: Streaming, no large accumulation
- RX text buffer: Bounded (deque with maxlen)
- No memory leaks detected in testing

### Network
- HL2 UDP: Low bandwidth (~10 KB/s for IQ stream)
- API: RESTful, stateless (except WebSocket if added)

## Security Considerations

### Current State
- No authentication on API endpoints
- Runs on local network (192.168.x.x)
- No encryption (HTTP, not HTTPS)

### Recommendations for Deployment
1. **Network isolation**: Keep on private VLAN
2. **Firewall**: Restrict API access to known clients
3. **Authentication**: Add API key or OAuth for internet exposure
4. **HTTPS**: Use reverse proxy (nginx) with TLS

### Hardware Safety
- Software interlocks (planned):
  - Prevent TX when config invalid
  - Detect PTT flapping
  - Timeout on long TX (overheating protection)

## Extensibility

### Adding New Features
1. **New API endpoint**: Add route in `api.py`
2. **New hardware interface**: Create module similar to `ioboard.py`
3. **New bot behavior**: Extend `qso_bot.py` state machine
4. **New decoder**: Implement adapter in `cw_rx.py`

### Plugin System (future)
```python
# Example plugin interface
class SOTACWPlugin:
    def on_startup(self, app): pass
    def on_qso_complete(self, qso): pass
    def on_tx_start(self, job): pass
```

## Documentation

### Current Documentation
- `docs/` - User guides (hardware, bringup, troubleshooting)
- `docs/tx_quality_nanovna_h4.md` - TX test plan
- `docs/test_reports/` - Test data and schemas
- This file - Technical architecture

### API Documentation
Auto-generated at `/docs` (FastAPI Swagger UI) and `/redoc` (ReDoc)

Access at: `http://<raspberry_pi_ip>:8000/docs`

## Future Roadmap

### High Priority
- [ ] WebUI integration (React/Vue frontend)
- [ ] Enhanced bot logic (QRL?, QRS, partial decodes)
- [ ] Systemd service files
- [ ] Deployment documentation

### Medium Priority
- [ ] Database integration (SQLite)
- [ ] Config profiles (SOTA/portable/lab)
- [ ] Software interlocks
- [ ] Harmonics/TX quality self-test

### Low Priority
- [ ] WebSocket streaming (real-time RX text)
- [ ] Docker deployment
- [ ] Multi-HL2 support
- [ ] Remote operation (VPN/SSH tunnel)
