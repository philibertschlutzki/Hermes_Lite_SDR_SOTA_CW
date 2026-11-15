"""Audio-Pfade zwischen HL2-IQ und PipeWire / Tablet / CW-Decoder.

RX (A1, A3):
    HL2Client IQ-Callback -> Queue -> Demodulator (Mode des HL2Control)
        -> PipeWire `SDR_RX_Sink` (WSJT-X, fldigi lesen dessen Monitor)
        -> AudioStreamer (/ws/audio, Tablet)
        -> CW-Decoder (multimon-ng, 22 050 Hz)

TX (A2):
    PipeWire `Digital_TX_Sink.monitor` (WSJT-X/fldigi spielen dorthin)
        -> Ringpuffer -> SSBModulator -> HL2Client TX-Quelle (EP2-IQ bei MOX)

CW läuft nicht über diesen Pfad: Das Keying macht der Pico (cw_jobs.py).
Die PipeWire-Anbindung nutzt `pacat`/`parec` (pipewire-pulse); fehlen die
Programme, laufen nur Tablet-Stream und CW-Decoder.
"""
from __future__ import annotations

import logging
import queue
import shlex
import shutil
import subprocess
import threading
from typing import Callable, Optional

import numpy as np

from ..dsp import FS, Demodulator, SSBModulator, float_to_pcm16

logger = logging.getLogger(__name__)

AudioConsumer = Callable[[np.ndarray], None]

SSB_MODES = ("USB", "LSB", "DIGU", "DIGL", "AM", "SAM")


class _Subprocess:
    def __init__(self, cmd: str, *, stdin: bool):
        self.cmd = cmd
        self.stdin = stdin
        self.proc: Optional[subprocess.Popen] = None

    def available(self) -> bool:
        argv = shlex.split(self.cmd)
        return bool(argv) and shutil.which(argv[0]) is not None

    def start(self) -> bool:
        if not self.available():
            logger.warning("Audio-Programm nicht gefunden: %s", self.cmd)
            return False
        try:
            self.proc = subprocess.Popen(
                shlex.split(self.cmd),
                stdin=subprocess.PIPE if self.stdin else subprocess.DEVNULL,
                stdout=None if self.stdin else subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            return True
        except OSError as e:
            logger.warning("Audio-Programm startet nicht (%s): %s", self.cmd, e)
            self.proc = None
            return False

    def stop(self) -> None:
        if self.proc is None:
            return
        try:
            self.proc.terminate()
            self.proc.wait(timeout=2)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None


class RxAudioPipeline:
    def __init__(self, *, mode: str = "CWU", cw_pitch_hz: float = 600.0, sink_cmd: Optional[str] = None):
        self.demod = Demodulator(mode, cw_pitch_hz=cw_pitch_hz)
        self._consumers: list[AudioConsumer] = []
        self._q: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=200)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._sink = _Subprocess(sink_cmd, stdin=True) if sink_cmd else None
        self.dropped_blocks = 0

    def add_consumer(self, c: AudioConsumer) -> None:
        self._consumers.append(c)

    def set_mode(self, mode: str) -> None:
        self.demod.set_mode(mode)

    def on_iq(self, iq: np.ndarray) -> None:
        """Aufruf aus dem HL2-RX-Thread: nur einreihen."""
        try:
            self._q.put_nowait(iq)
        except queue.Full:
            self.dropped_blocks += 1

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        if self._sink is not None:
            self._sink.start()
        self._thread = threading.Thread(target=self._loop, name="rx-audio", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._sink is not None:
            self._sink.stop()

    def process_block(self, iq: np.ndarray) -> np.ndarray:
        audio = self.demod.process(iq)
        if self._sink is not None and self._sink.proc is not None and self._sink.proc.stdin:
            try:
                self._sink.proc.stdin.write(float_to_pcm16(audio))
            except (BrokenPipeError, OSError):
                logger.warning("PipeWire-RX-Sink beendet, starte neu")
                self._sink.stop()
                self._sink.start()
        for c in self._consumers:
            try:
                c(audio)
            except Exception as e:
                logger.debug("audio consumer failed: %s", e)
        return audio

    def _loop(self) -> None:
        # ~10 Pakete (≈26 ms) bündeln, um Python-Overhead zu senken
        while self._running:
            try:
                first = self._q.get(timeout=0.5)
            except queue.Empty:
                continue
            blocks = [first]
            while len(blocks) < 10:
                try:
                    blocks.append(self._q.get_nowait())
                except queue.Empty:
                    break
            self.process_block(np.concatenate(blocks))


class TxAudioPipeline:
    """Liefert dem HL2Client bei MOX moduliertes IQ aus dem PipeWire-TX-Audio."""

    def __init__(self, *, source_cmd: Optional[str] = None, max_buffer_s: float = 0.5, gain: float = 1.0):
        self.mod = SSBModulator(sideband="USB", gain=gain)
        self.mode = "USB"
        self._buf = np.zeros(0, dtype=np.float32)
        self._lock = threading.Lock()
        self._max = int(max_buffer_s * FS)
        self._src = _Subprocess(source_cmd, stdin=False) if source_cmd else None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.underruns = 0

    def set_mode(self, mode: str) -> None:
        self.mode = mode.upper()
        self.mod.set_sideband(self.mode)

    def push_audio(self, audio: np.ndarray) -> None:
        with self._lock:
            self._buf = np.concatenate((self._buf, np.asarray(audio, dtype=np.float32)))
            if len(self._buf) > self._max:
                self._buf = self._buf[-self._max:]

    def tx_source(self, n: int) -> Optional[np.ndarray]:
        """Callback für HL2Client.set_tx_source."""
        if self.mode not in SSB_MODES:
            return None  # CW: Pico tastet, kein IQ
        with self._lock:
            if len(self._buf) >= n:
                chunk, self._buf = self._buf[:n], self._buf[n:]
            else:
                self.underruns += 1
                chunk = np.concatenate((self._buf, np.zeros(n - len(self._buf), dtype=np.float32)))
                self._buf = np.zeros(0, dtype=np.float32)
        return self.mod.process(chunk)

    def start(self) -> None:
        if self._running or self._src is None:
            return
        if not self._src.start():
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="tx-audio", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._src is not None:
            self._src.stop()

    def _loop(self) -> None:
        assert self._src is not None
        while self._running and self._src.proc is not None and self._src.proc.stdout is not None:
            data = self._src.proc.stdout.read(960 * 2)  # 20 ms
            if not data:
                break
            self.push_audio(np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768.0)
