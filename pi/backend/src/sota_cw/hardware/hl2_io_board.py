"""
HL2 IO Board integration (Jim Ahlstrom RP2040 Pico design).

Communicates via HL2 internal I2C bus (address 0x1D) bridged via HL2 Extended Registers (0x3F).

Standard register map:
- Registers 0x00..0x04: TX frequency in Hz (5 bytes Big-Endian). Writing reg 4 triggers band update.
- Register 0x05: Control / Fan
- Register 0x06: Input status pins (EXTTR, In1..In5, PTT in)
- Register 0x07: Antenna Tuner (ATU) interface (e.g. Icom AH-4 / Elecraft T1)
- Register 0x08: Fault code
- Register 0x09: Firmware version
- Extended Base (200+): SOTA CW Hardware Keyer register block (Pico Keyer firmware)
"""
from __future__ import annotations

import enum
import logging
import time
from dataclasses import dataclass
from typing import Optional

from ..hl2_client import HL2Client

logger = logging.getLogger(__name__)


class ATUState(enum.Enum):
    IDLE = 0
    START_TUNE = 1
    BYPASS = 2
    TUNE_REQUEST = 0xEE  # Tuner asks radio to send RF tune carrier (~2W)
    SUCCESS = 0x00
    FAULT = 0xF0


@dataclass
class IOBoardStatus:
    freq_hz: int
    control: int
    inputs: int
    atu_status: int
    fault: int
    firmware_version: int


class HL2IOBoard:
    """Interface to the HL2 IO Board (Raspberry Pi Pico RP2040)."""

    I2C_ADDR = 0x1D

    # Standard Register Addresses
    REG_FREQ_B4 = 0x00
    REG_FREQ_B3 = 0x01
    REG_FREQ_B2 = 0x02
    REG_FREQ_B1 = 0x03
    REG_FREQ_B0 = 0x04  # LSB and update trigger
    REG_CONTROL = 0x05
    REG_INPUTS = 0x06
    REG_ATU = 0x07
    REG_FAULT = 0x08
    REG_FW_VER = 0x09

    def __init__(self, client: HL2Client, cw_reg_base: int = 200):
        self.client = client
        self.cw_reg_base = cw_reg_base
        self.last_freq_hz: int = 0
        self.atu_in_progress: bool = False

    def write_reg(self, reg_addr: int, value: int) -> None:
        """Write 16-bit word to IO Board register via HL2 Extended Address (0x3F)."""
        self.client.ext_write_u16(eaddr=int(reg_addr), value=int(value))

    def read_reg(self, reg_addr: int) -> int:
        """Read 16-bit word from IO Board register via HL2 Extended Address (0x3F)."""
        return int(self.client.ext_read_u16(eaddr=int(reg_addr)))

    # --- Standard IO Board Functions ---

    def set_tx_frequency(self, freq_hz: int) -> None:
        """
        Send 5-byte frequency to IO Board.
        Writing byte 0 (LSB) triggers internal band recalculation on the Pico.
        """
        self.last_freq_hz = int(freq_hz)
        b4 = (freq_hz >> 32) & 0xFF
        b3 = (freq_hz >> 24) & 0xFF
        b2 = (freq_hz >> 16) & 0xFF
        b1 = (freq_hz >> 8) & 0xFF
        b0 = freq_hz & 0xFF

        # Write high bytes
        self.write_reg(self.REG_FREQ_B4, b4)
        self.write_reg(self.REG_FREQ_B3, b3)
        self.write_reg(self.REG_FREQ_B2, b2)
        self.write_reg(self.REG_FREQ_B1, b1)
        # Write trigger byte
        self.write_reg(self.REG_FREQ_B0, b0)
        logger.debug(f"IO Board frequency updated: {freq_hz} Hz")

    def set_fan_speed(self, speed_level: int) -> None:
        """Set fan speed (0=off, 1=low, 2=med, 3=high)."""
        self.write_reg(self.REG_CONTROL, int(speed_level) & 0x0F)

    def read_inputs(self) -> int:
        """Read input pins (EXTTR, In1..In5)."""
        try:
            return self.read_reg(self.REG_INPUTS)
        except Exception:
            return 0

    def start_atu_tune(self) -> None:
        """Command the external Antenna Tuner to start auto-tuning cycle."""
        logger.info("Starting ATU tuning cycle...")
        self.write_reg(self.REG_ATU, 1)  # 1 = Start Tune
        self.atu_in_progress = True

    def bypass_atu(self) -> None:
        """Command the Antenna Tuner to enter bypass mode."""
        logger.info("Bypassing ATU...")
        self.write_reg(self.REG_ATU, 2)  # 2 = Bypass
        self.atu_in_progress = False

    def get_atu_status(self) -> int:
        """
        Check ATU status register.
        0x00: Tuning complete / Idle
        0xEE: Tuner requests RF tune carrier
        >= 0xF0: Fault or error
        """
        try:
            val = self.read_reg(self.REG_ATU) & 0xFF
            if val == 0:
                self.atu_in_progress = False
            return val
        except Exception:
            return 0

    def get_status(self) -> IOBoardStatus:
        """Read snapshot of IO board state."""
        try:
            ctrl = self.read_reg(self.REG_CONTROL)
            inputs = self.read_reg(self.REG_INPUTS)
            atu = self.read_reg(self.REG_ATU)
            fault = self.read_reg(self.REG_FAULT)
            fw = self.read_reg(self.REG_FW_VER)
        except Exception:
            ctrl, inputs, atu, fault, fw = 0, 0, 0, 0, 1

        return IOBoardStatus(
            freq_hz=self.last_freq_hz,
            control=ctrl,
            inputs=inputs,
            atu_status=atu,
            fault=fault,
            firmware_version=fw,
        )
