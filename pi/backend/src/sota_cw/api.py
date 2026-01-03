from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .config import settings
from .hl2_control import HL2Control
from .ioboard import IOBoard
from .cw_jobs import CWJob, submit_job, abort_job

app = FastAPI(title="HL2 SOTA CW API")

hl2 = HL2Control(ip=settings.hl2_ip, port=settings.hl2_port)
io = IOBoard(reg_base=settings.io_reg_base)


class FrequencyRequest(BaseModel):
    hz: int = Field(..., ge=100_000, le=60_000_000)


class ModeRequest(BaseModel):
    mode: str


class CWSendRequest(BaseModel):
    text: str
    wpm: int = Field(20, ge=5, le=60)
    ptt_lead_ms: int = Field(80, ge=0, le=5000)
    ptt_tail_ms: int = Field(120, ge=0, le=5000)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/hl2/frequency")
def set_frequency(req: FrequencyRequest):
    hl2.set_frequency_hz(req.hz)
    return {"ok": True}


@app.post("/hl2/mode")
def set_mode(req: ModeRequest):
    hl2.set_mode(req.mode)
    return {"ok": True}


@app.post("/cw/send")
def cw_send(req: CWSendRequest):
    job = CWJob(text=req.text, wpm=req.wpm, ptt_lead_ms=req.ptt_lead_ms, ptt_tail_ms=req.ptt_tail_ms)
    submit_job(io, job)
    return {"ok": True}


@app.post("/cw/abort")
def cw_abort():
    abort_job(io)
    return {"ok": True}


@app.get("/cw/status")
def cw_status():
    st = io.read_cw_status()
    return st.__dict__
