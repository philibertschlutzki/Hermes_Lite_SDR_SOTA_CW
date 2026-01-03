import subprocess
import threading
import collections
import logging
import shlex
import time
from .config import CW_DECODER_CMD

logger = logging.getLogger(__name__)

class CWDecoder:
    def __init__(self, buffer_size=100):
        self.cmd = CW_DECODER_CMD
        self.process = None
        self.thread = None
        self.running = False
        self.text_buffer = collections.deque(maxlen=buffer_size)

    def start(self):
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_decoder, daemon=True)
        self.thread.start()
        logger.info(f"CW Decoder started with command: {self.cmd}")

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        logger.info("CW Decoder stopped")

    def get_text(self):
        return list(self.text_buffer)

    def clear_text(self):
        self.text_buffer.clear()

    def _run_decoder(self):
        # Use shell=True to allow piping in the command string defined in config
        try:
            self.process = subprocess.Popen(
                self.cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            while self.running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if not line:
                    continue
                
                # multimon-ng output format for CW usually starts with "CW: "
                # We filter specific CW tags
                if "CW: " in line:
                    decoded = line.replace("CW: ", "").strip()
                    if decoded:
                        self.text_buffer.append(decoded)
                        
        except Exception as e:
            logger.error(f"Error in CW decoder process: {e}")
        finally:
            if self.process:
                self.process.stdout.close()
                self.process.stderr.close()
