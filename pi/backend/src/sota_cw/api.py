from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .cw_jobs import CWJobManager
from .cw_rx import CWDecoder
from .hl2_client import HL2Client
from .hl2_control import HL2Control
from .ioboard import IOBoard
from .config import (
    HL2_IP,
    HL2_PORT,
    HL2_LOCAL_PORT,
    IO_REG_BASE,
    CW_ENV_RISE_US,
    CW_ENV_FALL_US,
    CW_ENV_SHAPE,
    CW_ENV_MAX_AMP_Q15,
)
from .qso_bot import QSOBot, BotConfig

app = FastAPI(title="SOTA CW HL2 Backend")

# Initialize HL2 client + abstractions
hl2_client = HL2Client(HL2_IP, HL2_PORT, local_port=HL2_LOCAL_PORT)
hl2 = HL2Control(HL2_IP, HL2_PORT, client=hl2_client, local_port=HL2_LOCAL_PORT)
io_board = IOBoard(hl2_client, IO_REG_BASE)

# CW manager defaults are configurable via env vars.
cw_manager = CWJobManager(
    io_board,
    hl2=hl2,
    default_env_rise_us=CW_ENV_RISE_US,
    default_env_fall_us=CW_ENV_FALL_US,
    default_env_shape=CW_ENV_SHAPE,
    default_env_max_amp_q15=CW_ENV_MAX_AMP_Q15,
)

cw_decoder = CWDecoder()

# Bot Default Config
default_bot_config = BotConfig(
    my_call="NOCALL",  # User must configure this
    my_ref="",
    wpm=20
)
qso_bot = QSOBot(cw_manager, cw_decoder, default_bot_config)


# Models
class CWSendRequest(BaseModel):
    text: str
    wpm: int = 20

    ptt_lead_ms: int = 80
    ptt_tail_ms: int = 120

    farnsworth_wpm: int = Field(default=0, ge=0, le=60)
    weight_pct: int = Field(default=50, ge=0, le=100)

    # Envelope shaping (HL2-side amplitude control)
    env_rise_us: int = Field(default=CW_ENV_RISE_US, ge=0, le=20000)
    env_fall_us: int = Field(default=CW_ENV_FALL_US, ge=0, le=20000)
    env_shape: int = Field(default=CW_ENV_SHAPE, ge=0, le=10)
    env_max_amp_q15: int = Field(default=CW_ENV_MAX_AMP_Q15, ge=0, le=32767)


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
    job_id = cw_manager.start_job(
        req.text,
        req.wpm,
        ptt_lead_ms=req.ptt_lead_ms,
        ptt_tail_ms=req.ptt_tail_ms,
        farnsworth_wpm=req.farnsworth_wpm,
        weight_pct=req.weight_pct,
        env_rise_us=req.env_rise_us,
        env_fall_us=req.env_fall_us,
        env_shape=req.env_shape,
        env_max_amp_q15=req.env_max_amp_q15,
    )
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
    cw_decoder.start()
    return {"status": "rx_started"}


@app.post("/cw/rx/stop")
def stop_rx():
    cw_decoder.stop()
    return {"status": "rx_stopped"}


@app.get("/cw/rx/text")
def get_rx_text():
    return {
        "lines": cw_decoder.get_text(),
        "running": cw_decoder.running,
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
    qso_bot.start()
    return {"status": "bot_started"}


@app.post("/bot/stop")
def stop_bot():
    qso_bot.stop()
    return {"status": "bot_stopped"}


@app.post("/bot/cq")
def trigger_cq():
    if not qso_bot.running:
        raise HTTPException(status_code=400, detail="Bot not running. Call /bot/start first.")
    qso_bot.trigger_cq()
    return {"status": "cq_triggered"}


@app.get("/bot/state")
def get_bot_state():
    return {
        "state": qso_bot.state.name,
        "running": qso_bot.running,
        "partner": qso_bot.current_partner_call,
    }


# Lifecycle
@app.on_event("startup")
def startup_event():
    # Ensure HL2 is running (watchdog disabled for headless operation).
    hl2.start(disable_watchdog=True)

    # Program default envelope once at startup.
    hl2.set_cw_envelope(
        rise_us=CW_ENV_RISE_US,
        fall_us=CW_ENV_FALL_US,
        max_amp_q15=CW_ENV_MAX_AMP_Q15,
    )

    cw_decoder.start()
    qso_bot.start()


@app.on_event("shutdown")
def shutdown_event():
    cw_decoder.stop()
    qso_bot.stop()
