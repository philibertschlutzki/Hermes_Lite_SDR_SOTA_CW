from __future__ import annotations

import logging
from typing import Optional

from .hl2_client import HL2Client
from .hardware.n2adr_filter import N2ADRFilterBoard, SWRMeasurement, BandInfo
from .hardware.hl2_io_board import HL2IOBoard

logger = logging.getLogger(__name__)


class HL2Control:
    """HL2 Control (Frequenz, Filter, IO-Board, Power & Envelope).

    Integriert:
    - Metis/openHPSDR Command & Control (C&C)
    - Automatische N2ADR Filter-Relais Steuerung (Reg 0x08)
    - Automatische IO-Board Frequenzaktualisierung (I2C)
    - SWR-Messung & Schutzabschaltung
    - Tune-Carrier Steuerung für Antennentuner
    """

    def __init__(
        self,
        ip: str,
        port: int,
        *,
        client: HL2Client | None = None,
        local_port: int = 1025,
        n2adr: N2ADRFilterBoard | None = None,
        io_board: HL2IOBoard | None = None,
    ):
        self.ip = ip
        self.port = port
        self.client = client or HL2Client(ip, port, local_port=local_port)
        self.n2adr = n2adr or N2ADRFilterBoard()
        self.io_board = io_board

        self._mode = "CWU"
        self._frequency_hz = 7030000  # Default 40m QRP CW
        self._tx_power_w = 5.0
        self._is_transmitting = False
        self._tune_active = False

    @property
    def frequency_hz(self) -> int:
        return self._frequency_hz

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def is_transmitting(self) -> bool:
        return self._is_transmitting

    def start(self, *, disable_watchdog: bool = True) -> None:
        self.client.metis_start(disable_watchdog=disable_watchdog)
        # Initialize filters on startup
        self.set_frequency_hz(self._frequency_hz)

    def stop(self, *, disable_watchdog: bool = True) -> None:
        self.client.metis_stop(disable_watchdog=disable_watchdog)

    def set_frequency_hz(self, hz: int) -> None:
        """
        Set TX and RX1 NCO frequencies, update N2ADR filter relays and notify IO board.
        """
        self._frequency_hz = int(hz)

        # 1. Set HL2 TX and RX1 NCOs (ADDR 0x01 and 0x02)
        self.client.cc_write(addr=0x01, data=self._frequency_hz & 0xFFFFFFFF)
        self.client.cc_write(addr=0x02, data=self._frequency_hz & 0xFFFFFFFF)

        # 2. Update N2ADR Filter Board LPF & HPF relays via OpenHPSDR C&C Reg 0x08
        if self.n2adr is not None:
            relay_word = self.n2adr.calculate_relay_word(self._frequency_hz)
            self.client.cc_write(addr=0x08, data=relay_word & 0xFF)
            logger.debug(f"N2ADR relays set to 0x{relay_word:02x} for {self._frequency_hz} Hz")

        # 3. Notify IO Board (RP2040) about frequency change for band outputs / ATU
        if self.io_board is not None:
            try:
                self.io_board.set_tx_frequency(self._frequency_hz)
            except Exception as e:
                logger.warning(f"Failed to update IO board frequency: {e}")

    def set_mode(self, mode: str) -> None:
        """Set radio mode (CWU, CWL, USB, LSB, AM, SAM, DIGU)."""
        self._mode = mode.upper()
        logger.info(f"HL2 Mode set to: {self._mode}")

    def set_cw_envelope(self, *, rise_us: int, fall_us: int, max_amp_q15: int) -> None:
        """Gateware interface (Hermes-Lite2_DSP PR#1) for raised-cosine envelope shaping."""
        d0 = ((int(fall_us) & 0xFFFF) << 16) | (int(rise_us) & 0xFFFF)
        self.client.cc_write(addr=0x18, data=d0)
        self.client.cc_write(addr=0x19, data=int(max_amp_q15) & 0xFFFF)

    def set_ptt(self, ptt: bool) -> None:
        """Engage or disengage PTT via Metis MOX bit."""
        self._is_transmitting = bool(ptt)
        # Send C&C frame with MOX bit set
        self.client.cc_write(addr=0x00, data=0, mox=self._is_transmitting)

    def set_tune_carrier(self, enable: bool, power_w: float = 2.0) -> None:
        """
        Output a continuous unmodulated carrier at specified power for antenna tuning.
        """
        self._tune_active = enable
        if enable:
            logger.info(f"Enabling tune carrier ({power_w} W)...")
            self.set_ptt(True)
        else:
            logger.info("Disabling tune carrier.")
            self.set_ptt(False)

    def measure_swr(self, ain1_raw: int = 0, ain2_raw: int = 0) -> SWRMeasurement:
        """Compute SWR and forward/reflected power."""
        return self.n2adr.compute_swr_and_power(ain1_raw, ain2_raw)

    def get_band_info(self) -> BandInfo:
        """Get current active HF band info."""
        return self.n2adr.get_band_for_frequency(self._frequency_hz)
