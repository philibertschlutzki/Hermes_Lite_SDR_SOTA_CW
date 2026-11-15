"""CW-Decoder über multimon-ng.

Intern (Standard): Demoduliertes Audio (48 kHz, aus RxAudioPipeline) wird
auf 22 050 Hz umgetastet (A4) und an `multimon-ng -a MORSE_CW -t raw -`
geschickt. Der HL2-Stream gehört dem zentralen HL2Client; der Decoder öffnet
keinen eigenen Socket (G6).

Legacy: beliebige Shell-Pipeline (`cw_decoder_cmd_legacy`).
"""
import collections
import logging
import queue
import shutil
import subprocess
import threading

import numpy as np

from .config import CW_DECODER_CMD_INTERNAL, CW_DECODER_CMD_LEGACY, USE_INTERNAL_STREAMER
from .dsp import FS, Resampler, float_to_pcm16

logger = logging.getLogger(__name__)

MULTIMON_RATE = 22050


class CWDecoder:
    def __init__(self, buffer_size=100, *, use_internal=USE_INTERNAL_STREAMER):
        self.process = None
        self.thread = None
        self.writer_thread = None
        self.running = False
        self.use_internal = use_internal
        self.text_buffer = collections.deque(maxlen=buffer_size)
        self._audio_q: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=100)
        self._resampler = Resampler(FS, MULTIMON_RATE)

    def start(self):
        if self.running:
            return
        cmd0 = CW_DECODER_CMD_INTERNAL[0] if self.use_internal else None
        if cmd0 and shutil.which(cmd0) is None:
            logger.warning("multimon-ng nicht installiert, CW-Decoder bleibt aus")
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_decoder, daemon=True)
        self.thread.start()
        logger.info("CW-Decoder gestartet (intern: %s)", self.use_internal)

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        logger.info("CW-Decoder gestoppt")

    def get_text(self):
        return list(self.text_buffer)

    def clear_text(self):
        self.text_buffer.clear()

    # Consumer für RxAudioPipeline (nur sinnvoll in CW-Modes)
    def feed_audio(self, audio: np.ndarray) -> None:
        if not self.running or not self.use_internal:
            return
        try:
            self._audio_q.put_nowait(audio)
        except queue.Full:
            pass

    def _writer(self, stdin) -> None:
        while self.running:
            try:
                audio = self._audio_q.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                stdin.write(float_to_pcm16(self._resampler.process(audio)))
                stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                break

    def _run_decoder(self):
        try:
            if self.use_internal:
                self.process = subprocess.Popen(
                    CW_DECODER_CMD_INTERNAL,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                self.writer_thread = threading.Thread(target=self._writer, args=(self.process.stdin,), daemon=True)
                self.writer_thread.start()
            else:
                self.process = subprocess.Popen(
                    CW_DECODER_CMD_LEGACY, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                )

            assert self.process.stdout is not None
            while self.running and self.process.poll() is None:
                raw = self.process.stdout.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="replace")
                if "CW: " in line:
                    decoded = line.replace("CW: ", "").strip()
                    if decoded:
                        self.text_buffer.append(decoded)
        except Exception as e:
            logger.error("CW-Decoder-Fehler: %s", e)
        finally:
            self.running = False
            if self.process and self.process.stdout:
                self.process.stdout.close()
