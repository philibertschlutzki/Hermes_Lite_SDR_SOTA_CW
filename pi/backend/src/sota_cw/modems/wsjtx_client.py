"""
WSJT-X UDP Protocol Client.

Implements bidirectional network communication with WSJT-X over UDP (port 2237).
Supports all WSJT-X modes: FT8, FT4, WSPR, JT9, JT65, FST4, FST4W.

Parses Qt QDataStream binary packets and exposes:
- Real-time status (TX/RX, Frequency, Mode, Current QSO partner)
- Decoded band activity stream (Callsign, SNR, Grid, Time, Message)
- Outgoing control (One-touch QSO Reply, Halt TX, Free Text)
"""
from __future__ import annotations

import collections
import io
import logging
import socket
import struct
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# WSJT-X Protocol Constants
WSJTX_MAGIC = 0xADBCCBDA
WSJTX_SCHEMA_VERSION = 2

# Message Types
MSG_HEARTBEAT = 0
MSG_STATUS = 1
MSG_DECODE = 2
MSG_CLEAR = 3
MSG_REPLY = 4
MSG_QSOLOGGED = 5
MSG_CLOSE = 6
MSG_REPLAY = 7
MSG_HALTTX = 8
MSG_FREETEXT = 9
MSG_WSPRDECODE = 10
MSG_LOCATIONCHANGE = 11
MSG_LOGGEDADIF = 12
MSG_HIGHLIGHTCALL = 13


@dataclass
class WSJTXDecode:
    time_str: str          # e.g. "14:30:15"
    snr_db: int            # e.g. -12
    delta_time_s: float    # e.g. 0.2
    delta_freq_hz: int     # Audio frequency e.g. 1250
    mode: str              # Mode marker: "~" for FT8, "+" for FT4, ":" for WSPR, "&" for FST4
    message: str           # e.g. "CQ HB9SOTA JN47"
    callsign: Optional[str] = None
    grid: Optional[str] = None
    raw_time_ms: int = 0
    is_cq: bool = False


@dataclass
class WSJTXStatus:
    dial_freq_hz: int = 0
    mode: str = "FT8"
    dx_call: str = ""
    report: str = ""
    tx_mode: str = ""
    tx_enabled: bool = False
    transmitting: bool = False
    decoding: bool = False
    rx_df: int = 0
    tx_df: int = 0
    de_call: str = ""
    de_grid: str = ""
    dx_grid: str = ""
    tx_watchdog: bool = False
    sub_mode: str = ""
    fast_mode: bool = False
    last_heard: float = 0.0


class QDataStreamParser:
    """Helper to parse Qt QDataStream binary serialized buffers."""

    def __init__(self, data: bytes):
        self.stream = io.BytesIO(data)

    def read_u32(self) -> int:
        raw = self.stream.read(4)
        if len(raw) < 4:
            raise EOFError()
        return struct.unpack(">I", raw)[0]

    def read_i32(self) -> int:
        raw = self.stream.read(4)
        if len(raw) < 4:
            raise EOFError()
        return struct.unpack(">i", raw)[0]

    def read_u64(self) -> int:
        raw = self.stream.read(8)
        if len(raw) < 8:
            raise EOFError()
        return struct.unpack(">Q", raw)[0]

    def read_bool(self) -> bool:
        raw = self.stream.read(1)
        if len(raw) < 1:
            raise EOFError()
        return struct.unpack(">?", raw)[0]

    def read_double(self) -> float:
        raw = self.stream.read(8)
        if len(raw) < 8:
            raise EOFError()
        return struct.unpack(">d", raw)[0]

    def read_string(self) -> str:
        length = self.read_u32()
        if length == 0xFFFFFFFF:
            return ""
        raw = self.stream.read(length)
        return raw.decode("utf-8", errors="replace")


class WSJTXClient:
    """UDP Server and Client for WSJT-X communication."""

    def __init__(self, host: str = "127.0.0.1", port: int = 2237, max_decodes: int = 150):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.running: bool = False
        self.thread: Optional[threading.Thread] = None

        self.status = WSJTXStatus()
        self.decodes: collections.deque[WSJTXDecode] = collections.deque(maxlen=max_decodes)
        self.wsjt_client_id: str = "WSJT-X"
        self.remote_addr: Optional[tuple[str, int]] = None
        self.on_decode_callback: Optional[Callable[[WSJTXDecode], None]] = None

    def start(self) -> None:
        """Start listening for WSJT-X UDP packets."""
        if self.running:
            return
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.bind((self.host, self.port))
            self.sock.settimeout(1.0)
            self.thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.thread.start()
            logger.info(f"WSJT-X client listening on UDP {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"Could not bind WSJT-X UDP socket on {self.host}:{self.port}: {e}")

    def stop(self) -> None:
        """Stop listening."""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        logger.info("WSJT-X client stopped.")

    def clear_decodes(self) -> None:
        self.decodes.clear()

    def get_decodes(self) -> list[WSJTXDecode]:
        return list(self.decodes)

    def get_status_dict(self) -> dict:
        is_connected = (time.time() - self.status.last_heard) < 15.0 if self.status.last_heard > 0 else False
        return {
            "connected": is_connected,
            "dial_freq_hz": self.status.dial_freq_hz,
            "mode": self.status.mode,
            "dx_call": self.status.dx_call,
            "report": self.status.report,
            "transmitting": self.status.transmitting,
            "tx_enabled": self.status.tx_enabled,
            "decoding": self.status.decoding,
            "de_call": self.status.de_call,
            "de_grid": self.status.de_grid,
            "rx_df": self.status.rx_df,
            "tx_df": self.status.tx_df,
            "decode_count": len(self.decodes),
        }

    # --- Outgoing Commands to WSJT-X ---

    def reply_to_decode(self, decode: WSJTXDecode) -> None:
        """Trigger WSJT-X to reply to a specific decode (One-touch QSO)."""
        if not self.remote_addr or not self.sock:
            logger.warning("No remote WSJT-X instance known yet to reply to.")
            return

        buf = bytearray()
        buf.extend(struct.pack(">I", WSJTX_MAGIC))
        buf.extend(struct.pack(">I", WSJTX_SCHEMA_VERSION))
        buf.extend(struct.pack(">I", MSG_REPLY))

        # Id string
        id_bytes = self.wsjt_client_id.encode("utf-8")
        buf.extend(struct.pack(">I", len(id_bytes)))
        buf.extend(id_bytes)

        # Time (ms)
        buf.extend(struct.pack(">I", decode.raw_time_ms))
        # SNR
        buf.extend(struct.pack(">i", decode.snr_db))
        # Delta time (double)
        buf.extend(struct.pack(">d", decode.delta_time_s))
        # Delta freq
        buf.extend(struct.pack(">I", decode.delta_freq_hz))

        # Mode string
        mode_bytes = decode.mode.encode("utf-8")
        buf.extend(struct.pack(">I", len(mode_bytes)))
        buf.extend(mode_bytes)

        # Message string
        msg_bytes = decode.message.encode("utf-8")
        buf.extend(struct.pack(">I", len(msg_bytes)))
        buf.extend(msg_bytes)

        # Low confidence (bool)
        buf.extend(struct.pack(">?", False))
        # Modifiers (0=no modifier, 1=Shift, 2=Ctrl, 3=Alt)
        buf.extend(struct.pack(">B", 0))

        try:
            self.sock.sendto(buf, self.remote_addr)
            logger.info(f"Sent Reply command to WSJT-X for: {decode.message}")
        except Exception as e:
            logger.error(f"Failed to send reply to WSJT-X: {e}")

    def halt_tx(self, auto_only: bool = False) -> None:
        """Tell WSJT-X to stop transmitting immediately."""
        if not self.remote_addr or not self.sock:
            return

        buf = bytearray()
        buf.extend(struct.pack(">I", WSJTX_MAGIC))
        buf.extend(struct.pack(">I", WSJTX_SCHEMA_VERSION))
        buf.extend(struct.pack(">I", MSG_HALTTX))

        id_bytes = self.wsjt_client_id.encode("utf-8")
        buf.extend(struct.pack(">I", len(id_bytes)))
        buf.extend(id_bytes)
        buf.extend(struct.pack(">?", auto_only))

        try:
            self.sock.sendto(buf, self.remote_addr)
            logger.info("Sent HaltTx command to WSJT-X")
        except Exception as e:
            logger.error(f"Failed to send HaltTx to WSJT-X: {e}")

    def trigger_cq(self) -> None:
        """Configure WSJT-X to call CQ."""
        self.set_free_text("CQ", send=True)

    def set_free_text(self, text: str, send: bool = False) -> None:
        """Send free text message to WSJT-X."""
        if not self.remote_addr or not self.sock:
            return

        buf = bytearray()
        buf.extend(struct.pack(">I", WSJTX_MAGIC))
        buf.extend(struct.pack(">I", WSJTX_SCHEMA_VERSION))
        buf.extend(struct.pack(">I", MSG_FREETEXT))

        id_bytes = self.wsjt_client_id.encode("utf-8")
        buf.extend(struct.pack(">I", len(id_bytes)))
        buf.extend(id_bytes)

        txt_bytes = text.strip().encode("utf-8")
        buf.extend(struct.pack(">I", len(txt_bytes)))
        buf.extend(txt_bytes)
        buf.extend(struct.pack(">?", send))

        try:
            self.sock.sendto(buf, self.remote_addr)
            logger.info(f"Sent FreeText ('{text}') to WSJT-X (send={send})")
        except Exception as e:
            logger.error(f"Failed to send FreeText to WSJT-X: {e}")

    # --- Packet Receiving & Parsing ---

    def _recv_loop(self) -> None:
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                self.remote_addr = addr
                self._parse_packet(data)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.debug(f"WSJT-X recv error: {e}")

    def _parse_packet(self, data: bytes) -> None:
        if len(data) < 12:
            return

        parser = QDataStreamParser(data)
        try:
            magic = parser.read_u32()
            if magic != WSJTX_MAGIC:
                return

            schema = parser.read_u32()
            msg_type = parser.read_u32()
            client_id = parser.read_string()
            self.wsjt_client_id = client_id

            if msg_type == MSG_HEARTBEAT:
                self.status.last_heard = time.time()

            elif msg_type == MSG_STATUS:
                self.status.dial_freq_hz = parser.read_u64()
                self.status.mode = parser.read_string()
                self.status.dx_call = parser.read_string()
                self.status.report = parser.read_string()
                self.status.tx_mode = parser.read_string()
                self.status.tx_enabled = parser.read_bool()
                self.status.transmitting = parser.read_bool()
                self.status.decoding = parser.read_bool()
                self.status.rx_df = parser.read_u32()
                self.status.tx_df = parser.read_u32()
                self.status.de_call = parser.read_string()
                self.status.de_grid = parser.read_string()
                self.status.dx_grid = parser.read_string()
                self.status.last_heard = time.time()

            elif msg_type == MSG_DECODE:
                is_new = parser.read_bool()
                time_ms = parser.read_u32()
                snr = parser.read_i32()
                delta_time = parser.read_double()
                delta_freq = parser.read_u32()
                mode = parser.read_string()
                message = parser.read_string()

                # Parse callsign & grid from message
                # Message format e.g. "CQ SOTA HB9XXX JN47" or "CQ HB9XXX JN47" or "HB9XXX DL1ABC -12"
                tokens = message.split()
                callsign = None
                grid = None
                is_cq = "CQ" in tokens

                if len(tokens) >= 2:
                    if tokens[0] == "CQ":
                        if len(tokens) >= 3 and tokens[1] in ("SOTA", "POTA", "DX"):
                            callsign = tokens[2]
                            grid = tokens[3] if len(tokens) > 3 else None
                        else:
                            callsign = tokens[1]
                            grid = tokens[2] if len(tokens) > 2 else None
                    else:
                        callsign = tokens[1]
                        grid = tokens[2] if len(tokens) > 2 else None

                # Format time HH:MM:SS
                secs = time_ms // 1000
                h = (secs // 3600) % 24
                m = (secs // 60) % 60
                s = secs % 60
                time_str = f"{h:02d}:{m:02d}:{s:02d}"

                dec = WSJTXDecode(
                    time_str=time_str,
                    snr_db=snr,
                    delta_time_s=round(delta_time, 2),
                    delta_freq_hz=delta_freq,
                    mode=mode,
                    message=message,
                    callsign=callsign,
                    grid=grid,
                    raw_time_ms=time_ms,
                    is_cq=is_cq,
                )
                self.decodes.append(dec)
                if self.on_decode_callback:
                    self.on_decode_callback(dec)

            elif msg_type == MSG_CLEAR:
                self.clear_decodes()

            elif msg_type == MSG_QSOLOGGED:
                # Capture logged QSO automatically into sota_log.csv
                dt = datetime.now(timezone.utc)
                dx_call = parser.read_string()
                dx_grid = parser.read_string()
                dial_freq = parser.read_u64()
                mode = parser.read_string()
                rst_sent = parser.read_string()
                rst_rcvd = parser.read_string()

                logger.info(f"Auto-Logged QSO from WSJT-X: {dx_call} ({mode}) Sent:{rst_sent} Rcvd:{rst_rcvd}")
                with open("sota_log.csv", "a") as f:
                    f.write(f"{dt.strftime('%Y-%m-%d,%H:%M')},{dx_call},{mode},{rst_sent},{rst_rcvd}\n")

        except Exception as e:
            logger.debug(f"Packet parse error: {e}")
