from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .cw_jobs import CWJobManager
from .cw_rx import CWDecoder
from .hl2_control import HL2Control
from .ioboard import IOBoard
from .config import HL2_IP, HL2_PORT, IO_REG_BASE

app = FastAPI(title="SOTA CW HL2 Backend")

# Initialize components
hl2 = HL2Control(HL2_IP, HL2_PORT)
io_board = IOBoard(IO_REG_BASE)
cw_manager = CWJobManager(io_board)
cw_decoder = CWDecoder()

# Models
class CWSendRequest(BaseModel):
    text: str
    wpm: int = 20

@app.get("/health")
def health():
    return {"status": "ok", "hl2": hl2.ip}

# --- TX Routes ---

@app.post("/cw/send")
def send_cw(req: CWSendRequest):
    job_id = cw_manager.start_job(req.text, req.wpm)
    return {"job_id": job_id, "status": "started"}

@app.post("/cw/abort")
def abort_cw():
    cw_manager.abort_job()
    return {"status": "aborted"}

@app.get("/cw/status")
def get_status():
    return cw_manager.get_status()

# --- RX Routes ---

@app.post("/cw/rx/start")
def start_rx():
    """Startet den Hintergrundprozess für multimon-ng"""
    cw_decoder.start()
    return {"status": "rx_started"}

@app.post("/cw/rx/stop")
def stop_rx():
    """Stoppt den Decoder"""
    cw_decoder.stop()
    return {"status": "rx_stopped"}

@app.get("/cw/rx/text")
def get_rx_text():
    """Holt die letzten decodierten Textzeilen"""
    return {
        "lines": cw_decoder.get_text(),
        "running": cw_decoder.running
    }

@app.post("/cw/rx/clear")
def clear_rx_text():
    cw_decoder.clear_text()
    return {"status": "cleared"}

# Lifecycle
@app.on_event("startup")
def startup_event():
    # Optional: Auto-start decoder on boot
    # cw_decoder.start()
    pass

@app.on_event("shutdown")
def shutdown_event():
    cw_decoder.stop()
