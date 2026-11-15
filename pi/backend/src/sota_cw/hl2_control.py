from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from . import hl2_protocol as p
from .hardware.hl2_io_board import HL2IOBoard
from .hardware.n2adr_filter import BandInfo, N2ADRFilterBoard, SWRMeasurement
from .hl2_client import HL2Client

logger = logging.getLogger(__name__)

MODE_ALIASES = {"PKTUSB": "DIGU", "PKTLSB": "DIGL", "CW": "CWU", "CWR": "CWL"}
KNOWN_MODES = ("CWU", "CWL", "USB", "LSB", "DIGU", "DIGL", "AM", "SAM")


class HL2Control:
    """HL2-Steuerung: Frequenz, Filter, PTT, Drive, SWR-Schutz.

    Der vollständige Funkgerätezustand liegt in den dauerhaften C&C-Registern
    des `HL2Client` und wird zyklisch gesendet:

    - 0x00: Samplerate 48 kHz, OC-Bits = N2ADR-Relaiswort (DATA[23:17]),
      1 Empfänger, Duplex. PTT ändert nur das MOX-Bit in C0, nie dieses Wort.
    - 0x01/0x02: TX-/RX1-NCO
    - 0x09: Drive-Level und PA
    - 0x10: CW-Hang-Zeit (hält den T/R-Wechsel zwischen den Zeichen)

    SWR-Schutz: Aus jeder Telemetrie mit Vorwärts- und Rückwärtsleistung wird
    das SWR berechnet. Liegt es `trip_count` Messungen in Folge über dem
    Grenzwert, wird MOX abgeschaltet, Drive auf 0 gesetzt und die Callbacks
    (z. B. CW-Abbruch im Pico) aufgerufen. Die Sperre bleibt bis
    `reset_swr_trip()` bestehen.
    """

    def __init__(
        self,
        ip: str,
        port: int,
        *,
        client: HL2Client | None = None,
        local_port: int = 0,
        n2adr: N2ADRFilterBoard | None = None,
        io_board: HL2IOBoard | None = None,
        custom_gateware_envelope: bool = False,
        trip_count: int = 3,
        drive_level: int = 15,
        cw_hang_ms: int = 250,
    ):
        self.ip = ip
        self.port = port
        self.client = client or HL2Client(ip, port, local_port=local_port)
        self.n2adr = n2adr or N2ADRFilterBoard()
        self.io_board = io_board
        self.custom_gateware_envelope = custom_gateware_envelope
        self.trip_count = max(1, trip_count)

        self._mode = "CWU"
        self._frequency_hz = 7_030_000
        self._tx_power_w = 5.0
        self._drive_level = max(0, min(15, drive_level))
        self._is_transmitting = False
        self._tune_active = False
        self._oc_bits = 0
        self._swr_tripped = False
        self._swr_bad_count = 0
        self.swr_trip_reason: Optional[str] = None
        self._trip_callbacks: list[Callable[[str], None]] = []
        self._mode_callbacks: list[Callable[[str], None]] = []
        self._lock = threading.RLock()
        # IO-Board-Frequenz im Hintergrund nachführen (5 bestätigte I2C-Writes),
        # damit Frequenzwechsel über API/CAT nicht blockieren; nur der letzte Wert zählt.
        self._io_freq_pending: Optional[int] = None
        self._io_event = threading.Event()
        self._io_thread: Optional[threading.Thread] = None

        self.client.set_register(p.ADDR_CW_HANG, p.cw_hang_word(cw_hang_ms))
        self.client.add_telemetry_callback(self._on_telemetry)
        self._apply_frequency(push_io=False)
        self._push_drive()

    # ------------------------------------------------------------ Properties

    @property
    def frequency_hz(self) -> int:
        return self._frequency_hz

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def is_transmitting(self) -> bool:
        return self._is_transmitting

    @property
    def swr_tripped(self) -> bool:
        return self._swr_tripped

    @property
    def telemetry(self) -> p.Telemetry:
        return self.client.telemetry

    def add_trip_callback(self, cb: Callable[[str], None]) -> None:
        self._trip_callbacks.append(cb)

    def add_mode_callback(self, cb: Callable[[str], None]) -> None:
        self._mode_callbacks.append(cb)

    # ------------------------------------------------------------ Lifecycle

    def start(self, *, disable_watchdog: bool = False) -> None:
        self.client.start(disable_watchdog=disable_watchdog)
        self.set_frequency_hz(self._frequency_hz)

    def stop(self, *, disable_watchdog: bool = False) -> None:
        self.set_ptt(False)
        self.client.stop(disable_watchdog=disable_watchdog)

    # ------------------------------------------------------------ Register

    def _general_word(self) -> int:
        return p.general_word(sample_rate=48000, oc_bits=self._oc_bits, n_receivers=1, duplex=True)

    def _push_general(self) -> None:
        self.client.set_register(p.ADDR_GENERAL, self._general_word())

    def _push_drive(self) -> None:
        lvl = 0 if self._swr_tripped else self._drive_level
        self.client.set_register(p.ADDR_TX_DRIVE, p.tx_drive_word(drive_level=lvl, pa_enable=True))

    def _apply_frequency(self, *, push_io: bool = True) -> None:
        f = self._frequency_hz
        self.client.set_register(p.ADDR_TX_NCO, f)
        self.client.set_register(p.ADDR_RX1_NCO, f)
        if self.n2adr is not None:
            self._oc_bits = self.n2adr.calculate_relay_word(f) & 0x7F
        self._push_general()
        if push_io and self.io_board is not None:
            self._io_freq_pending = f
            if self._io_thread is None or not self._io_thread.is_alive():
                self._io_thread = threading.Thread(target=self._io_freq_loop, name="io-freq", daemon=True)
                self._io_thread.start()
            self._io_event.set()

    def _io_freq_loop(self) -> None:
        while True:
            self._io_event.wait()
            self._io_event.clear()
            f = self._io_freq_pending
            if f is None or self.io_board is None:
                continue
            try:
                self.io_board.set_tx_frequency(f)
            except Exception as e:
                logger.debug("IO-Board-Frequenz nicht gesetzt: %s", e)

    def set_frequency_hz(self, hz: int) -> None:
        """TX/RX1-NCO setzen, N2ADR-Relais (OC-Bits in 0x00) und IO-Board nachführen."""
        with self._lock:
            new = int(hz)
            if self._is_transmitting:
                band_now = self.get_band_info()
                band_new = self.n2adr.get_band_for_frequency(new)
                if band_now.lpf_relay_bit != band_new.lpf_relay_bit or not band_new.tx_allowed:
                    # Kein Filterwechsel unter HF-Last
                    self.set_ptt(False)
            self._frequency_hz = new
            self._apply_frequency()
            logger.debug("Frequenz %d Hz, OC-Bits 0x%02x", new, self._oc_bits)

    def set_mode(self, mode: str) -> None:
        m = MODE_ALIASES.get(mode.upper(), mode.upper())
        if m not in KNOWN_MODES:
            raise ValueError(f"Unbekannter Mode {mode}")
        self._mode = m
        for cb in self._mode_callbacks:
            try:
                cb(m)
            except Exception as e:
                logger.warning("mode callback failed: %s", e)
        logger.info("HL2 Mode: %s", self._mode)

    def set_drive_level(self, level: int) -> None:
        self._drive_level = max(0, min(15, int(level)))
        self._push_drive()

    def set_cw_envelope(self, *, rise_us: int, fall_us: int, max_amp_q15: int) -> None:
        """Nur mit eigener Gateware (Adressen 0x18/0x19). Die Standard-Gateware formt selbst (G10)."""
        if not self.custom_gateware_envelope:
            return
        d0 = ((int(fall_us) & 0xFFFF) << 16) | (int(rise_us) & 0xFFFF)
        self.client.cc_write(addr=0x18, data=d0)
        self.client.cc_write(addr=0x19, data=int(max_amp_q15) & 0xFFFF)

    # ------------------------------------------------------------ TX

    def tx_allowed(self) -> tuple[bool, str]:
        if self._swr_tripped:
            return False, f"SWR-Schutz ausgelöst: {self.swr_trip_reason}"
        band = self.get_band_info()
        if not band.tx_allowed:
            return False, f"TX auf {band.name} gesperrt (kein passender Tiefpass)"
        return True, ""

    def set_ptt(self, ptt: bool) -> None:
        """MOX-Bit setzen (für SSB/Digital-TX über EP2-IQ). Register 0x00 bleibt unverändert."""
        with self._lock:
            if ptt:
                ok, reason = self.tx_allowed()
                if not ok:
                    raise PermissionError(reason)
            self._is_transmitting = bool(ptt)
            self._swr_bad_count = 0
            self.client.set_mox(self._is_transmitting)

    def set_tune_carrier(self, enable: bool, power_w: float = 2.0) -> None:
        """Tune über den HL2 (Tune-Bit in 0x09 + MOX)."""
        with self._lock:
            if enable:
                ok, reason = self.tx_allowed()
                if not ok:
                    raise PermissionError(reason)
            self._tune_active = bool(enable)
            lvl = 0 if self._swr_tripped else max(1, min(15, int(round(power_w / max(self._tx_power_w, 0.1) * 15))))
            self.client.set_register(
                p.ADDR_TX_DRIVE,
                p.tx_drive_word(drive_level=lvl if enable else self._drive_level, pa_enable=True, tune=enable),
            )
            self.set_ptt(enable)
            if not enable:
                self._push_drive()

    # ------------------------------------------------------------ SWR-Schutz

    def measure_swr(self, ain1_raw: int | None = None, ain2_raw: int | None = None) -> SWRMeasurement:
        t = self.client.telemetry
        fwd = t.fwd_power_raw if ain1_raw is None else ain1_raw
        rev = t.rev_power_raw if ain2_raw is None else ain2_raw
        return self.n2adr.compute_swr_and_power(fwd, rev)

    def _on_telemetry(self, t: p.Telemetry) -> None:
        transmitting = self._is_transmitting or t.ptt_in
        if not transmitting:
            self._swr_bad_count = 0
            return
        meas = self.n2adr.compute_swr_and_power(t.fwd_power_raw, t.rev_power_raw)
        if meas.fwd_power_w <= 0.0:
            return
        if meas.is_safe:
            self._swr_bad_count = 0
            return
        self._swr_bad_count += 1
        if self._swr_bad_count >= self.trip_count and not self._swr_tripped:
            self.trip_swr(f"SWR {meas.vswr:.1f} > {self.n2adr.max_vswr_threshold:.1f}")

    def trip_swr(self, reason: str) -> None:
        with self._lock:
            self._swr_tripped = True
            self.swr_trip_reason = reason
            logger.error("SWR-Schutz: TX abgeschaltet (%s)", reason)
            self._is_transmitting = False
            self._tune_active = False
            self.client.set_mox(False)
            self._push_drive()
        for cb in self._trip_callbacks:
            try:
                cb(reason)
            except Exception as e:
                logger.error("SWR trip callback failed: %s", e)

    def reset_swr_trip(self) -> None:
        with self._lock:
            self._swr_tripped = False
            self.swr_trip_reason = None
            self._swr_bad_count = 0
            self._push_drive()

    def get_band_info(self) -> BandInfo:
        return self.n2adr.get_band_for_frequency(self._frequency_hz)

    def status(self) -> dict:
        t = self.client.telemetry
        return {
            "frequency_hz": self._frequency_hz,
            "mode": self._mode,
            "band": self.get_band_info().name,
            "transmitting": self._is_transmitting,
            "ptt_in": t.ptt_in,
            "key_in": t.key_in,
            "swr_tripped": self._swr_tripped,
            "swr_trip_reason": self.swr_trip_reason,
            "stream_running": self.client.running,
            "packets_rx": self.client.packets_rx,
            "seq_errors": self.client.seq_errors,
            "rx_age_s": round(time.monotonic() - self.client.last_rx_time, 2) if self.client.last_rx_time else None,
            "gateware_version": t.firmware_version,
        }
