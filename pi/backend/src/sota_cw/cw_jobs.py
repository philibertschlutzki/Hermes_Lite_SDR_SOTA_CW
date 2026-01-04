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

    # Text buffer: 2 ASCII bytes per 16-bit register
    buf_base = base + 8
    for i in range(0, len(text), 2):
        c0 = ord(text[i])
        c1 = ord(text[i + 1]) if (i + 1) < len(text) else 0
        io.write_reg(buf_base + (i // 2), _pack_two_chars(c0, c1))

    # Start
    io.write_reg(base + 0, CW_CMD_START)


def abort_job(io: IOBoard) -> None:
    io.write_reg(io.reg_base + 0, CW_CMD_ABORT)


class CWJobManager:
    """High-level TX job API used by FastAPI.

    The backend stays state-light: the IO board is the authority for execution/state.
    """

    def __init__(self, io: IOBoard):
        self.io = io
        self._job_seq = 0
        self._current_job_id: int | None = None

    def start_job(
        self,
        text: str,
        wpm: int = 20,
        ptt_lead_ms: int = 80,
        ptt_tail_ms: int = 120,
    ) -> int:
        self._job_seq += 1
        job_id = self._job_seq

        submit_job(
            self.io,
            CWJob(
                text=text,
                wpm=int(wpm),
                ptt_lead_ms=int(ptt_lead_ms),
                ptt_tail_ms=int(ptt_tail_ms),
            ),
        )

        self._current_job_id = job_id
        return job_id

    def abort_job(self) -> None:
        abort_job(self.io)

    def get_status(self) -> dict:
        # IO wiring might not be available in unit tests/dev without HL2 library.
        try:
            s = self.io.read_cw_status()
        except NotImplementedError:
            return {
                "wired": False,
                "job_id": self._current_job_id,
                "error": "IOBoard read_reg/write_reg not wired (see third_party/README.md)",
            }

        return {
            "wired": True,
            "job_id": self._current_job_id,
            "cmd": s.cmd,
            "status": s.status,
            "wpm": s.wpm,
            "ptt_lead_ms": s.ptt_lead_ms,
            "ptt_tail_ms": s.ptt_tail_ms,
            "text_len": s.text_len,
            "progress": s.progress,
            "error_code": s.error_code,
        }
