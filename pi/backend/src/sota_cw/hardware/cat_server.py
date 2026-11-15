"""
Lightweight Hamlib rigctld protocol server (TCP port 4532).

Allows WSJT-X, fldigi, and other standard amateur radio software to control
the Hermes-Lite 2 via standard Hamlib 'NET rigctl' protocol.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..hl2_control import HL2Control

logger = logging.getLogger(__name__)


class HamlibCatServer:
    """Async TCP Server implementing Hamlib rigctld protocol commands."""

    def __init__(self, hl2: HL2Control, host: str = "127.0.0.1", port: int = 4532):
        self.hl2 = hl2
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.running: bool = False

    async def start(self) -> None:
        """Start the rigctld TCP server."""
        if self.running:
            return
        self.running = True
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        logger.info(f"Hamlib rigctld CAT server listening on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the rigctld TCP server."""
        self.running = False
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Hamlib rigctld CAT server stopped.")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle individual client connections (e.g. WSJT-X or fldigi)."""
        addr = writer.get_extra_info("peername")
        logger.debug(f"CAT client connected from {addr}")

        try:
            while self.running:
                line = await reader.readline()
                if not line:
                    break

                cmd_str = line.decode("ascii", errors="ignore").strip()
                if not cmd_str:
                    continue

                response = self._process_command(cmd_str)
                if response is not None:
                    writer.write(response.encode("ascii"))
                    await writer.drain()

        except Exception as e:
            logger.debug(f"CAT client error: {e}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            logger.debug(f"CAT client disconnected from {addr}")

    def _process_command(self, cmd_line: str) -> Optional[str]:
        """Parse Hamlib rigctld text command and return text response."""
        tokens = cmd_line.split()
        if not tokens:
            return None

        cmd = tokens[0]

        # 1. Get Frequency: 'f' or '\get_freq'
        if cmd in ("f", "\\get_freq"):
            return f"{self.hl2.frequency_hz}\n"

        # 2. Set Frequency: 'F <hz>' or '\set_freq <hz>'
        elif cmd in ("F", "\\set_freq") and len(tokens) > 1:
            try:
                hz = int(tokens[1])
                self.hl2.set_frequency_hz(hz)
                return "RPRT 0\n"
            except Exception:
                return "RPRT -1\n"

        # 3. Get Mode: 'm' or '\get_mode'
        elif cmd in ("m", "\\get_mode"):
            mode = self.hl2.mode
            # Return mode and default passband width
            width = 3000 if mode in ("USB", "LSB", "DIGU", "PKTUSB") else 500
            return f"{mode}\n{width}\n"

        # 4. Set Mode: 'M <mode> <width>' or '\set_mode <mode> <width>'
        elif cmd in ("M", "\\set_mode") and len(tokens) > 1:
            mode = tokens[1]
            self.hl2.set_mode(mode)
            return "RPRT 0\n"

        # 5. Get PTT: 't' or '\get_ptt'
        elif cmd in ("t", "\\get_ptt"):
            ptt = 1 if self.hl2.is_transmitting else 0
            return f"{ptt}\n"

        # 6. Set PTT: 'T <0|1>' or '\set_ptt <0|1>'
        elif cmd in ("T", "\\set_ptt") and len(tokens) > 1:
            try:
                ptt_val = int(tokens[1])
                self.hl2.set_ptt(ptt_val != 0)
                return "RPRT 0\n"
            except Exception:
                return "RPRT -1\n"

        # 7. Dump state / capabilities: '\dump_state'
        elif cmd == "\\dump_state":
            return (
                "0\n"  # Rigctl protocol version
                "2\n"  # Rig model: NET rigctl
                "1\n"  # ITU region
                "100000.000000 60000000.000000 0xef -1 -1 0x1 0x0\n"  # RX range
                "1800000.000000 29700000.000000 0xef 5000 5000 0x1 0x0\n"  # TX range (kein 6-m-TX: N2ADR ohne 6-m-Filter)
                "0 0 0 0 0 0 0\n"
                "0 0 0 0 0 0 0\n"
                "0xef 500\n"  # CW filter
                "0xef 3000\n" # SSB filter
                "0 0\n"
                "RPRT 0\n"
            )

        # 8. Quit
        elif cmd in ("q", "quit", "\\quit"):
            return None

        # Fallback for unsupported commands: Success return
        return "RPRT 0\n"
