from __future__ import annotations

import asyncio
import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import settings
from .cw_jobs import CWJobManager, TxNotAllowed
from .cw_rx import CWDecoder
from .hl2_client import HL2Client
from .hl2_control import HL2Control
from .hardware.n2adr_filter import N2ADRFilterBoard
from .hardware.hl2_io_board import HL2IOBoard
from .hardware.cat_server import HamlibCatServer
from .modems.wsjtx_client import WSJTXClient, WSJTXDecode
from .modems.fldigi_client import FldigiClient
from .audio.audio_streamer import AudioStreamer
from .audio.radio_audio import RxAudioPipeline, TxAudioPipeline
from .logging_config import setup_logging, get_logger
from .qso_bot import QSOBot, BotConfig

# Initialize logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Hermes Lite 2 SDR SOTA & Digital Modes Backend",
    version="1.0.0",
    description="Headless SDR control for CW, FT8, FT4, WSPR, PSK31, and RTTY with N2ADR and IO Board integration."
)

# -----------------------------------------------------------------------------
# Optionaler Zugriffsschutz (B4): Token im Header X-API-Token oder ?token=
# -----------------------------------------------------------------------------
_OPEN_PATHS = ("/health", "/healthz")


def _token_ok(token: str | None) -> bool:
    return not settings.api_token or token == settings.api_token


@app.middleware("http")
async def api_token_middleware(request: Request, call_next):
    path = request.url.path
    if settings.api_token and path not in _OPEN_PATHS and not path.startswith("/webui"):
        token = request.headers.get("x-api-token") or request.query_params.get("token")
        if not _token_ok(token):
            return JSONResponse(status_code=401, content={"detail": "API-Token fehlt oder falsch"})
    return await call_next(request)


async def _ws_accept(websocket: WebSocket) -> bool:
    if not _token_ok(websocket.query_params.get("token")):
        await websocket.close(code=4401)
        return False
    await websocket.accept()
    return True


# -----------------------------------------------------------------------------
# System Initialization
# -----------------------------------------------------------------------------
# Ein einziger Protocol-1-Socket für Steuerung, IQ und TX (G6)
hl2_client = HL2Client(settings.hl2_ip, settings.hl2_port, local_port=settings.hl2_local_port)

n2adr_board = N2ADRFilterBoard(
    max_vswr_threshold=settings.max_vswr_threshold,
    power_cal_factor=settings.power_cal_factor,
    detector_law=settings.power_detector_law,
)
io_board = HL2IOBoard(hl2_client, cw_reg_base=settings.io_reg_base)

hl2 = HL2Control(
    settings.hl2_ip,
    settings.hl2_port,
    client=hl2_client,
    n2adr=n2adr_board,
    io_board=io_board if settings.io_board_enabled else None,
    custom_gateware_envelope=settings.hl2_custom_gateware_envelope,
    trip_count=settings.swr_trip_count,
    drive_level=settings.hl2_drive_level,
    cw_hang_ms=settings.hl2_cw_hang_ms,
)

cw_manager = CWJobManager(
    io_board,
    hl2=hl2,
    default_env_rise_us=settings.cw_env_rise_us,
    default_env_fall_us=settings.cw_env_fall_us,
    default_env_shape=settings.cw_env_shape,
    default_env_max_amp_q15=settings.cw_env_max_amp_q15,
    watchdog_s=settings.cw_watchdog_s,
)


def _on_swr_trip(reason: str) -> None:
    # Der Pico tastet CN4 über das Keying-Kabel; nur er kann eine laufende CW-Aussendung beenden
    try:
        cw_manager.abort_job()
        cw_manager.tune(False)
    except Exception as e:
        logger.error(f"CW-Abbruch nach SWR-Trip fehlgeschlagen: {e}")


hl2.add_trip_callback(_on_swr_trip)

cw_decoder = CWDecoder()

default_bot_config = BotConfig(
    my_call="NOCALL",
    my_ref="",
    wpm=20
)
qso_bot = QSOBot(cw_manager, cw_decoder, default_bot_config)

# Digital Modems & Audio
wsjtx_client = WSJTXClient(host=settings.wsjtx_host, port=settings.wsjtx_port)
fldigi_client = FldigiClient(host=settings.fldigi_host, port=settings.fldigi_port)
audio_streamer = AudioStreamer(sample_rate=settings.audio_sample_rate)

rx_audio = RxAudioPipeline(
    mode=hl2.mode,
    cw_pitch_hz=settings.cw_pitch_hz,
    sink_cmd=settings.rx_audio_sink_cmd if settings.pipewire_enabled else None,
)
tx_audio = TxAudioPipeline(
    source_cmd=settings.tx_audio_source_cmd if settings.pipewire_enabled else None,
    gain=settings.tx_audio_gain,
)
rx_audio.add_consumer(audio_streamer.feed_audio)
rx_audio.add_consumer(lambda a: cw_decoder.feed_audio(a) if hl2.mode in ("CWU", "CWL") else None)
hl2_client.add_iq_callback(rx_audio.on_iq)
hl2_client.set_tx_source(tx_audio.tx_source)


def _on_mode(mode: str) -> None:
    rx_audio.set_mode(mode)
    tx_audio.set_mode(mode)


hl2.add_mode_callback(_on_mode)
_on_mode(hl2.mode)
cat_server = HamlibCatServer(hl2=hl2, host=settings.cat_server_host, port=settings.cat_server_port)


# -----------------------------------------------------------------------------
# Pydantic Request Models
# -----------------------------------------------------------------------------
class FrequencyRequest(BaseModel):
    hz: int = Field(..., ge=100000, le=60000000, description="Frequency in Hertz")


class ModeRequest(BaseModel):
    mode: str = Field(..., description="Operating mode: CWU, CWL, USB, LSB, DIGU, AM, SAM")


class PttRequest(BaseModel):
    ptt: bool = Field(..., description="Set Transmit (MOX) state")


class CWSendRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=255)
    wpm: int = Field(default=20, ge=5, le=60)
    ptt_lead_ms: int = Field(default=80, ge=0, le=255)
    ptt_tail_ms: int = Field(default=120, ge=0, le=255)
    farnsworth_wpm: int = Field(default=0, ge=0, le=60)
    weight_pct: int = Field(default=50, ge=25, le=75)
    env_rise_us: int = Field(default=3000, ge=0, le=20000)
    env_fall_us: int = Field(default=3000, ge=0, le=20000)
    env_shape: int = Field(default=0, ge=0, le=10)
    env_max_amp_q15: int = Field(default=32767, ge=0, le=32767)


class CWAppendRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=255)


class TuneRequest(BaseModel):
    enable: bool
    max_s: float = Field(default=10.0, gt=0, le=15)


class BotConfigRequest(BaseModel):
    my_call: str
    my_ref: str
    wpm: int


class WSJTXReplyRequest(BaseModel):
    time_str: str
    snr_db: int
    delta_time_s: float
    delta_freq_hz: int
    mode: str
    message: str
    raw_time_ms: int = 0


class WSJTXFreeTextRequest(BaseModel):
    text: str
    send: bool = False


class FldigiSendRequest(BaseModel):
    text: str


class FldigiModemRequest(BaseModel):
    modem: str  # BPSK31, RTTY, CW


class AudioVolumeRequest(BaseModel):
    volume: float = Field(..., ge=0.0, le=2.0)


# -----------------------------------------------------------------------------
# Core Diagnostics & Health Endpoints
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "hl2_ip": settings.hl2_ip,
        "n2adr_active": settings.n2adr_enabled,
        "io_board_active": settings.io_board_enabled,
    }


@app.get("/healthz")
def healthz():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/diag")
def diagnostics():
    cw_status = cw_manager.get_status()
    bot_state = {
        "state": qso_bot.state.name,
        "running": qso_bot.running,
        "partner": qso_bot.current_partner_call,
    }
    band_info = hl2.get_band_info()
    return {
        "status": "ok",
        "hl2": {
            "ip": settings.hl2_ip,
            "port": settings.hl2_port,
            "freq_hz": hl2.frequency_hz,
            "mode": hl2.mode,
            "band": band_info.name,
            "transmitting": hl2.is_transmitting,
            **hl2.status(),
        },
        "n2adr": {
            "band": band_info.name,
            "relay_word": hex(n2adr_board.current_relay_word),
            "hpf_active": band_info.enable_hpf,
            "last_swr": n2adr_board.last_measurement.__dict__ if n2adr_board.last_measurement else None,
        },
        "io_board": io_board.get_status().__dict__,
        "cw_status": cw_status,
        "wsjtx": wsjtx_client.get_status_dict(),
        "fldigi": {
            "connected": fldigi_client.is_connected,
            "modem": fldigi_client.current_modem,
            "transmitting": fldigi_client.is_transmitting,
        },
        "bot": bot_state,
    }


@app.get("/diag/tx_test_plan")
def tx_test_plan():
    cw_status = cw_manager.get_status()
    band_info = hl2.get_band_info()
    return {
        "test_plan_version": "1.0",
        "test_plan_doc": "docs/tx_quality_nanovna_h4.md",
        "current_configuration": {
            "tx_mode": "CW_CARRIER" if hl2.is_transmitting else "IDLE",
            "band_m": band_info.name,
            "tx_freq_hz": hl2.frequency_hz,
            "tx_power_setting_w": 5.0,
            "cw_wpm": cw_status.get("wpm", 20),
            "cw_farnsworth_wpm": 0,
            "cw_weight_pct": 50,
            "ptt_lead_ms": cw_status.get("ptt_lead_ms", 80),
            "ptt_tail_ms": cw_status.get("ptt_tail_ms", 120),
            "env_rise_us": settings.cw_env_rise_us,
            "env_fall_us": settings.cw_env_fall_us,
            "env_max_amp_q15": settings.cw_env_max_amp_q15,
        },
        "recommended_attenuator": {
            "total_db_nominal": 50.0,
            "configuration": "20dB + 20dB + 10dB",
            "safety_margin_db": 13.0,
        },
        "test_checklist": [
            {"step": 1, "name": "Attenuator Characterization", "required": True, "status": "pending"},
            {"step": 2, "name": "S11 Measurement (Matching)", "required": True, "status": "pending"},
            {"step": 3, "name": "TX Frequency Verification", "required": True, "status": "pending"},
            {"step": 4, "name": "Filter Performance (N2ADR)", "required": True, "status": "pending"},
        ],
    }


# -----------------------------------------------------------------------------
# HL2 Control Endpoints (Frequenz, Mode, PTT)
# -----------------------------------------------------------------------------
@app.post("/hl2/frequency")
def set_frequency(req: FrequencyRequest):
    hl2.set_frequency_hz(req.hz)
    return {"status": "ok", "frequency_hz": hl2.frequency_hz, "band": hl2.get_band_info().name}


@app.get("/hl2/frequency")
def get_frequency():
    return {"frequency_hz": hl2.frequency_hz, "band": hl2.get_band_info().name}


@app.post("/hl2/mode")
def set_mode(req: ModeRequest):
    try:
        hl2.set_mode(req.mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "mode": hl2.mode}


@app.get("/hl2/mode")
def get_mode():
    return {"mode": hl2.mode}


@app.post("/hl2/ptt")
def set_ptt(req: PttRequest):
    try:
        hl2.set_ptt(req.ptt)
    except PermissionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"status": "ok", "transmitting": hl2.is_transmitting}


@app.get("/hl2/swr")
def get_swr():
    meas = n2adr_board.last_measurement
    return {
        "tripped": hl2.swr_tripped,
        "reason": hl2.swr_trip_reason,
        "threshold": n2adr_board.max_vswr_threshold,
        "measurement": meas.__dict__ if meas else None,
        "raw": {"fwd": hl2.telemetry.fwd_power_raw, "rev": hl2.telemetry.rev_power_raw},
    }


@app.post("/hl2/swr/reset")
def reset_swr():
    hl2.reset_swr_trip()
    return {"status": "ok", "tripped": hl2.swr_tripped}


@app.get("/hl2/status")
def get_hl2_status():
    return hl2.status()


# -----------------------------------------------------------------------------
# Hardware Subsystem Endpoints (N2ADR & IO Board)
# -----------------------------------------------------------------------------
@app.get("/hardware/n2adr/status")
def get_n2adr_status():
    band = hl2.get_band_info()
    meas = n2adr_board.last_measurement
    return {
        "band": band.name,
        "lpf_relay_bit": band.lpf_relay_bit,
        "hpf_enabled": band.enable_hpf,
        "relay_word": hex(n2adr_board.current_relay_word),
        "measurement": meas.__dict__ if meas else None,
    }


@app.get("/hardware/ioboard/status")
def get_ioboard_status():
    return io_board.get_status().__dict__


@app.post("/hardware/ioboard/atu/tune")
def trigger_atu_tune():
    try:
        io_board.start_atu_tune()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"IO-Board nicht erreichbar: {e}")
    return {"status": "tune_started"}


@app.post("/hardware/ioboard/atu/bypass")
def trigger_atu_bypass():
    try:
        io_board.bypass_atu()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"IO-Board nicht erreichbar: {e}")
    return {"status": "bypassed"}


# -----------------------------------------------------------------------------
# CW Subsystem Endpoints (Pico Keyer & Decoder)
# -----------------------------------------------------------------------------
@app.post("/cw/send")
def send_cw(req: CWSendRequest):
    try:
        job_id = _start_cw(req)
    except TxNotAllowed as e:
        raise HTTPException(status_code=409, detail=str(e))
    except (ConnectionError, TimeoutError, RuntimeError) as e:
        raise HTTPException(status_code=503, detail=f"Keyer nicht erreichbar: {e}")
    return {"job_id": job_id, "status": "started"}


def _start_cw(req: CWSendRequest) -> int:
    return cw_manager.start_job(
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


@app.post("/cw/append")
def append_cw(req: CWAppendRequest):
    try:
        n = cw_manager.append(req.text)
    except TxNotAllowed as e:
        raise HTTPException(status_code=409, detail=str(e))
    except (ConnectionError, TimeoutError, RuntimeError) as e:
        raise HTTPException(status_code=503, detail=f"Keyer nicht erreichbar: {e}")
    return {"status": "appended", "chars": n}


@app.post("/cw/abort")
def abort_cw():
    try:
        cw_manager.abort_job()
    except (ConnectionError, TimeoutError, RuntimeError) as e:
        raise HTTPException(status_code=503, detail=f"Keyer nicht erreichbar: {e}")
    return {"status": "aborted"}


@app.post("/cw/tune")
def tune_cw(req: TuneRequest):
    """Dauerträger über den Pico-Keyer (z. B. für einen externen Tuner)."""
    try:
        cw_manager.tune(req.enable, max_s=req.max_s)
    except TxNotAllowed as e:
        raise HTTPException(status_code=409, detail=str(e))
    except (ConnectionError, TimeoutError, RuntimeError) as e:
        raise HTTPException(status_code=503, detail=f"Keyer nicht erreichbar: {e}")
    return {"status": "tune_on" if req.enable else "tune_off"}


@app.get("/cw/status")
def get_cw_status():
    return cw_manager.get_status()


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


# -----------------------------------------------------------------------------
# CW QSO Bot Endpoints
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# WSJT-X (Weak-Signal) Endpoints
# -----------------------------------------------------------------------------
@app.get("/wsjtx/status")
def get_wsjtx_status():
    return wsjtx_client.get_status_dict()


@app.get("/wsjtx/decodes")
def get_wsjtx_decodes():
    return [d.__dict__ for d in wsjtx_client.get_decodes()]


@app.post("/wsjtx/reply")
def reply_wsjtx(req: WSJTXReplyRequest):
    dec = WSJTXDecode(
        time_str=req.time_str,
        snr_db=req.snr_db,
        delta_time_s=req.delta_time_s,
        delta_freq_hz=req.delta_freq_hz,
        mode=req.mode,
        message=req.message,
        raw_time_ms=req.raw_time_ms,
    )
    wsjtx_client.reply_to_decode(dec)
    return {"status": "reply_sent"}


@app.post("/wsjtx/halt")
def halt_wsjtx():
    wsjtx_client.halt_tx()
    return {"status": "halt_sent"}


@app.post("/wsjtx/freetext")
def freetext_wsjtx(req: WSJTXFreeTextRequest):
    wsjtx_client.set_free_text(req.text, send=req.send)
    return {"status": "freetext_sent"}


@app.post("/wsjtx/clear")
def clear_wsjtx():
    wsjtx_client.clear_decodes()
    return {"status": "cleared"}


# -----------------------------------------------------------------------------
# fldigi (PSK31 / RTTY) Endpoints
# -----------------------------------------------------------------------------
@app.get("/fldigi/status")
def get_fldigi_status():
    return {
        "connected": fldigi_client.is_connected,
        "modem": fldigi_client.current_modem,
        "transmitting": fldigi_client.is_transmitting,
        "rx_text": fldigi_client.get_rx_text(),
    }


@app.post("/fldigi/modem")
def set_fldigi_modem(req: FldigiModemRequest):
    ok = fldigi_client.set_modem(req.modem)
    return {"status": "ok" if ok else "failed", "modem": fldigi_client.current_modem}


@app.post("/fldigi/send")
def send_fldigi_text(req: FldigiSendRequest):
    ok = fldigi_client.send_text(req.text)
    return {"status": "ok" if ok else "failed"}


@app.post("/fldigi/abort")
def abort_fldigi():
    ok = fldigi_client.abort_tx()
    return {"status": "ok" if ok else "failed"}


@app.post("/fldigi/clear")
def clear_fldigi_rx():
    fldigi_client.clear_rx_text()
    return {"status": "cleared"}


# -----------------------------------------------------------------------------
# Audio Endpoints
# -----------------------------------------------------------------------------
@app.post("/audio/volume")
def set_audio_volume(req: AudioVolumeRequest):
    audio_streamer.set_volume(req.volume)
    return {"status": "ok", "volume": audio_streamer.volume}


# -----------------------------------------------------------------------------
# Log Export Routes (SOTA CSV & ADIF)
# -----------------------------------------------------------------------------
@app.get("/log/export/csv")
def export_log_csv():
    from fastapi.responses import StreamingResponse
    log_file = "sota_log.csv"
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="No log file found. Complete QSOs first.")

    def generate():
        with open(log_file, "r") as f:
            content = f.read()
            if not content.startswith("date,time"):
                yield "date,time,callsign,mode,sent,rcvd\n"
            yield content

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sota_log.csv"}
    )


@app.get("/log/export/adif")
def export_log_adif():
    from fastapi.responses import Response
    log_file = "sota_log.csv"
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="No log file found. Complete QSOs first.")

    adif_records = [
        "ADIF Export from SOTA CW HL2\n",
        "<ADIF_VER:5>3.1.0\n",
        "<PROGRAMID:11>SOTA_CW_HL2\n",
        "<EOH>\n\n",
    ]
    with open(log_file, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 5:
                date, time_str, call, mode, sent = parts[0], parts[1], parts[2], parts[3], parts[4]
                rcvd = parts[5] if len(parts) > 5 else parts[4]
                qso_date = date.replace("-", "")
                qso_time = time_str.replace(":", "")
                adif_record = (
                    f"<QSO_DATE:8>{qso_date} "
                    f"<TIME_ON:4>{qso_time} "
                    f"<CALL:{len(call)}>{call} "
                    f"<MODE:{len(mode)}>{mode} "
                    f"<RST_SENT:{len(sent)}>{sent} "
                    f"<RST_RCVD:{len(rcvd)}>{rcvd} "
                    "<EOR>\n"
                )
                adif_records.append(adif_record)

    return Response(
        content="".join(adif_records),
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=sota_log.adi"}
    )


@app.get("/log/count")
def get_log_count():
    log_file = "sota_log.csv"
    if not os.path.exists(log_file):
        return {"count": 0, "file_exists": False}
    with open(log_file, "r") as f:
        count = sum(1 for line in f if line.strip())
    return {"count": count, "file_exists": True}


# -----------------------------------------------------------------------------
# WebSockets: Real-Time Telemetry & Audio Streaming for Tablet
# -----------------------------------------------------------------------------
@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """Pushes real-time radio state, SWR, decodes, and modem activity to tablet."""
    if not await _ws_accept(websocket):
        return
    try:
        while True:
            band_info = hl2.get_band_info()
            swr_meas = n2adr_board.last_measurement
            telemetry = {
                "type": "telemetry",
                "timestamp": time.time(),
                "frequency_hz": hl2.frequency_hz,
                "mode": hl2.mode,
                "band": band_info.name,
                "transmitting": hl2.is_transmitting or hl2.telemetry.ptt_in,
                "swr_tripped": hl2.swr_tripped,
                "swr_trip_reason": hl2.swr_trip_reason,
                "swr": swr_meas.vswr if swr_meas else 1.0,
                "fwd_power_w": swr_meas.fwd_power_w if swr_meas else 0.0,
                "cw": {
                    "running": cw_decoder.running,
                    "recent_text": cw_decoder.get_text()[-5:],
                    "status": await asyncio.to_thread(cw_manager.get_status),
                },
                "wsjtx": wsjtx_client.get_status_dict(),
                "fldigi": {
                    "connected": fldigi_client.is_connected,
                    "modem": fldigi_client.current_modem,
                    "transmitting": fldigi_client.is_transmitting,
                    "recent_text": fldigi_client.get_rx_text()[-100:],
                },
            }
            await websocket.send_json(telemetry)
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"Telemetry WS error: {e}")


@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket):
    """Streams live demodulated PCM audio to the tablet browser."""
    if not await _ws_accept(websocket):
        return
    q: asyncio.Queue = asyncio.Queue(maxsize=30)
    audio_streamer.register_subscriber(q)
    try:
        while True:
            pcm_chunk = await q.get()
            await websocket.send_bytes(pcm_chunk)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"Audio WS error: {e}")
    finally:
        audio_streamer.unregister_subscriber(q)


# -----------------------------------------------------------------------------
# Static WebUI Mount
# -----------------------------------------------------------------------------
webui_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../webui/static"))
if os.path.exists(webui_dir):
    app.mount("/webui", StaticFiles(directory=webui_dir, html=True), name="webui")


# -----------------------------------------------------------------------------
# Server Lifecycle Events
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Hermes Lite 2 SOTA & Digital Modes Backend...")
    try:
        # HL2-Watchdog bleibt aktiv: fällt der Pi aus, stoppt der HL2 den Stream
        hl2.start(disable_watchdog=False)
    except Exception as e:
        logger.warning(f"HL2 start warning: {e}")

    rx_audio.start()
    tx_audio.start()

    if settings.io_board_enabled:
        try:
            present, api = await asyncio.to_thread(io_board.probe_keyer)
            if present:
                logger.info(f"Pico-CW-Keyer gefunden (API {api})")
            else:
                logger.warning("IO-Board antwortet, aber ohne CW-Keyer-Firmware (Magic fehlt)")
        except Exception as e:
            logger.warning(f"IO-Board/Pico nicht erreichbar: {e}")

    if settings.cat_server_enabled:
        try:
            await cat_server.start()
        except Exception as e:
            logger.warning(f"Hamlib CAT server startup failed: {e}")

    if settings.wsjtx_enabled:
        wsjtx_client.start()

    if settings.fldigi_enabled:
        fldigi_client.start()

    cw_decoder.start()
    qso_bot.start()
    logger.info("Hermes Lite 2 Backend fully initialized.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Hermes Lite 2 Backend...")
    if settings.cat_server_enabled:
        await cat_server.stop()
    wsjtx_client.stop()
    fldigi_client.stop()
    cw_decoder.stop()
    qso_bot.stop()
    rx_audio.stop()
    tx_audio.stop()
    try:
        hl2.stop()
    except Exception:
        pass
    logger.info("Hermes Lite 2 Backend shut down cleanly.")
