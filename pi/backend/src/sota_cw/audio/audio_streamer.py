"""
Audio Streamer for Remote Tablet Playback.

Bekommt demodulierte Audioblöcke aus RxAudioPipeline (feed_audio)
and broadcasts them via WebSocket or HTTP streaming to Android tablet clients.
Features:
- Low-latency circular buffering
- Volume scaling and software squelch
- Multi-client subscription model
"""
from __future__ import annotations

import asyncio
import logging
import math
import struct
import threading
from typing import Set

import numpy as np

logger = logging.getLogger(__name__)


class AudioStreamer:
    """Manages audio distribution to remote web clients (Android Tablet)."""

    def __init__(self, sample_rate: int = 48000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.subscribers: Set[asyncio.Queue] = set()
        self.volume: float = 1.0  # 0.0 to 1.5
        self.squelch_open: bool = True
        self.squelch_threshold: float = 0.0
        self.is_running: bool = False
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self.blocks_sent = 0

    def set_volume(self, vol: float) -> None:
        self.volume = max(0.0, min(2.0, float(vol)))

    def set_squelch(self, threshold: float) -> None:
        self.squelch_threshold = max(0.0, float(threshold))

    def broadcast_pcm(self, pcm_bytes: bytes) -> None:
        """
        Deliver raw 16-bit signed PCM audio bytes to all active subscribers.
        Called from the audio capture or demodulation thread.
        """
        if not self.subscribers:
            return

        # Apply volume scaling if needed
        if abs(self.volume - 1.0) > 0.01:
            try:
                samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
                samples = np.clip(samples * self.volume, -32767, 32767).astype(np.int16)
                pcm_bytes = samples.tobytes()
            except Exception:
                pass

        # Aus dem Audio-Thread an die Event-Loop der WebSocket-Clients übergeben
        loop = self._loop
        for q in list(self.subscribers):
            try:
                if loop is not None and loop.is_running():
                    loop.call_soon_threadsafe(self._queue_put_nowait, q, pcm_bytes)
                else:
                    self._queue_put_nowait(q, pcm_bytes)
            except Exception:
                pass
        self.blocks_sent += 1

    def feed_audio(self, audio: np.ndarray) -> None:
        """Consumer für RxAudioPipeline: float32 -1..1 -> PCM16 an alle Clients."""
        if not self.subscribers:
            return
        pcm = np.clip(np.round(np.asarray(audio) * 32767.0), -32767, 32767).astype(np.int16).tobytes()
        self.broadcast_pcm(pcm)

    def _queue_put_nowait(self, q: asyncio.Queue, data: bytes) -> None:
        try:
            if q.qsize() > 20:  # Prevent buffer buildup on slow networks
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            q.put_nowait(data)
        except Exception:
            pass

    def register_subscriber(self, q: asyncio.Queue) -> None:
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        with self._lock:
            self.subscribers.add(q)
            logger.info(f"New audio subscriber registered. Total: {len(self.subscribers)}")

    def unregister_subscriber(self, q: asyncio.Queue) -> None:
        with self._lock:
            self.subscribers.discard(q)
            logger.info(f"Audio subscriber unregistered. Remaining: {len(self.subscribers)}")
