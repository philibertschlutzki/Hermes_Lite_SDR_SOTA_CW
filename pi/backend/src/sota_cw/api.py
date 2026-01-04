from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import logging

from .cw_jobs import CWJobManager
from .cw_rx import CWDecoder
from .hl2_client import HL2Client
from .hl2_control import HL2Control
from .ioboard import IOBoard
from .config import settings
from .qso_bot import QSOBot, BotConfig
from .logging_config import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="SOTA CW HL2 Backend", version="0.1.0")

# Initialize HL2 client + abstractions
hl2_client = HL2Client(settings.hl2_ip, settings.hl2_port, local_port=settings.hl2_local_port)
hl2 = HL2Control(settings.hl2_ip, settings.hl2_port, client=hl2_client, local_port=settings.hl2_local_port)
io_board = IOBoard(hl2_client, settings.io_reg_base)

# CW manager defaults are configurable via settings
cw_manager = CWJobManager(
    io_board,
    hl2=hl2,
    default_env_rise_us=settings.cw_env_rise_us,
    default_env_fall_us=settings.cw_env_fall_us,
    default_env_shape=settings.cw_env_shape,
    default_env_max_amp_q15=settings.cw_env_max_amp_q15,
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
    env_rise_us: int = Field(default=3000, ge=0, le=20000)
    env_fall_us: int = Field(default=3000, ge=0, le=20000)
    env_shape: int = Field(default=0, ge=0, le=10)
    env_max_amp_q15: int = Field(default=32767, ge=0, le=32767)


class BotConfigRequest(BaseModel):
    my_call: str
    my_ref: str
    wpm: int


@app.get("/health")
def health():
    """Basic health check endpoint."""
    return {"status": "ok", "hl2_ip": settings.hl2_ip}


@app.get("/healthz")
def healthz():
    """Kubernetes-style health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/diag")
def diagnostics():
    """Diagnostics endpoint with system status."""
    cw_status = cw_manager.get_status()
    bot_state = {
        "state": qso_bot.state.name,
        "running": qso_bot.running,
        "partner": qso_bot.current_partner_call,
    }
    
    return {
        "status": "ok",
        "config": {
            "hl2_ip": settings.hl2_ip,
            "hl2_port": settings.hl2_port,
            "io_reg_base": settings.io_reg_base,
            "use_internal_streamer": settings.use_internal_streamer,
        },
        "cw_status": cw_status,
        "decoder": {
            "running": cw_decoder.running,
            "buffer_size": len(cw_decoder.get_text()),
        },
        "bot": bot_state,
    }


@app.get("/diag/tx_test_plan")
def tx_test_plan():
    """
    TX Quality Test Plan parameters and checklist.
    
    Returns current system configuration relevant for TX quality testing
    with NanoVNA-H4 as described in docs/tx_quality_nanovna_h4.md
    """
    cw_status = cw_manager.get_status()
    
    # Get current frequency from HL2 (would need to track this state)
    # For now, return placeholder - in real implementation, track last set frequency
    current_freq_hz = 7100000  # Placeholder
    current_band_m = 40  # Derived from freq
    
    return {
        "test_plan_version": "1.0",
        "test_plan_doc": "docs/tx_quality_nanovna_h4.md",
        "current_configuration": {
            "tx_mode": "CW_CARRIER",  # or CW_KEYED based on actual state
            "band_m": current_band_m,
            "tx_freq_hz": current_freq_hz,
            "tx_power_setting_w": 5.0,  # HL2 typical max
            "cw_wpm": cw_status.get("wpm", 20),
            "cw_farnsworth_wpm": 0,  # From status if available
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
            "safety_margin_db": 13.0,  # +37 dBm - 50 dB = -13 dBm (safe for VNA)
        },
        "test_checklist": [
            {
                "step": 1,
                "name": "Attenuator Characterization",
                "description": "Measure S21 of attenuator chain across HF",
                "required": True,
                "status": "pending",
            },
            {
                "step": 2,
                "name": "S11 Measurement (Matching)",
                "description": "Measure HL2 output impedance and VSWR",
                "required": True,
                "status": "pending",
            },
            {
                "step": 3,
                "name": "TX Frequency Verification",
                "description": "Verify HL2 transmits on correct frequency",
                "required": True,
                "status": "pending",
            },
            {
                "step": 4,
                "name": "Filter Performance (if applicable)",
                "description": "Measure external filter S21 in-band and out-of-band",
                "required": False,
                "status": "pending",
            },
        ],
        "csv_template": "docs/test_reports/tx_quality/templates/tx_quality_run_template.csv",
        "validation_tool": "docs/test_reports/tools/validate_tx_quality_csv.py",
    }



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


# --- Log Export Routes ---

@app.get("/log/export/csv")
def export_log_csv():
    """
    Export QSO log in SOTA CSV format.
    
    Returns CSV file with columns: date, time, callsign, mode, sent, rcvd
    """
    import csv
    from io import StringIO
    from fastapi.responses import StreamingResponse
    import os
    
    log_file = "sota_log.csv"
    
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="No log file found. Complete QSOs first.")
    
    # Read log file and return as streaming response
    def generate():
        with open(log_file, 'r') as f:
            # Add header if not present
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
    """
    Export QSO log in ADIF format.
    
    Returns ADIF file compatible with common logging programs.
    """
    import os
    from fastapi.responses import Response
    
    log_file = "sota_log.csv"
    
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="No log file found. Complete QSOs first.")
    
    # Convert CSV to ADIF
    adif_records = []
    adif_records.append("ADIF Export from SOTA CW HL2\n")
    adif_records.append("<ADIF_VER:5>3.1.0\n")
    adif_records.append("<PROGRAMID:11>SOTA_CW_HL2\n")
    adif_records.append("<EOH>\n\n")
    
    with open(log_file, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 5:
                date, time, call, mode, sent, rcvd = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5] if len(parts) > 5 else parts[4]
                
                # Convert date format YYYY-MM-DD to YYYYMMDD
                qso_date = date.replace('-', '')
                # Time is HH:MM, convert to HHMM
                qso_time = time.replace(':', '')
                
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
    
    adif_content = "".join(adif_records)
    
    return Response(
        content=adif_content,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=sota_log.adi"}
    )


@app.get("/log/count")
def get_log_count():
    """Get the number of QSOs in the log."""
    import os
    
    log_file = "sota_log.csv"
    
    if not os.path.exists(log_file):
        return {"count": 0, "file_exists": False}
    
    with open(log_file, 'r') as f:
        count = sum(1 for line in f if line.strip())
    
    return {"count": count, "file_exists": True}


# Lifecycle
@app.on_event("startup")
def startup_event():
    logger.info("Starting SOTA CW HL2 Backend")
    logger.info(f"HL2 IP: {settings.hl2_ip}:{settings.hl2_port}")
    logger.info(f"Internal Streamer: {settings.use_internal_streamer}")
    
    # Ensure HL2 is running (watchdog disabled for headless operation).
    hl2.start(disable_watchdog=True)

    # Program default envelope once at startup.
    hl2.set_cw_envelope(
        rise_us=settings.cw_env_rise_us,
        fall_us=settings.cw_env_fall_us,
        max_amp_q15=settings.cw_env_max_amp_q15,
    )

    cw_decoder.start()
    qso_bot.start()
    logger.info("SOTA CW HL2 Backend started successfully")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down SOTA CW HL2 Backend")
    cw_decoder.stop()
    qso_bot.stop()
    logger.info("SOTA CW HL2 Backend shut down successfully")
