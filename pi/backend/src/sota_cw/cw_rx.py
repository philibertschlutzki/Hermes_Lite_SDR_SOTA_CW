import subprocess
import threading
import collections
import logging
import shlex
import time
import sys
from .config import USE_INTERNAL_STREAMER, CW_DECODER_CMD_INTERNAL, CW_DECODER_CMD_LEGACY
from .hl2_stream import HL2Streamer

logger = logging.getLogger(__name__)

class CWDecoder:
    def __init__(self, buffer_size=100):
        self.process = None
        self.thread = None
        self.streamer_thread = None
        self.running = False
        self.text_buffer = collections.deque(maxlen=buffer_size)
        self.streamer = None

    def start(self):
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_decoder, daemon=True)
        self.thread.start()
        logger.info(f"CW Decoder started (Internal Streamer: {USE_INTERNAL_STREAMER})")

    def stop(self):
        self.running = False
        
        # Stop internal streamer if active
        if self.streamer:
            self.streamer.stop()
            
        # Stop multimon-ng
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

    def _run_internal_streamer(self, stdin_pipe):
        """Thread target: Pumps audio from HL2Streamer to multimon-ng stdin"""
        self.streamer = HL2Streamer()
        # Configure Pitch/Filter if needed (using defaults for now)
        # self.streamer.cw_pitch = 600 
        
        try:
            # stream() blocks until stopped or error
            # We pass the stdin pipe as the output file
            self.streamer.stream(out_file=stdin_pipe, demod=True)
        except Exception as e:
            logger.error(f"Streamer thread failed: {e}")
        finally:
            # Ensure pipe is closed to signal EOF to multimon-ng
            try:
                stdin_pipe.close()
            except:
                pass

    def _run_decoder(self):
        try:
            if USE_INTERNAL_STREAMER:
                # Start multimon-ng with STDIN pipe
                self.process = subprocess.Popen(
                    CW_DECODER_CMD_INTERNAL,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                # Start HL2 Streamer in separate thread to feed stdin
                self.streamer_thread = threading.Thread(
                    target=self._run_internal_streamer, 
                    args=(self.process.stdin,),
                    daemon=True
                )
                self.streamer_thread.start()
                
            else:
                # Legacy: Run shell command pipeline
                self.process = subprocess.Popen(
                    CW_DECODER_CMD_LEGACY,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
            
            # Read stdout loop
            while self.running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if not line:
                    continue
                
                if "CW: " in line:
                    decoded = line.replace("CW: ", "").strip()
                    if decoded:
                        self.text_buffer.append(decoded)
                        
        except Exception as e:
            logger.error(f"Error in CW decoder process: {e}")
        finally:
            if self.process:
                if self.process.stdout: self.process.stdout.close()
                if self.process.stderr: self.process.stderr.close()
