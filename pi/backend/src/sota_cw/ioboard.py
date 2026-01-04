from __future__ import annotations

from dataclasses import dataclass

from .hl2_client import HL2Client


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

    Dieses Projekt nutzt ein Registermodell (16-bit) im Adressbereich ab `reg_base`.

    Implementiert via HL2 Command&Control "Extended Address":
    - ADDR 0x3f + EADDR (Register-Adresse)

    Damit sind Registeradressen > 255 möglich (Textbuffer + Envelope-Regs).
    """

    def __init__(self, hl2: HL2Client, reg_base: int = 200):
        self.hl2 = hl2
        self.reg_base = reg_base

    def read_reg(self, addr: int) -> int:
        return int(self.hl2.ext_read_u16(eaddr=int(addr)))

    def write_reg(self, addr: int, value: int) -> None:
        self.hl2.ext_write_u16(eaddr=int(addr), value=int(value))

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
