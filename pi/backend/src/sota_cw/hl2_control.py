from __future__ import annotations

from .hl2_client import HL2Client


class HL2Control:
    """HL2 Control (Frequenz/Envelope).

    Diese Implementierung nutzt den Metis/openHPSDR kompatiblen Command&Control Kern
    (siehe `HL2Client`) und stellt die für dieses Repo benötigten Operationen bereit.

    Ein "Mode" (CW/USB/LSB) ist auf HL2-Seite primär Host/DSP-Konvention und wird
    hier nur als Host-State gespeichert.
    """

    def __init__(self, ip: str, port: int, *, client: HL2Client | None = None, local_port: int = 1025):
        self.ip = ip
        self.port = port
        self.client = client or HL2Client(ip, port, local_port=local_port)
        self._mode = "CWU"

    def start(self, *, disable_watchdog: bool = True) -> None:
        self.client.metis_start(disable_watchdog=disable_watchdog)

    def stop(self, *, disable_watchdog: bool = True) -> None:
        self.client.metis_stop(disable_watchdog=disable_watchdog)

    def set_frequency_hz(self, hz: int) -> None:
        # Set TX and RX1 NCOs (ADDR 0x01 and 0x02).
        self.client.cc_write(addr=0x01, data=int(hz) & 0xFFFFFFFF)
        self.client.cc_write(addr=0x02, data=int(hz) & 0xFFFFFFFF)

    def set_mode(self, mode: str) -> None:
        self._mode = mode

    def set_cw_envelope(self, *, rise_us: int, fall_us: int, max_amp_q15: int) -> None:
        # Gateware interface (Hermes-Lite2_DSP PR#1):
        # 0x18: [15:0]=rise_us, [31:16]=fall_us
        # 0x19: [15:0]=max_amp_q15
        d0 = ((int(fall_us) & 0xFFFF) << 16) | (int(rise_us) & 0xFFFF)
        self.client.cc_write(addr=0x18, data=d0)
        self.client.cc_write(addr=0x19, data=int(max_amp_q15) & 0xFFFF)
