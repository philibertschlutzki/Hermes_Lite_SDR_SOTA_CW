"""Zugriff auf das HL2-IO-Board (Pico/RP2040) über den I2C2-Bus des HL2.

Weg: Pi --Ethernet/Protocol 1--> HL2 --C&C 0x3D (I2C2)--> Pico (I2C-Adresse 0x1D)

- Register sind 8 bit breit und 0..255 adressiert.
- Ein Write überträgt genau ein Datenbyte.
- Ein Read liefert 4 Bytes ab der angefragten Registernummer (der Pico
  zählt die Registernummer pro gelesenem Byte hoch).

Die CW-Registermap (ab 200) ist in `firmware/pico_cw_keyer/src/ioboard_regs.h`
definiert und hier gespiegelt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

IO_BOARD_I2C_ADDR = 0x1D
CW_REG_BASE = 200

# --- CW-Keyer-Registermap (Offsets ab CW_REG_BASE), siehe ioboard_regs.h ---
REG_OFF_CMD = 0
REG_OFF_STATUS = 1
REG_OFF_WPM = 2
REG_OFF_PTT_LEAD_MS = 3
REG_OFF_PTT_TAIL_MS = 4
REG_OFF_FARNSWORTH_WPM = 5
REG_OFF_WEIGHT_PCT = 6
REG_OFF_ERROR = 7
REG_OFF_PROGRESS = 8
REG_OFF_FIFO_LEVEL = 9
REG_OFF_FIFO_DATA = 10
REG_OFF_HEARTBEAT = 11
REG_OFF_WATCHDOG_S = 12
REG_OFF_KEY_DIRECT = 13
REG_OFF_API_VERSION = 14
REG_OFF_MAGIC = 15

CW_CMD_IDLE = 0
CW_CMD_START = 1
CW_CMD_ABORT = 2
CW_CMD_CLEAR = 3

CW_STATUS_IDLE = 0
CW_STATUS_RUNNING = 1
CW_STATUS_DONE = 2
CW_STATUS_ABORTED = 3
CW_STATUS_ERROR = 4
CW_STATUS_TUNE = 5

CW_ERR_NONE = 0
CW_ERR_FIFO_OVERFLOW = 1
CW_ERR_HOST_WATCHDOG = 2
CW_ERR_TUNE_TIMEOUT = 3

CW_FIFO_SIZE = 255
KEYER_MAGIC = 0xC5
KEYER_API_VERSION = 1


class I2CTransport(Protocol):
    def i2c_write(self, *, i2c_addr: int, reg: int, data: int, bus: int = 2, confirm: bool = True) -> None: ...

    def i2c_read(self, *, i2c_addr: int, reg: int, bus: int = 2) -> bytes: ...


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
    fifo_level: int = 0
    farnsworth_wpm: int = 0
    weight_pct: int = 50


class IOBoard:
    """8-bit-Registerzugriff auf das IO-Board über HL2-I2C2."""

    def __init__(self, hl2: I2CTransport, reg_base: int = CW_REG_BASE, *, i2c_addr: int = IO_BOARD_I2C_ADDR,
                 bus: int = 2):
        if not 0 <= reg_base <= 255 - 15:
            raise ValueError("reg_base must leave room for 16 registers below 256")
        self.hl2 = hl2
        self.reg_base = reg_base
        self.i2c_addr = i2c_addr
        self.bus = bus
        self.last_text_len = 0

    def write_reg(self, reg: int, value: int) -> None:
        reg = int(reg)
        value = int(value)
        if not 0 <= reg <= 255:
            raise ValueError(f"IO-Board-Register {reg} außerhalb 0..255")
        if not 0 <= value <= 255:
            raise ValueError(f"IO-Board-Wert {value} außerhalb 0..255 (Register {reg})")
        self.hl2.i2c_write(i2c_addr=self.i2c_addr, reg=reg, data=value, bus=self.bus)

    def read_regs(self, reg: int) -> bytes:
        """4 aufeinanderfolgende Register ab `reg` lesen."""
        if not 0 <= int(reg) <= 255:
            raise ValueError(f"IO-Board-Register {reg} außerhalb 0..255")
        return bytes(self.hl2.i2c_read(i2c_addr=self.i2c_addr, reg=int(reg), bus=self.bus))

    def read_reg(self, reg: int) -> int:
        return self.read_regs(reg)[0]

    # --- CW-Keyer ---

    def cw_reg(self, offset: int) -> int:
        return self.reg_base + offset

    def read_cw_status(self) -> CWStatus:
        b0 = self.read_regs(self.cw_reg(0))   # cmd, status, wpm, lead
        b1 = self.read_regs(self.cw_reg(4))   # tail, farnsworth, weight, error
        b2 = self.read_regs(self.cw_reg(8))   # progress, fifo level, (fifo data), heartbeat
        return CWStatus(
            cmd=b0[0], status=b0[1], wpm=b0[2], ptt_lead_ms=b0[3],
            ptt_tail_ms=b1[0], farnsworth_wpm=b1[1], weight_pct=b1[2], error_code=b1[3],
            progress=b2[0], fifo_level=b2[1], text_len=self.last_text_len,
        )

    def probe_keyer(self) -> tuple[bool, int]:
        """(Keyer-Firmware vorhanden, API-Version) über MAGIC/API-Register."""
        b = self.read_regs(self.cw_reg(12))  # watchdog, key_direct, api, magic
        return b[3] == KEYER_MAGIC, b[2]
