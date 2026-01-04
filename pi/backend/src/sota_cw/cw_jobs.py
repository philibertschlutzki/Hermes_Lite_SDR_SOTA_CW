from __future__ import annotations

from dataclasses import dataclass

from .ioboard import IOBoard

CW_CMD_IDLE = 0
CW_CMD_START = 1
CW_CMD_ABORT = 2

# Register offsets (relative to IO_REG_BASE / CW_REG_BASE)
REG_OFF_CMD = 0
REG_OFF_STATUS = 1
REG_OFF_WPM = 2
REG_OFF_PTT_LEAD_MS = 3
REG_OFF_PTT_TAIL_MS = 4
REG_OFF_TEXT_LEN = 5
REG_OFF_PROGRESS = 6
REG_OFF_ERROR = 7
REG_OFF_FARNSWORTH_WPM = 8
REG_OFF_WEIGHT_PCT = 9
REG_OFF_TEXT_BUF = 10

# Envelope shaping registers are placed AFTER the text buffer.
# With TEXT_MAX_CHARS=120 => TEXT_MAX_REGS=60 => text regs: 10..69, first free is 70.
REG_OFF_ENV_RISE_US = 70   # abs: base + 70 => 270
REG_OFF_ENV_FALL_US = 71   # abs: base + 71 => 271
REG_OFF_ENV_SHAPE = 72     # abs: base + 72 => 272
REG_OFF_ENV_MAX_AMP_Q15 = 73  # abs: base + 73 => 273


@dataclass
class CWJob:
    text: str
    wpm: int = 20
    ptt_lead_ms: int = 80
    ptt_tail_ms: int = 120

    # TX quality / timing refinements
    # Farnsworth spacing: if set (< wpm), increases inter-character/word gaps while keeping element speed.
    farnsworth_wpm: int = 0
    # Weighting: 50 = nominal; firmware clamps to a conservative range.
    weight_pct: int = 50

    # Envelope shaping (HL2-side amplitude control)
    env_rise_us: int = 3000
    env_fall_us: int = 3000
    env_shape: int = 0
    env_max_amp_q15: int = 32767


def _pack_two_chars(a: int, b: int) -> int:
    return ((a & 0xFF) << 8) | (b & 0xFF)


def submit_job(io: IOBoard, job: CWJob) -> None:
    base = io.reg_base

    text = job.text.strip("\n\r")
    if len(text) > 120:
        text = text[:120]

    # Params
    io.write_reg(base + REG_OFF_WPM, int(job.wpm))
    io.write_reg(base + REG_OFF_PTT_LEAD_MS, int(job.ptt_lead_ms))
    io.write_reg(base + REG_OFF_PTT_TAIL_MS, int(job.ptt_tail_ms))
    io.write_reg(base + REG_OFF_TEXT_LEN, len(text))

    # TX quality params (firmware-side)
    io.write_reg(base + REG_OFF_FARNSWORTH_WPM, int(job.farnsworth_wpm))
    io.write_reg(base + REG_OFF_WEIGHT_PCT, int(job.weight_pct))

    # Envelope shaping params (HL2-side)
    io.write_reg(base + REG_OFF_ENV_RISE_US, int(job.env_rise_us))
    io.write_reg(base + REG_OFF_ENV_FALL_US, int(job.env_fall_us))
    io.write_reg(base + REG_OFF_ENV_SHAPE, int(job.env_shape))
    io.write_reg(base + REG_OFF_ENV_MAX_AMP_Q15, int(job.env_max_amp_q15))

    # Text buffer: 2 ASCII bytes per 16-bit register
    buf_base = base + REG_OFF_TEXT_BUF
    for i in range(0, len(text), 2):
        c0 = ord(text[i])
        c1 = ord(text[i + 1]) if (i + 1) < len(text) else 0
        io.write_reg(buf_base + (i // 2), _pack_two_chars(c0, c1))

    # Start (edge-trigger)
    io.write_reg(base + REG_OFF_CMD, CW_CMD_START)


def abort_job(io: IOBoard) -> None:
    io.write_reg(io.reg_base + REG_OFF_CMD, CW_CMD_ABORT)


class CWJobManager:
    def __init__(
        self,
        io: IOBoard,
        default_env_rise_us: int = 3000,
        default_env_fall_us: int = 3000,
        default_env_shape: int = 0,
        default_env_max_amp_q15: int = 32767,
    ):
        self.io = io
        self._job_seq = 0
        self.default_env_rise_us = default_env_rise_us
        self.default_env_fall_us = default_env_fall_us
        self.default_env_shape = default_env_shape
        self.default_env_max_amp_q15 = default_env_max_amp_q15

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
        submit_job(self.io, job)
        return self._job_seq

    def abort_job(self) -> None:
        abort_job(self.io)

    def get_status(self):
        st = self.io.read_cw_status()
        return {
            "cmd": st.cmd,
            "status": st.status,
            "wpm": st.wpm,
            "ptt_lead_ms": st.ptt_lead_ms,
            "ptt_tail_ms": st.ptt_tail_ms,
            "text_len": st.text_len,
            "progress": st.progress,
            "error_code": st.error_code,
        }
