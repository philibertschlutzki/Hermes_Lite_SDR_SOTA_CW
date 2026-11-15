"""CW-Sendeaufträge an den Keyer im Pico des HL2-IO-Boards.

Ablauf (nur über das Netzwerkkabel Pi <-> HL2):

    Pi --Protocol 1, C&C 0x3D--> HL2 --I2C2 0x1D--> Pico
    Pico --Low-Side-Schalter (J6)--> HL2 CN4 Tip (Key) / Ring (PTT)

Der Pico erzeugt das Morse-Timing selbst. Der HL2 formt die HF-Hüllkurve
(CN4-Tip getastet = CW mit eingebauter Flankenformung).

Ein Auftrag:
1. Parameter (WPM, PTT-Vorlauf/-Nachlauf, Farnsworth, Gewichtung) schreiben
2. CMD=CLEAR, dann Text Zeichen für Zeichen in das FIFO-Register
3. CMD=START
Während der Auftrag läuft, schreibt der Host alle 0,5 s das Heartbeat-
Register. Bleibt es länger als WATCHDOG_S aus (Pi abgestürzt, Netz weg),
lässt der Pico die Taste los und meldet Fehler 2.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

from .ioboard import (
    CW_CMD_ABORT,
    CW_CMD_CLEAR,
    CW_CMD_IDLE,
    CW_CMD_START,
    CW_FIFO_SIZE,
    CW_STATUS_RUNNING,
    CW_STATUS_TUNE,
    IOBoard,
    REG_OFF_CMD,
    REG_OFF_FARNSWORTH_WPM,
    REG_OFF_FIFO_DATA,
    REG_OFF_HEARTBEAT,
    REG_OFF_KEY_DIRECT,
    REG_OFF_PTT_LEAD_MS,
    REG_OFF_PTT_TAIL_MS,
    REG_OFF_WATCHDOG_S,
    REG_OFF_WEIGHT_PCT,
    REG_OFF_WPM,
)

logger = logging.getLogger(__name__)

__all__ = [
    "CW_CMD_IDLE", "CW_CMD_START", "CW_CMD_ABORT", "CW_CMD_CLEAR",
    "CWJob", "CWJobManager", "submit_job", "abort_job", "sanitize_text", "TEXT_MAX_CHARS",
]

TEXT_MAX_CHARS = CW_FIFO_SIZE

# Zeichen, die die Pico-Firmware kennt (cw_morse.c)
_ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/?=.,+-:'()\"@!& ")


def sanitize_text(text: str) -> str:
    """Großschreibung, unbekannte Zeichen entfernen, Leerraum zusammenfassen."""
    t = " ".join(text.upper().replace("\r", " ").replace("\n", " ").split())
    t = "".join(c for c in t if c in _ALLOWED)
    return t[:TEXT_MAX_CHARS]


def _u8(v: int, lo: int = 0, hi: int = 255) -> int:
    return max(lo, min(hi, int(v)))


@dataclass
class CWJob:
    text: str
    wpm: int = 20
    ptt_lead_ms: int = 80
    ptt_tail_ms: int = 120
    farnsworth_wpm: int = 0
    weight_pct: int = 50
    # Hüllkurve: nur mit eigener Gateware wirksam (C&C 0x18/0x19), sonst formt der HL2 selbst
    env_rise_us: int = 3000
    env_fall_us: int = 3000
    env_shape: int = 0
    env_max_amp_q15: int = 32767


def submit_job(io: IOBoard, job: CWJob, *, watchdog_s: int = 3) -> int:
    """Auftrag in den Pico schreiben und starten. Gibt die gesendete Textlänge zurück."""
    base = io.reg_base
    text = sanitize_text(job.text)

    io.write_reg(base + REG_OFF_CMD, CW_CMD_CLEAR)
    io.write_reg(base + REG_OFF_WPM, _u8(job.wpm, 5, 60))
    io.write_reg(base + REG_OFF_PTT_LEAD_MS, _u8(job.ptt_lead_ms))
    io.write_reg(base + REG_OFF_PTT_TAIL_MS, _u8(job.ptt_tail_ms))
    io.write_reg(base + REG_OFF_FARNSWORTH_WPM, _u8(job.farnsworth_wpm, 0, 60))
    io.write_reg(base + REG_OFF_WEIGHT_PCT, _u8(job.weight_pct, 25, 75))
    io.write_reg(base + REG_OFF_WATCHDOG_S, _u8(watchdog_s, 1, 30))

    for ch in text:
        io.write_reg(base + REG_OFF_FIFO_DATA, ord(ch))

    io.write_reg(base + REG_OFF_CMD, CW_CMD_START)
    io.last_text_len = len(text)
    return len(text)


def append_text(io: IOBoard, text: str) -> int:
    """Text an einen laufenden Auftrag anhängen (Type-ahead)."""
    t = sanitize_text(text)
    for ch in t:
        io.write_reg(io.reg_base + REG_OFF_FIFO_DATA, ord(ch))
    io.last_text_len += len(t)
    return len(t)


def abort_job(io: IOBoard) -> None:
    io.write_reg(io.reg_base + REG_OFF_CMD, CW_CMD_ABORT)


class TxNotAllowed(RuntimeError):
    pass


class CWJobManager:
    HEARTBEAT_INTERVAL_S = 0.5

    def __init__(
        self,
        io: IOBoard,
        *,
        hl2=None,
        default_env_rise_us: int = 3000,
        default_env_fall_us: int = 3000,
        default_env_shape: int = 0,
        default_env_max_amp_q15: int = 32767,
        watchdog_s: int = 3,
    ):
        self.io = io
        self.hl2 = hl2
        self._job_seq = 0
        self.default_env_rise_us = default_env_rise_us
        self.default_env_fall_us = default_env_fall_us
        self.default_env_shape = default_env_shape
        self.default_env_max_amp_q15 = default_env_max_amp_q15
        self.watchdog_s = watchdog_s
        self._busy_until = 0.0
        self._hb_stop = threading.Event()
        self._hb_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.last_error: Optional[str] = None

    # --- Senden ---

    def _check_tx_allowed(self) -> None:
        if self.hl2 is None:
            return
        allowed = getattr(self.hl2, "tx_allowed", None)
        if callable(allowed):
            res = allowed()
            if isinstance(res, tuple) and len(res) == 2 and res[0] is False:
                raise TxNotAllowed(res[1])

    def start_job(
        self,
        text: str,
        wpm: int = 20,
        *,
        ptt_lead_ms: int = 80,
        ptt_tail_ms: int = 120,
        farnsworth_wpm: int = 0,
        weight_pct: int = 50,
        env_rise_us: int | None = None,
        env_fall_us: int | None = None,
        env_shape: int | None = None,
        env_max_amp_q15: int | None = None,
    ) -> int:
        self._check_tx_allowed()
        self._job_seq += 1
        job = CWJob(
            text=text,
            wpm=wpm,
            ptt_lead_ms=ptt_lead_ms,
            ptt_tail_ms=ptt_tail_ms,
            farnsworth_wpm=farnsworth_wpm,
            weight_pct=weight_pct,
            env_rise_us=self.default_env_rise_us if env_rise_us is None else env_rise_us,
            env_fall_us=self.default_env_fall_us if env_fall_us is None else env_fall_us,
            env_shape=self.default_env_shape if env_shape is None else env_shape,
            env_max_amp_q15=self.default_env_max_amp_q15 if env_max_amp_q15 is None else env_max_amp_q15,
        )
        if self.hl2 is not None:
            # Wirkt nur mit eigener Gateware; HL2Control ignoriert es sonst (G10)
            self.hl2.set_cw_envelope(rise_us=job.env_rise_us, fall_us=job.env_fall_us,
                                     max_amp_q15=job.env_max_amp_q15)
        n = submit_job(self.io, job, watchdog_s=self.watchdog_s)
        self._busy_until = time.monotonic() + self.estimate_duration_s(n, job.wpm, job.farnsworth_wpm) \
            + (job.ptt_lead_ms + job.ptt_tail_ms) / 1000.0 + 0.5
        self._start_heartbeat()
        return self._job_seq

    def append(self, text: str) -> int:
        self._check_tx_allowed()
        n = append_text(self.io, text)
        self._busy_until = max(self._busy_until, time.monotonic()) + self.estimate_duration_s(n, 20, 0)
        self._start_heartbeat()
        return n

    @staticmethod
    def estimate_duration_s(n_chars: int, wpm: int, farnsworth_wpm: int = 0) -> float:
        """Grobe Dauer: PARIS = 50 Dit pro Wort, ~10 Dit pro Zeichen."""
        eff = farnsworth_wpm or wpm
        dit_s = 1.2 / max(5, min(60, eff))
        return n_chars * 10 * dit_s

    def abort_job(self) -> None:
        self._busy_until = 0.0
        try:
            abort_job(self.io)
        finally:
            self._stop_heartbeat()

    def tune(self, enable: bool, *, max_s: float = 10.0) -> None:
        """Dauerträger über den Pico (Key down). Der Pico begrenzt die Dauer selbst."""
        if enable:
            self._check_tx_allowed()
            self.io.write_reg(self.io.reg_base + REG_OFF_WATCHDOG_S, _u8(self.watchdog_s, 1, 30))
            self.io.write_reg(self.io.reg_base + REG_OFF_KEY_DIRECT, 1)
            self._busy_until = time.monotonic() + max_s
            self._start_heartbeat()
        else:
            self._busy_until = 0.0
            try:
                self.io.write_reg(self.io.reg_base + REG_OFF_KEY_DIRECT, 0)
            finally:
                self._stop_heartbeat()

    # --- Heartbeat ---

    def _start_heartbeat(self) -> None:
        with self._lock:
            if self._hb_thread is not None and self._hb_thread.is_alive():
                return
            self._hb_stop.clear()
            self._hb_thread = threading.Thread(target=self._heartbeat_loop, name="cw-heartbeat", daemon=True)
            self._hb_thread.start()

    def _stop_heartbeat(self) -> None:
        self._hb_stop.set()

    def _heartbeat_loop(self) -> None:
        counter = 0
        while not self._hb_stop.wait(self.HEARTBEAT_INTERVAL_S):
            counter = (counter + 1) & 0xFF
            try:
                self.io.write_reg(self.io.reg_base + REG_OFF_HEARTBEAT, counter)
                st = self.io.read_cw_status()
                if st.status not in (CW_STATUS_RUNNING, CW_STATUS_TUNE):
                    if st.error_code:
                        self.last_error = f"Keyer-Fehler {st.error_code}"
                    self._busy_until = 0.0
                    break
            except Exception as e:
                logger.debug("CW heartbeat failed: %s", e)
                if time.monotonic() > self._busy_until + 5.0:
                    break

    # --- Status ---

    def is_busy(self) -> bool:
        try:
            st = self.io.read_cw_status()
            return st.status in (CW_STATUS_RUNNING, CW_STATUS_TUNE)
        except Exception:
            return time.monotonic() < self._busy_until

    def get_status(self) -> dict:
        try:
            st = self.io.read_cw_status()
        except Exception as e:
            return {"reachable": False, "error": str(e), "busy": time.monotonic() < self._busy_until}
        return {
            "reachable": True,
            "cmd": st.cmd,
            "status": st.status,
            "wpm": st.wpm,
            "ptt_lead_ms": st.ptt_lead_ms,
            "ptt_tail_ms": st.ptt_tail_ms,
            "text_len": st.text_len,
            "progress": st.progress,
            "fifo_level": st.fifo_level,
            "error_code": st.error_code,
            "last_error": self.last_error,
        }
