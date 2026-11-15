"""HL2 Protocol-1-Host: ein Socket für Steuerung, IQ-Empfang und TX.

Protocol 1 kennt genau einen Host-Stream. Dieser Client besitzt daher den
einzigen UDP-Socket zum HL2 und erledigt alles darüber:

- EP2-Pakete (Host -> HL2) mit je zwei C&C-Frames (7F 7F 7F + C0..C4) und
  126 TX-Samples. Pro empfangenem EP6-Paket wird ein EP2-Paket gesendet
  (gleiche Rate bei 48 kHz). Ohne RX-Daten sendet ein Keepalive-Timer.
- C&C-Planung: Einmal-Befehle (z. B. I2C) haben Vorrang; sonst werden die
  dauerhaften Register (0x00, 0x01, 0x02, 0x09, ...) reihum wiederholt, damit
  der HL2 immer den vollständigen Zustand kennt.
- RQST/ACK: höchstens eine offene Anfrage, wie im HL2-Wiki verlangt.
- EP6-Pakete werden zerlegt: Telemetrie (Vorwärts-/Rückwärtsleistung,
  PTT/Key) und 24-bit-IQ von RX1 gehen an registrierte Callbacks.
- I2C2 (Adresse 0x3D) zum IO-Board: 8-bit-Register, ein Datenbyte.
"""
from __future__ import annotations

import collections
import logging
import socket
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from . import hl2_protocol as p

logger = logging.getLogger(__name__)

METIS_PORT_DEFAULT = p.HL2_PORT


@dataclass(frozen=True)
class HL2Response:
    addr: int
    data: int
    ptt: int


class _PendingRequest:
    def __init__(self, cc: p.CCWrite):
        self.cc = cc
        self.event = threading.Event()
        self.response: Optional[HL2Response] = None
        self.sent_at = 0.0


IQCallback = Callable[[np.ndarray], None]
TelemetryCallback = Callable[[p.Telemetry], None]
TxSource = Callable[[int], Optional[np.ndarray]]


class HL2Client:
    """Protocol-1-Host für den Hermes-Lite 2."""

    PERSISTENT_ORDER = (
        p.ADDR_GENERAL,
        p.ADDR_TX_NCO,
        p.ADDR_RX1_NCO,
        p.ADDR_TX_DRIVE,
        p.ADDR_CW_HANG,
        p.ADDR_PTT_HANG,
    )

    def __init__(
        self,
        hl2_ip: str,
        hl2_port: int = METIS_PORT_DEFAULT,
        *,
        interface_ip: str = "0.0.0.0",
        local_port: int = 0,
        timeout_s: float = 0.05,
        keepalive_s: float = 0.02,
        sock: Optional[socket.socket] = None,
    ):
        self.hl2_ip = hl2_ip
        self.hl2_port = hl2_port
        self._interface = (interface_ip, local_port)
        self._timeout_s = timeout_s
        self._keepalive_s = keepalive_s
        self.sock = sock

        self._lock = threading.RLock()
        self._seq = 0
        self._mox = False
        self._regs: dict[int, int] = {
            p.ADDR_GENERAL: p.general_word(),
            p.ADDR_TX_NCO: 7_030_000,
            p.ADDR_RX1_NCO: 7_030_000,
            p.ADDR_TX_DRIVE: p.tx_drive_word(drive_level=0, pa_enable=True),
            p.ADDR_CW_HANG: p.cw_hang_word(250),
            p.ADDR_PTT_HANG: p.ptt_hang_word(),
        }
        self._rr_index = 0
        self._urgent: collections.deque[int] = collections.deque()  # Register, die sofort raus sollen
        self._oneshot: collections.deque[p.CCWrite] = collections.deque()
        self._req_queue: collections.deque[_PendingRequest] = collections.deque()
        self._req_inflight: Optional[_PendingRequest] = None
        self._last_was_rqst = False

        self.telemetry = p.Telemetry()
        self._iq_callbacks: list[IQCallback] = []
        self._telemetry_callbacks: list[TelemetryCallback] = []
        self._tx_source: Optional[TxSource] = None

        self._running = False
        self._rx_thread: Optional[threading.Thread] = None
        self._ka_thread: Optional[threading.Thread] = None
        self._last_tx = 0.0
        self.last_rx_time = 0.0
        self.packets_rx = 0
        self.packets_tx = 0
        self.seq_errors = 0
        self._last_rx_seq: Optional[int] = None

    # ------------------------------------------------------------------ setup

    def _ensure_socket(self) -> socket.socket:
        if self.sock is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(self._interface)
            s.settimeout(self._timeout_s)
            self.sock = s
        return self.sock

    def _send(self, pkt: bytes) -> None:
        sock = self._ensure_socket()
        try:
            sock.sendto(pkt, (self.hl2_ip, self.hl2_port))
        except OSError as e:  # Netz weg: nicht crashen, Watchdog des HL2 greift
            logger.debug("HL2 send failed: %s", e)

    @staticmethod
    def discover(timeout_s: float = 2.0, interface_ip: str = "0.0.0.0") -> list[tuple[str, bytes]]:
        """Discovery-Broadcast; liefert (IP, Antwort) aller HL2 im Netz."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind((interface_ip, 0))
        s.settimeout(0.2)
        found: list[tuple[str, bytes]] = []
        try:
            s.sendto(p.DISCOVERY_REQUEST, ("255.255.255.255", p.HL2_PORT))
            deadline = time.monotonic() + timeout_s
            while time.monotonic() < deadline:
                try:
                    data, addr = s.recvfrom(2048)
                except socket.timeout:
                    continue
                if data[:2] == b"\xef\xfe" and data[2] in (0x02, 0x03):
                    found.append((addr[0], data))
        finally:
            s.close()
        return found

    # -------------------------------------------------------------- callbacks

    def add_iq_callback(self, cb: IQCallback) -> None:
        self._iq_callbacks.append(cb)

    def add_telemetry_callback(self, cb: TelemetryCallback) -> None:
        self._telemetry_callbacks.append(cb)

    def set_tx_source(self, src: Optional[TxSource]) -> None:
        """Quelle für TX-IQ (n Samples complex, |x|<=1) bei MOX; None = Stille."""
        self._tx_source = src

    # -------------------------------------------------------------- lifecycle

    def start(self, *, disable_watchdog: bool = False) -> None:
        if self._running:
            return
        self._ensure_socket()
        self._running = True
        self._rx_thread = threading.Thread(target=self._rx_loop, name="hl2-rx", daemon=True)
        self._ka_thread = threading.Thread(target=self._keepalive_loop, name="hl2-ka", daemon=True)
        self._rx_thread.start()
        self._ka_thread.start()
        # Erst Zustand senden, dann Stream starten
        for _ in range(len(self.PERSISTENT_ORDER)):
            self._send_ep2()
        self._send(p.metis_start_packet(iq=True, disable_watchdog=disable_watchdog))

    def stop(self, *, disable_watchdog: bool = False) -> None:
        with self._lock:
            self._mox = False
        if self.sock is not None:
            self._send_ep2()  # MOX=0 sicher übertragen
            self._send(p.metis_stop_packet(disable_watchdog=disable_watchdog))
        self._running = False
        for t in (self._rx_thread, self._ka_thread):
            if t is not None and t.is_alive() and t is not threading.current_thread():
                t.join(timeout=1.0)

    # Rückwärtskompatible Namen
    def metis_start(self, *, wideband: bool = False, disable_watchdog: bool = False) -> None:
        self.start(disable_watchdog=disable_watchdog)

    def metis_stop(self, *, wideband: bool = False, disable_watchdog: bool = False) -> None:
        self.stop(disable_watchdog=disable_watchdog)

    @property
    def running(self) -> bool:
        return self._running

    # ------------------------------------------------------------ C&C-Zustand

    def set_register(self, addr: int, data: int) -> None:
        """Dauerhaftes Register setzen; wird sofort und danach zyklisch gesendet."""
        with self._lock:
            self._regs[addr & 0x3F] = data & 0xFFFFFFFF
            if addr not in self._urgent:
                self._urgent.append(addr & 0x3F)

    def get_register(self, addr: int) -> int:
        with self._lock:
            return self._regs.get(addr & 0x3F, 0)

    def set_mox(self, mox: bool) -> None:
        with self._lock:
            self._mox = bool(mox)
        if self._running:
            self._send_ep2()

    @property
    def mox(self) -> bool:
        return self._mox

    def cc_write(self, *, addr: int, data: int, mox: bool | None = None, rqst: bool = False, eaddr: int = 0,
                 timeout_s: float = 0.5) -> HL2Response | None:
        """Einmaliger C&C-Write. Mit rqst=True wird auf das ACK gewartet."""
        if mox is not None:
            self.set_mox(mox)
        cc = p.CCWrite(addr=addr & 0x3F, data=data & 0xFFFFFFFF, rqst=rqst)
        if not rqst:
            with self._lock:
                self._oneshot.append(cc)
            if self._running:
                self._send_ep2()
            return None
        return self._request(cc, timeout_s=timeout_s)

    def _request(self, cc: p.CCWrite, *, timeout_s: float, retries: int = 2) -> HL2Response:
        if not self._running:
            raise ConnectionError("HL2-Stream läuft nicht (start() nicht aufgerufen)")
        last_err: Exception | None = None
        for _attempt in range(retries + 1):
            req = _PendingRequest(cc)
            with self._lock:
                self._req_queue.append(req)
            if self._running:
                self._send_ep2()
            if req.event.wait(timeout_s) and req.response is not None:
                if req.response.addr == p.ADDR_ERROR and cc.addr != p.ADDR_ERROR:
                    last_err = RuntimeError(f"HL2 meldet Fehler (RADDR 0x3F) für ADDR 0x{cc.addr:02x}")
                    time.sleep(0.005)
                    continue
                return req.response
            with self._lock:
                if self._req_inflight is req:
                    self._req_inflight = None
                try:
                    self._req_queue.remove(req)
                except ValueError:
                    pass
            last_err = TimeoutError(f"HL2 ACK timeout for ADDR=0x{cc.addr:02x}")
        assert last_err is not None
        raise last_err

    # ------------------------------------------------------------------- I2C

    def i2c_write(self, *, i2c_addr: int, reg: int, data: int, bus: int = 2, confirm: bool = True,
                  timeout_s: float = 0.3) -> None:
        addr = p.ADDR_I2C2 if bus == 2 else p.ADDR_I2C1
        word = p.i2c_word(write=True, i2c_addr=i2c_addr, reg=reg, data=data)
        if confirm:
            self._request(p.CCWrite(addr=addr, data=word, rqst=True), timeout_s=timeout_s)
        else:
            self.cc_write(addr=addr, data=word)

    def i2c_read(self, *, i2c_addr: int, reg: int, bus: int = 2, timeout_s: float = 0.3) -> bytes:
        """Liest 4 Bytes ab `reg` (Gerät inkrementiert die Registernummer selbst)."""
        addr = p.ADDR_I2C2 if bus == 2 else p.ADDR_I2C1
        word = p.i2c_word(write=False, i2c_addr=i2c_addr, reg=reg)
        resp = self._request(p.CCWrite(addr=addr, data=word, rqst=True), timeout_s=timeout_s)
        return resp.data.to_bytes(4, "big")

    # ------------------------------------------------------------- Scheduler

    def _next_cc(self) -> p.CCWrite:
        """Nächsten C&C-Eintrag wählen (Aufruf unter self._lock)."""
        # RQST höchstens jedes zweite Frame und nur einer gleichzeitig
        if not self._last_was_rqst and self._req_inflight is None and self._req_queue:
            req = self._req_queue.popleft()
            req.sent_at = time.monotonic()
            self._req_inflight = req
            self._last_was_rqst = True
            return req.cc
        self._last_was_rqst = False
        if self._urgent:
            addr = self._urgent.popleft()
            return p.CCWrite(addr=addr, data=self._regs[addr])
        if self._oneshot:
            return self._oneshot.popleft()
        addr = self.PERSISTENT_ORDER[self._rr_index % len(self.PERSISTENT_ORDER)]
        self._rr_index += 1
        return p.CCWrite(addr=addr, data=self._regs.get(addr, 0))

    def build_next_packet(self) -> bytes:
        with self._lock:
            # Hängende Anfrage nach 250 ms freigeben (Paketverlust)
            inflight = self._req_inflight
            if inflight is not None and time.monotonic() - inflight.sent_at > 0.25:
                self._req_inflight = None
            cc1 = self._next_cc()
            cc2 = self._next_cc()
            mox = self._mox
            seq = self._seq
            self._seq = (self._seq + 1) & 0xFFFFFFFF
        iq = None
        if mox and self._tx_source is not None:
            try:
                iq = self._tx_source(p.SAMPLES_PER_PACKET_TX)
            except Exception as e:  # TX-Quelle darf den Stream nie stoppen
                logger.warning("TX source failed: %s", e)
        return p.build_ep2_packet(seq, cc1, cc2, mox=mox, sample_bytes=p.tx_samples_to_bytes(iq))

    def _send_ep2(self) -> None:
        self._send(self.build_next_packet())
        self._last_tx = time.monotonic()
        self.packets_tx += 1

    # ----------------------------------------------------------------- Loops

    def _keepalive_loop(self) -> None:
        while self._running:
            time.sleep(self._keepalive_s / 2)
            if time.monotonic() - self._last_tx >= self._keepalive_s:
                self._send_ep2()

    def _rx_loop(self) -> None:
        sock = self._ensure_socket()
        while self._running:
            try:
                pkt, _ = sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                if self._running:
                    time.sleep(0.05)
                continue
            self.handle_packet(pkt)

    def handle_packet(self, pkt: bytes) -> None:
        """Ein empfangenes Paket verarbeiten (auch direkt aus Tests nutzbar)."""
        ep6 = p.parse_ep6_packet(pkt)
        if ep6 is None:
            return
        self.packets_rx += 1
        self.last_rx_time = time.monotonic()
        if self._last_rx_seq is not None and ep6.seq != ((self._last_rx_seq + 1) & 0xFFFFFFFF):
            self.seq_errors += 1
        self._last_rx_seq = ep6.seq

        for info in ep6.frames:
            self.telemetry.update(info)
            if info.ack:
                self._handle_ack(info)
        for tcb in self._telemetry_callbacks:
            try:
                tcb(self.telemetry)
            except Exception as e:
                logger.warning("telemetry callback failed: %s", e)
        for cb in self._iq_callbacks:
            try:
                cb(ep6.iq)
            except Exception as e:
                logger.warning("IQ callback failed: %s", e)
        # TX-Takt an RX koppeln: ein EP2 pro EP6
        if self._running:
            self._send_ep2()

    def _handle_ack(self, info: p.RxFrameInfo) -> None:
        with self._lock:
            req = self._req_inflight
            if req is None:
                return
            if info.raddr == req.cc.addr or info.raddr == p.ADDR_ERROR:
                req.response = HL2Response(addr=info.raddr, data=info.data, ptt=int(info.ptt))
                self._req_inflight = None
                req.event.set()
