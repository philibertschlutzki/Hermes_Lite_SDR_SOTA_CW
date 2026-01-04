from __future__ import annotations

import socket
import struct
import time
from dataclasses import dataclass

# Metis/HL2 protocol markers
METIS_PORT_DEFAULT = 1024

METIS_DISCOVERY = b"\xef\xfe\x02" + b"\x00" * 61
METIS_START = b"\xef\xfe\x04"  # + <command byte> + 60x00
METIS_STOP = b"\xef\xfe\x04"   # + <command byte> + 60x00


@dataclass(frozen=True)
class HL2Response:
    addr: int
    data: int
    ptt: int


class HL2Client:
    """Minimaler HL2 UDP Client (Metis/openHPSDR kompatibler Kern).

    Fokus:
    - Senden von Command&Control Writes (C0..C4)
    - Optionales RQST/ACK Roundtrip für Reads (ACK==1)
    - Extended Address (EADDR) für "extended write" an ADDR 0x3f

    Dieser Client ist absichtlich klein gehalten, um externe Abhängigkeiten
    zu vermeiden und die Integration auf dem Raspberry Pi zu vereinfachen.
    """

    def __init__(
        self,
        hl2_ip: str,
        hl2_port: int = METIS_PORT_DEFAULT,
        *,
        interface_ip: str = "0.0.0.0",
        local_port: int = 1025,
        timeout_s: float = 0.5,
    ):
        self.hl2_ip = hl2_ip
        self.hl2_port = hl2_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((interface_ip, local_port))
        self.sock.settimeout(timeout_s)

        self._seq = 0

    # --- Metis control ---

    def metis_start(self, *, wideband: bool = False, disable_watchdog: bool = True) -> None:
        cmd = 0
        cmd |= 0x01  # start radio
        if wideband:
            cmd |= 0x02
        if disable_watchdog:
            cmd |= 0x80
        pkt = METIS_START + bytes([cmd]) + b"\x00" * 60
        self.sock.sendto(pkt, (self.hl2_ip, self.hl2_port))

    def metis_stop(self, *, wideband: bool = False, disable_watchdog: bool = True) -> None:
        cmd = 0
        if wideband:
            cmd |= 0x02
        if disable_watchdog:
            cmd |= 0x80
        pkt = METIS_STOP + bytes([cmd]) + b"\x00" * 60
        self.sock.sendto(pkt, (self.hl2_ip, self.hl2_port))

    # --- Command & Control framing ---

    def _build_cc_frame(self, *, addr: int, data: int, mox: bool, rqst: bool, eaddr: int = 0) -> bytes:
        # C0: [7]=RQST, [6:1]=ADDR[5:0], [0]=MOX
        c0 = ((1 if rqst else 0) << 7) | ((addr & 0x3F) << 1) | (1 if mox else 0)

        payload = bytearray(1024)
        payload[0] = c0
        payload[1:5] = struct.pack(">I", data & 0xFFFFFFFF)

        # HL2: Extended address word directly after DATA word.
        # Word format: [31:24] reserved, [15:0] EADDR
        payload[5:9] = struct.pack(">I", eaddr & 0xFFFF)

        header = b"\xef\xfe\x01" + bytes([0x02]) + struct.pack(">I", self._seq & 0xFFFFFFFF)
        self._seq = (self._seq + 1) & 0xFFFFFFFF

        return header + payload

    def _recv_ack(self, *, expect_addr: int, timeout_s: float = 0.6) -> HL2Response:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                pkt, _ = self.sock.recvfrom(2048)
            except socket.timeout:
                continue

            if not pkt.startswith(b"\xef\xfe\x01") or len(pkt) < 8 + 5:
                continue

            payload = pkt[8:]
            c0 = payload[0]

            # ACK==1 response
            if (c0 & 0x80) == 0:
                continue

            raddr = (c0 >> 1) & 0x3F
            ptt = c0 & 0x01
            rdata = struct.unpack(">I", payload[1:5])[0]

            if raddr != (expect_addr & 0x3F):
                continue

            return HL2Response(addr=raddr, data=rdata, ptt=ptt)

        raise TimeoutError(f"HL2 ACK timeout for ADDR=0x{expect_addr:02x}")

    def cc_write(self, *, addr: int, data: int, mox: bool = False, rqst: bool = False, eaddr: int = 0) -> HL2Response | None:
        frame = self._build_cc_frame(addr=addr, data=data, mox=mox, rqst=rqst, eaddr=eaddr)
        self.sock.sendto(frame, (self.hl2_ip, self.hl2_port))
        if rqst:
            return self._recv_ack(expect_addr=addr)
        return None

    # --- Convenience: Extended registers via ADDR 0x3f + EADDR ---

    def ext_write_u16(self, *, eaddr: int, value: int) -> None:
        self.cc_write(addr=0x3F, data=value & 0xFFFF, rqst=False, eaddr=eaddr)

    def ext_read_u16(self, *, eaddr: int) -> int:
        resp = self.cc_write(addr=0x3F, data=0, rqst=True, eaddr=eaddr)
        if resp is None:
            raise RuntimeError("Missing response")
        return resp.data & 0xFFFF
