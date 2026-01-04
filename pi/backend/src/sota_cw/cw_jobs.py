from __future__ import annotations

from dataclasses import dataclass

from .ioboard import IOBoard

CW_CMD_IDLE = 0
CW_CMD_START = 1
CW_CMD_ABORT = 2

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


def _pack_two_chars(a: int, b: int) -> int:
    return ((a & 0xFF) << 8) | (b & 0xFF)


def submit_job(io: IOBoard, job: CWJob) -> None:
    base = io.reg_base

    text = job.text.strip("\n\r")
    if len(text) > 120:
        text = text[:120]

    # Params
    io.write_reg(base + 2, int(job.wpm))
    io.write_reg(base + 3, int(job.ptt_lead_ms))
    io.write_reg(base + 4, int(job.ptt_tail_ms))
    io.write_reg(base + 5, len(text))

    # New TX quality params (see firmware register map)
    io.write_reg(base + 8, int(job.farnsworth_wpm))
    io.write_reg(base + 9, int(job.weight_pct))

    # Text buffer: 2 ASCII bytes per 16-bit register
    buf_base = base + 10
    for i in range(0, len(text), 2):
        c0 = ord(text[i])
        c1 = ord(text[i + 1]) if (i + 1) < len(text) else 0
        io.write_reg(buf_base + (i // 2), _pack_two_chars(c0, c1))

    # Start
    io.write_reg(base + 0, CW_CMD_START)


def abort_job(io: IOBoard) -> None:
    io.write_reg(io.reg_base + 0, CW_CMD_ABORT)
