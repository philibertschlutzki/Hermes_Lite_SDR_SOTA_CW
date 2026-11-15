"""
HL2 IO Board (N2ADR, Raspberry Pi Pico) – Standardregister.

Zugriff über den I2C2-Bus des HL2 (C&C 0x3D, I2C-Adresse 0x1D), siehe
`sota_cw.ioboard`. Registernummern nach `i2c_registers.h` aus
https://github.com/jimahlstrom/HL2IOBoard:

- 0..4   REG_TX_FREQ_BYTE4..BYTE0: TX-Frequenz in Hz, Register 0 = höchstes
         Byte. Der Write auf Register 4 (BYTE0) übernimmt die Frequenz.
- 5      REG_CONTROL (Write 1 = alle Register zurücksetzen)
- 6      REG_INPUT_PINS (Bit0 EXTTR, 1 = RX; Bit1..5 In1..In5)
- 7      REG_ANTENNA_TUNER
- 8      REG_FAULT
- 9/10   REG_FIRMWARE_MAJOR / REG_FIRMWARE_MINOR
- 11     REG_RF_INPUTS
- 12     REG_FAN_SPEED (0..255)
- 200+   CW-Keyer dieses Projekts (siehe `ioboard.py`)
"""
from __future__ import annotations

import enum
import logging
from dataclasses import dataclass

from ..ioboard import CW_REG_BASE, IOBoard, I2CTransport

logger = logging.getLogger(__name__)


class ATUState(enum.Enum):
    IDLE = 0
    START_TUNE = 1
    BYPASS = 2
    TUNE_REQUEST = 0xEE  # Tuner fordert Träger an
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
    firmware_minor: int = 0
    reachable: bool = False
    keyer_present: bool = False
    keyer_api: int = 0
    exttr_tx: bool = False


class HL2IOBoard(IOBoard):
    """IO-Board mit Standardfunktionen und CW-Keyer-Block."""

    I2C_ADDR = 0x1D

    REG_FREQ_B4 = 0
    REG_FREQ_B3 = 1
    REG_FREQ_B2 = 2
    REG_FREQ_B1 = 3
    REG_FREQ_B0 = 4  # LSB, löst Übernahme aus
    REG_CONTROL = 5
    REG_INPUTS = 6
    REG_ATU = 7
    REG_FAULT = 8
    REG_FW_MAJOR = 9
    REG_FW_MINOR = 10
    REG_RF_INPUTS = 11
    REG_FAN_SPEED = 12

    # Rückwärtskompatibler Name
    REG_FW_VER = REG_FW_MAJOR

    def __init__(self, client: I2CTransport, cw_reg_base: int = CW_REG_BASE):
        super().__init__(client, reg_base=cw_reg_base, i2c_addr=self.I2C_ADDR)
        self.client = client
        self.cw_reg_base = cw_reg_base
        self.last_freq_hz: int = 0
        self.atu_in_progress: bool = False

    # --- Standardfunktionen ---

    def set_tx_frequency(self, freq_hz: int) -> None:
        """5-Byte-Frequenz schreiben; Register 4 (LSB) zuletzt als Übernahme."""
        freq_hz = int(freq_hz)
        self.last_freq_hz = freq_hz
        for reg, shift in ((self.REG_FREQ_B4, 32), (self.REG_FREQ_B3, 24), (self.REG_FREQ_B2, 16),
                           (self.REG_FREQ_B1, 8), (self.REG_FREQ_B0, 0)):
            self.write_reg(reg, (freq_hz >> shift) & 0xFF)
        logger.debug("IO-Board TX-Frequenz: %d Hz", freq_hz)

    def set_fan_speed(self, speed: int) -> None:
        """Lüfter 0..255 (Firmware: PWM = Wert * 4)."""
        self.write_reg(self.REG_FAN_SPEED, max(0, min(255, int(speed))))

    def read_inputs(self) -> int:
        try:
            return self.read_reg(self.REG_INPUTS)
        except Exception:
            return 0

    def start_atu_tune(self) -> None:
        logger.info("ATU: Tune anfordern")
        self.write_reg(self.REG_ATU, 1)
        self.atu_in_progress = True

    def bypass_atu(self) -> None:
        logger.info("ATU: Bypass")
        self.write_reg(self.REG_ATU, 2)
        self.atu_in_progress = False

    def get_atu_status(self) -> int:
        try:
            val = self.read_reg(self.REG_ATU)
            if val == 0:
                self.atu_in_progress = False
            return val
        except Exception:
            return 0

    def get_status(self) -> IOBoardStatus:
        """Schnappschuss mit drei 4-Byte-Reads (5..8, 9..12, Keyer-Info)."""
        try:
            a = self.read_regs(self.REG_CONTROL)   # control, inputs, atu, fault
            b = self.read_regs(self.REG_FW_MAJOR)  # fw major, fw minor, rf inputs, fan
        except Exception:
            return IOBoardStatus(freq_hz=self.last_freq_hz, control=0, inputs=0, atu_status=0, fault=0,
                                 firmware_version=0, reachable=False)
        keyer_present, keyer_api = False, 0
        try:
            keyer_present, keyer_api = self.probe_keyer()
        except Exception:
            pass
        return IOBoardStatus(
            freq_hz=self.last_freq_hz,
            control=a[0],
            inputs=a[1],
            atu_status=a[2],
            fault=a[3],
            firmware_version=b[0],
            firmware_minor=b[1],
            reachable=True,
            keyer_present=keyer_present,
            keyer_api=keyer_api,
            exttr_tx=not bool(a[1] & 0x01),
        )
