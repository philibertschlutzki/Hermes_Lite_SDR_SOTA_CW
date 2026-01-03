import time
import re
import logging
import threading
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

class QSOState(Enum):
    IDLE = auto()
    SENDING_CQ = auto()
    LISTENING_FOR_CALL = auto()
    SENDING_REPORT = auto()
    WAITING_FOR_CONFIRM = auto()
    SENDING_73 = auto()
    LOGGING = auto()

@dataclass
class BotConfig:
    my_call: str
    my_ref: str = ""  # e.g. HB/ZH-001
    wpm: int = 20
    cq_interval: int = 5  # seconds between CQ loops
    max_loops: int = 3    # how many times to call CQ before giving up

class QSOBot:
    def __init__(self, cw_manager, cw_decoder, config: BotConfig):
        self.cw_manager = cw_manager
        self.cw_decoder = cw_decoder
        self.config = config
        self.state = QSOState.IDLE
        self.running = False
        self.thread = None
        self.current_partner_call = None
        self.cq_loop_count = 0
        self.last_state_change = 0.0

    def start(self):
        if self.running:
            return
        self.running = True
        self.state = QSOState.IDLE
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info("QSO Bot started")

    def stop(self):
        self.running = False
        self.state = QSOState.IDLE
        logger.info("QSO Bot stopped")

    def _loop(self):
        while self.running:
            time.sleep(0.5)
            
            # Simple State Machine
            if self.state == QSOState.IDLE:
                # Waiting for manual trigger to start CQ sequence via API
                pass

            elif self.state == QSOState.SENDING_CQ:
                if not self.cw_manager.is_busy():
                    text = f"CQ SOTA {self.config.my_call} {self.config.my_call} {self.config.my_ref} K"
                    logger.info(f"Bot Sending: {text}")
                    self.cw_manager.start_job(text, self.config.wpm)
                    self._change_state(QSOState.LISTENING_FOR_CALL)
                    # Clear RX buffer to not match old text
                    self.cw_decoder.clear_text()

            elif self.state == QSOState.LISTENING_FOR_CALL:
                if self.cw_manager.is_busy():
                    continue # Still sending

                # Check for timeout (e.g. 10s listen time)
                if (time.time() - self.last_state_change) > 10.0:
                    self.cq_loop_count += 1
                    if self.cq_loop_count < self.config.max_loops:
                        logger.info("Timeout listening, calling CQ again...")
                        self._change_state(QSOState.SENDING_CQ)
                    else:
                        logger.info("Max CQ loops reached. Going IDLE.")
                        self._change_state(QSOState.IDLE)
                    continue

                # Analyze RX text
                lines = self.cw_decoder.get_text()
                # Join last few lines to handle split calls
                rx_content = " ".join(lines[-3:]).upper()
                
                # Basic Regex for Callsign (simplified)
                # Look for DE [CALL] or just [CALL] different from mine
                # Avoiding my own echo if any
                found_call = self._extract_callsign(rx_content)
                if found_call and found_call != self.config.my_call.upper():
                    logger.info(f"Bot heard callsign: {found_call}")
                    self.current_partner_call = found_call
                    self._change_state(QSOState.SENDING_REPORT)

            elif self.state == QSOState.SENDING_REPORT:
                if not self.cw_manager.is_busy():
                    # Delay slightly
                    time.sleep(1.0)
                    text = f"{self.current_partner_call} 599 599 BK"
                    logger.info(f"Bot Sending: {text}")
                    self.cw_manager.start_job(text, self.config.wpm)
                    self._change_state(QSOState.WAITING_FOR_CONFIRM)
                    self.cw_decoder.clear_text()

            elif self.state == QSOState.WAITING_FOR_CONFIRM:
                if self.cw_manager.is_busy():
                    continue

                if (time.time() - self.last_state_change) > 8.0:
                    logger.info("No confirmation received. Aborting QSO.")
                    self._change_state(QSOState.IDLE) # Or retry
                    continue

                lines = self.cw_decoder.get_text()
                rx_content = " ".join(lines[-3:]).upper()
                
                # Look for confirmation keywords
                if any(x in rx_content for x in ["R", "TU", "73", "CFM", "QSL"]):
                    logger.info("Confirmation received!")
                    self._change_state(QSOState.SENDING_73)

            elif self.state == QSOState.SENDING_73:
                if not self.cw_manager.is_busy():
                    time.sleep(0.5)
                    text = f"TU {self.current_partner_call} 73 {self.config.my_call} SK"
                    logger.info(f"Bot Sending: {text}")
                    self.cw_manager.start_job(text, self.config.wpm)
                    self._change_state(QSOState.LOGGING)

            elif self.state == QSOState.LOGGING:
                if not self.cw_manager.is_busy():
                    self._log_qso()
                    # Reset for next CQ or stop?
                    # For safety, let's go IDLE
                    self._change_state(QSOState.IDLE)

    def trigger_cq(self):
        """Manually trigger the CQ sequence from API"""
        self.cq_loop_count = 0
        self._change_state(QSOState.SENDING_CQ)

    def _change_state(self, new_state):
        self.state = new_state
        self.last_state_change = time.time()
        logger.debug(f"State changed to {self.state.name}")

    def _extract_callsign(self, text):
        # Very naive extractor: Find word with number inside, 3-6 chars long
        # Exclude common keywords
        keywords = ["SOTA", "CQ", "DE", "TEST", "599", "R", "TU", "BK", "SK", "K"]
        words = text.split()
        for w in words:
            w = w.strip()
            if w in keywords: continue
            if w == self.config.my_call.upper(): continue
            # Basic Amateur Radio callsign regex (approx)
            if re.match(r'[A-Z0-9]{1,3}[0-9][A-Z0-9]{1,4}', w):
                return w
        return None

    def _log_qso(self):
        logger.info(f"LOGGED QSO with {self.current_partner_call} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        # Append to a simple CSV file
        with open("sota_log.csv", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d,%H:%M')},{self.current_partner_call},CW,599,599\n")
