"""DSP für RX-Demodulation und SSB/DIGU-TX-Modulation (numpy, 48 kHz).

RX: HL2-IQ (RX1, 48 kHz, Mitte = eingestellte Frequenz) -> Audio 48 kHz.
TX: Audio 48 kHz (WSJT-X/fldigi) -> komplexes Basisband-IQ für EP2.

Konvention: Die RX-/TX-NCO-Frequenz ist die Anzeige-/Dial-Frequenz.
- USB/DIGU: Signal bei +200..+2800 Hz -> Audio 200..2800 Hz
- LSB: Signal bei -2800..-200 Hz
- CWU: CW-Signal auf der Dial-Frequenz (0 Hz) wird als Ton mit `cw_pitch_hz`
  hörbar; das Filter liegt eng um 0 Hz.
- CWL: wie CWU, Ton gespiegelt (gleiches Hörbild).
- AM: Hüllkurve.
"""
from __future__ import annotations

import numpy as np

FS = 48000


def design_lowpass(num_taps: int, cutoff_hz: float, fs: float = FS) -> np.ndarray:
    """Gefensterter Sinc-Tiefpass (Blackman), DC-Verstärkung 1."""
    n = np.arange(num_taps)
    h = np.sinc(2 * cutoff_hz / fs * (n - (num_taps - 1) / 2))
    h *= np.blackman(num_taps)
    h /= np.sum(h)
    return h.astype(np.float32)


def design_complex_bandpass(num_taps: int, f_lo: float, f_hi: float, fs: float = FS) -> np.ndarray:
    """Komplexer Bandpass f_lo..f_hi (auch negative Frequenzen), Verstärkung 1."""
    center = 0.5 * (f_lo + f_hi)
    half_bw = 0.5 * (f_hi - f_lo)
    lp = design_lowpass(num_taps, half_bw, fs).astype(np.complex64)
    n = np.arange(num_taps) - (num_taps - 1) / 2
    return (lp * np.exp(2j * np.pi * center / fs * n)).astype(np.complex64)


class StreamingFIR:
    """FIR mit Zustand über Blockgrenzen (komplex oder reell)."""

    def __init__(self, taps: np.ndarray):
        self.taps = np.asarray(taps)
        self.state = np.zeros(len(self.taps) - 1, dtype=np.complex64)

    def __call__(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.complex64)
        buf = np.concatenate((self.state, x))
        self.state = buf[len(buf) - len(self.state):] if len(self.state) else self.state
        return np.convolve(buf, self.taps, mode="valid").astype(np.complex64)


class AGC:
    """Einfache Spitzenwert-AGC mit schnellem Angriff und langsamem Abklingen."""

    def __init__(self, target: float = 0.3, decay_s: float = 0.5, fs: float = FS, max_gain: float = 1e5):
        self.target = target
        self.peak = 1e-6
        self.decay = float(np.exp(-1.0 / (decay_s * fs)))
        self.max_gain = max_gain

    def __call__(self, x: np.ndarray) -> np.ndarray:
        if len(x) == 0:
            return x
        blk_peak = float(np.max(np.abs(x)))
        decay_blk = self.decay ** len(x)
        self.peak = max(blk_peak, self.peak * decay_blk, 1e-9)
        gain = min(self.target / self.peak, self.max_gain)
        return x * gain


class Demodulator:
    """RX-Demodulator für CWU/CWL/USB/LSB/DIGU/AM."""

    MODES = ("CWU", "CWL", "USB", "LSB", "DIGU", "DIGL", "AM", "SAM")

    def __init__(self, mode: str = "CWU", *, cw_pitch_hz: float = 600.0, cw_bw_hz: float = 500.0,
                 ssb_lo_hz: float = 200.0, ssb_hi_hz: float = 2800.0, num_taps: int = 255, agc: bool = True):
        self.cw_pitch_hz = cw_pitch_hz
        self.cw_bw_hz = cw_bw_hz
        self.ssb_lo_hz = ssb_lo_hz
        self.ssb_hi_hz = ssb_hi_hz
        self.num_taps = num_taps
        self._phase = 0.0
        self.agc = AGC() if agc else None
        self.mode = ""
        self.set_mode(mode)

    def set_mode(self, mode: str) -> None:
        mode = mode.upper()
        if mode not in self.MODES:
            raise ValueError(f"unknown mode {mode}")
        if mode == self.mode:
            return
        self.mode = mode
        if mode in ("CWU", "CWL"):
            half = self.cw_bw_hz / 2
            taps = design_complex_bandpass(self.num_taps, -half, half)
        elif mode in ("USB", "DIGU"):
            taps = design_complex_bandpass(self.num_taps, self.ssb_lo_hz, self.ssb_hi_hz)
        elif mode in ("LSB", "DIGL"):
            taps = design_complex_bandpass(self.num_taps, -self.ssb_hi_hz, -self.ssb_lo_hz)
        else:  # AM
            taps = design_lowpass(self.num_taps, 4000.0).astype(np.complex64)
        self.fir = StreamingFIR(taps)

    def process(self, iq: np.ndarray) -> np.ndarray:
        """IQ (complex, |x|<=1) -> Audio float32 (-1..1)."""
        y = self.fir(iq)
        if self.mode in ("CWU", "CWL"):
            n = np.arange(len(y))
            sign = 1.0 if self.mode == "CWU" else -1.0
            ph = self._phase + sign * 2 * np.pi * self.cw_pitch_hz / FS * n
            self._phase = float((self._phase + sign * 2 * np.pi * self.cw_pitch_hz / FS * len(y)) % (2 * np.pi))
            audio = np.real(y * np.exp(1j * ph))
        elif self.mode in ("AM", "SAM"):
            env = np.abs(y)
            audio = env - np.mean(env) if len(env) else env
        else:
            audio = np.real(y)
        audio = audio.astype(np.float32)
        if self.agc is not None:
            audio = self.agc(audio)
        return np.clip(audio, -1.0, 1.0).astype(np.float32)


class SSBModulator:
    """Audio (reell, 48 kHz) -> komplexes Basisband für USB/LSB/DIGU."""

    def __init__(self, *, sideband: str = "USB", lo_hz: float = 150.0, hi_hz: float = 2900.0, num_taps: int = 255,
                 gain: float = 1.0):
        self.gain = gain
        self.lo_hz = lo_hz
        self.hi_hz = hi_hz
        self.num_taps = num_taps
        self.sideband = ""
        self.set_sideband(sideband)

    def set_sideband(self, sideband: str) -> None:
        sb = "LSB" if sideband.upper() in ("LSB", "DIGL", "CWL") else "USB"
        if sb == self.sideband:
            return
        self.sideband = sb
        if sb == "USB":
            taps = design_complex_bandpass(self.num_taps, self.lo_hz, self.hi_hz)
        else:
            taps = design_complex_bandpass(self.num_taps, -self.hi_hz, -self.lo_hz)
        # Faktor 2: reelles Audio hat die Hälfte der Leistung im positiven Band
        self.fir = StreamingFIR(taps * 2.0)

    def process(self, audio: np.ndarray) -> np.ndarray:
        iq = self.fir(np.asarray(audio, dtype=np.float32)) * self.gain
        mag = np.abs(iq)
        over = mag > 1.0
        if np.any(over):
            iq[over] /= mag[over]  # harte Begrenzung ohne Phasenfehler
        return iq.astype(np.complex64)


class Resampler:
    """Streaming-Resampler (Tiefpass + lineare Interpolation), z. B. 48000 -> 22050."""

    def __init__(self, fs_in: float, fs_out: float, num_taps: int = 127):
        self.fs_in = float(fs_in)
        self.fs_out = float(fs_out)
        self.step = self.fs_in / self.fs_out
        cutoff = 0.45 * min(self.fs_in, self.fs_out)
        self.lp = StreamingFIR(design_lowpass(num_taps, cutoff, self.fs_in)) if fs_out < fs_in else None
        self._t = 0.0          # Position des nächsten Ausgangssamples (relativ zu _prev)
        self._prev = np.zeros(1, dtype=np.float32)

    def process(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float32)
        if self.lp is not None:
            x = np.real(self.lp(x)).astype(np.float32)
        buf = np.concatenate((self._prev, x))
        # Ausgangszeitpunkte im Bereich [0, len(buf)-1)
        positions = np.arange(self._t, len(buf) - 1, self.step)
        out = np.interp(positions, np.arange(len(buf)), buf).astype(np.float32)
        next_t = (positions[-1] + self.step) if len(positions) else self._t
        consumed = len(buf) - 1
        self._t = next_t - consumed
        self._prev = buf[-1:]
        return out


def float_to_pcm16(x: np.ndarray) -> bytes:
    return np.clip(np.round(np.asarray(x) * 32767.0), -32767, 32767).astype("<i2").tobytes()


def pcm16_to_float(b: bytes) -> np.ndarray:
    return (np.frombuffer(b, dtype="<i2").astype(np.float32) / 32768.0)
