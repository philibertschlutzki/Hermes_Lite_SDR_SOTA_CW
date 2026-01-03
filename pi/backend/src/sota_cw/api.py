from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .cw_jobs import CWJobManager
from .cw_rx import CWDecoder
from .hl2_control import HL2Control
from .ioboard import IOBoard
from .config import HL2_IP, HL2_PORT, IO_REG_BASE
from .qso_bot import QSOBot, BotConfig

app = FastAPI(title="SOTA CW HL2 Backend")

# Initialize components
hl2 = HL2Control(HL2_IP, HL2_PORT)
io_board = IOBoard(IO_REG_BASE)
cw_manager = CWJobManager(io_board)
cw_decoder = CWDecoder()

# Bot Default Config
default_bot_config = BotConfig(
    my_call="NOCALL", # User must configure this
    my_ref="",
    wpm=20
)
qso_bot = QSOBot(cw_manager, cw_decoder, default_bot_config)


# Models
class CWSendRequest(BaseModel):
    text: str
    wpm: int = 20

class BotConfigRequest(BaseModel):
    my_call: str
    my_ref: str
    wpm: int

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

# --- Bot Routes ---

@app.post("/bot/configure")
def configure_bot(config: BotConfigRequest):
    qso_bot.config.my_call = config.my_call
    qso_bot.config.my_ref = config.my_ref
    qso_bot.config.wpm = config.wpm
    return {"status": "configured", "config": qso_bot.config}

@app.post("/bot/start")
def start_bot():
    """Starts the bot thread (IDLE state)"""
    qso_bot.start()
    return {"status": "bot_started"}

@app.post("/bot/stop")
def stop_bot():
    """Stops the bot thread"""
    qso_bot.stop()
    return {"status": "bot_stopped"}

@app.post("/bot/cq")
def trigger_cq():
    """Triggers the CQ sequence immediately"""
    if not qso_bot.running:
        raise HTTPException(status_code=400, detail="Bot not running. Call /bot/start first.")
    qso_bot.trigger_cq()
    return {"status": "cq_triggered"}

@app.get("/bot/state")
def get_bot_state():
    return {
        "state": qso_bot.state.name,
        "running": qso_bot.running,
        "partner": qso_bot.current_partner_call
    }


# Lifecycle
@app.on_event("startup")
def startup_event():
    # Start RX by default for convenience
    cw_decoder.start()
    # Start Bot thread (IDLE)
    qso_bot.start()

@app.on_event("shutdown")
def shutdown_event():
    cw_decoder.stop()
    qso_bot.stop()
