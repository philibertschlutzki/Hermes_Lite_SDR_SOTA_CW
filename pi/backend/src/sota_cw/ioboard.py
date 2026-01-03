from __future__ import annotations

from dataclasses import dataclass

@dataclass
class CWStatus:
    cmd: int
    status: int
    wpm: int
    ptt_lead_ms: int
    ptt_tail_ms: int
    text_len: int
    progress: int
    error_code: int

class IOBoard:
    """Register-I/O Abstraktion.

    Erwartet read_reg/write_reg (16-bit). In der Praxis wird das über die HL2
    IO-Board Read/Write Funktionen einer HL2-Library realisiert.
    """

    def __init__(self, reg_base: int = 200):
        self.reg_base = reg_base

    def read_reg(self, addr: int) -> int:
        raise NotImplementedError("IOBoard read_reg not wired yet. See third_party/README.md")

    def write_reg(self, addr: int, value: int) -> None:
        raise NotImplementedError("IOBoard write_reg not wired yet. See third_party/README.md")

    def read_cw_status(self) -> CWStatus:
        base = self.reg_base
        return CWStatus(
            cmd=self.read_reg(base + 0),
            status=self.read_reg(base + 1),
            wpm=self.read_reg(base + 2),
            ptt_lead_ms=self.read_reg(base + 3),
            ptt_tail_ms=self.read_reg(base + 4),
            text_len=self.read_reg(base + 5),
            progress=self.read_reg(base + 6),
            error_code=self.read_reg(base + 7),
        )
