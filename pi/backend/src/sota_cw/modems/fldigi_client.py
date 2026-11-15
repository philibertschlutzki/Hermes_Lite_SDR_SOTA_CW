"""
fldigi XML-RPC Client.

Communicates with headless fldigi daemon running with `--xmlrpc-server`
on port 7362 (http://127.0.0.1:7362/RPC2).

Provides:
- PSK31, PSK63, RTTY, and CW (DSP decoding)
- Two-way text streaming (character by character)
- Squelch, AFC, and carrier control
"""
from __future__ import annotations

import collections
import enum
import logging
import threading
import time
import xmlrpc.client
from typing import Optional

logger = logging.getLogger(__name__)


class FldigiModem(str, enum.Enum):
    BPSK31 = "BPSK31"
    BPSK63 = "BPSK63"
    QPSK31 = "QPSK31"
    RTTY = "RTTY"
    CW = "CW"


class FldigiClient:
    """Client for headless fldigi XML-RPC server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7362, rx_buffer_size: int = 5000):
        self.url = f"http://{host}:{port}/RPC2"
        self.proxy: Optional[xmlrpc.client.ServerProxy] = None
        self.running: bool = False
        self.thread: Optional[threading.Thread] = None

        self.rx_buffer: collections.deque[str] = collections.deque(maxlen=rx_buffer_size)
        self.current_modem: str = "BPSK31"
        self.is_connected: bool = False
        self.is_transmitting: bool = False

    def connect(self) -> bool:
        """Attempt connection to fldigi XML-RPC daemon."""
        try:
            self.proxy = xmlrpc.client.ServerProxy(self.url, allow_none=True)
            # Test connection with simple ping
            version = self.proxy.fldigi.version()
            self.is_connected = True
            logger.info(f"Connected to fldigi daemon version: {version}")
            return True
        except Exception as e:
            self.is_connected = False
            logger.debug(f"fldigi daemon not reachable on {self.url}: {e}")
            return False

    def start(self) -> None:
        """Start background polling thread for received text."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        logger.info("fldigi RX poller started.")

    def stop(self) -> None:
        """Stop background poller."""
        self.running = False

    def get_rx_text(self) -> str:
        """Get all received text accumulated so far."""
        return "".join(self.rx_buffer)

    def clear_rx_text(self) -> None:
        """Clear received text buffer."""
        self.rx_buffer.clear()

    def set_modem(self, modem: str) -> bool:
        """Set modem type (e.g. BPSK31, BPSK63, RTTY, CW). "PSK31"/"PSK63" werden auf BPSK abgebildet."""
        aliases = {"PSK31": "BPSK31", "PSK63": "BPSK63"}
        modem = aliases.get(str(modem).upper(), str(modem))
        if not self.is_connected and not self.connect():
            return False
        try:
            self.proxy.modem.set_by_name(str(modem))
            self.current_modem = str(modem)
            logger.info(f"fldigi modem switched to {modem}")
            return True
        except Exception as e:
            logger.error(f"Failed to set fldigi modem: {e}")
            return False

    def send_text(self, text: str) -> bool:
        """Queue text for transmission and initiate TX."""
        if not self.is_connected and not self.connect():
            return False
        try:
            # Send text to TX buffer
            self.proxy.text.add_tx(text)
            # Switch to transmit
            self.proxy.main.tx()
            self.is_transmitting = True
            logger.info(f"fldigi sending TX: {text}")
            return True
        except Exception as e:
            logger.error(f"fldigi TX error: {e}")
            return False

    def abort_tx(self) -> bool:
        """Immediately abort transmission and return to receive."""
        if not self.is_connected:
            return False
        try:
            self.proxy.main.rx()
            self.proxy.text.clear_tx()
            self.is_transmitting = False
            logger.info("fldigi TX aborted")
            return True
        except Exception as e:
            logger.error(f"fldigi abort error: {e}")
            return False

    def set_audio_carrier_hz(self, hz: int) -> bool:
        """Set the audio carrier center frequency in the waterfall."""
        if not self.is_connected and not self.connect():
            return False
        try:
            self.proxy.modem.set_carrier(int(hz))
            return True
        except Exception:
            return False

    def set_afc(self, enable: bool) -> bool:
        """Enable or disable Automatic Frequency Control."""
        if not self.is_connected and not self.connect():
            return False
        try:
            self.proxy.main.set_afc(bool(enable))
            return True
        except Exception:
            return False

    def set_squelch(self, enable: bool) -> bool:
        """Enable or disable Squelch."""
        if not self.is_connected and not self.connect():
            return False
        try:
            self.proxy.main.set_squelch(bool(enable))
            return True
        except Exception:
            return False

    def _poll_loop(self) -> None:
        """Background loop reading received text from fldigi."""
        while self.running:
            if not self.is_connected:
                self.connect()
                time.sleep(2.0)
                continue

            try:
                # rx.get_data returns new bytes received since last call
                data = self.proxy.rx.get_data()
                if data:
                    text = str(data.data.decode("latin1", errors="replace")) if hasattr(data, "data") else str(data)
                    for char in text:
                        self.rx_buffer.append(char)

                # Check if transmission finished
                status = self.proxy.main.get_status1()
                # Status string contains 'TX' or 'RX'
                self.is_transmitting = "TX" in str(status)

            except Exception:
                self.is_connected = False

            time.sleep(0.15)
