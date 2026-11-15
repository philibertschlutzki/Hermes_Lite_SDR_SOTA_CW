"""HL2-IQ-Hilfen und Kommandozeilen-Recorder.

Der eigentliche Stream läuft über `HL2Client` (ein Socket, Protocol 1).
Dieses Modul stellt `FIRFilter` (Rückwärtskompatibilität), die 24-bit-IQ-
Zerlegung und ein CLI zum Mitschneiden/Demodulieren bereit.
"""
import argparse
import logging
import sys
import threading

import numpy as np

from .hl2_protocol import parse_ep6_packet, parse_rx_frame_samples  # noqa: F401  (Re-Export)

logger = logging.getLogger(__name__)

class FIRFilter:
    """
    Basic FIR filter implementation using overlap-save/add logic (via state)
    to handle streaming data without discontinuities.
    """
    def __init__(self, cutoff_hz, sample_rate, num_taps=101):
        self.taps = self._design_lowpass_fir(num_taps, cutoff_hz, sample_rate)
        self.state = np.zeros(num_taps - 1, dtype=np.complex64)

    def _design_lowpass_fir(self, num_taps, cutoff_hz, fs):
        # Windowed Sinc Filter (Blackman window)
        nyquist = 0.5 * fs
        norm_cutoff = cutoff_hz / nyquist
        
        # Sinc
        n = np.arange(num_taps)
        h = np.sinc(2 * norm_cutoff * (n - (num_taps - 1) / 2))
        
        # Window
        w = np.blackman(num_taps)
        h = h * w
        
        # Normalize
        h = h / np.sum(h)
        return h.astype(np.float32)

    def filter(self, signal):
        # Concatenate state (tail of previous chunk) with new signal
        x = np.concatenate((self.state, signal))
        
        # Update state for next chunk
        self.state = x[-len(self.state):]
        
        # Convolve
        # mode='valid' returns output of length len(x) - len(taps) + 1
        # Since we prepended (num_taps - 1) samples, the output length equals len(signal)
        filtered = np.convolve(x, self.taps, mode='valid')
        return filtered

def parse_iq_packet(pkt: bytes) -> np.ndarray:
    """EP6-Paket -> 126 komplexe RX1-Samples (24 bit, normiert auf +-1)."""
    ep6 = parse_ep6_packet(pkt)
    if ep6 is None:
        return np.zeros(0, dtype=np.complex64)
    return ep6.iq


def main() -> None:
    from .dsp import Demodulator, float_to_pcm16
    from .hl2_client import HL2Client

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Hermes Lite 2 Headless Recorder")
    parser.add_argument("--ip", help="HL2 IP (sonst Discovery)")
    parser.add_argument("--freq", type=int, default=7_030_000, help="RX-Frequenz in Hz")
    parser.add_argument("--out", required=True, help="Ausgabedatei oder '-' für stdout")
    parser.add_argument("--demod", choices=["none", "cwu", "usb", "lsb", "am"], default="none",
                        help="none = rohe IQ (complex64), sonst 48 kHz s16le Audio")
    parser.add_argument("--pitch", type=int, default=600)
    args = parser.parse_args()

    ip = args.ip
    if not ip:
        found = HL2Client.discover()
        if not found:
            logger.error("Kein HL2 gefunden")
            sys.exit(1)
        ip = found[0][0]
        logger.info("HL2 gefunden: %s", ip)

    out = sys.stdout.buffer if args.out == "-" else open(args.out, "wb")
    demod = None if args.demod == "none" else Demodulator(args.demod.upper() if args.demod != "cwu" else "CWU",
                                                          cw_pitch_hz=args.pitch)
    lock = threading.Lock()

    def on_iq(iq: np.ndarray) -> None:
        with lock:
            if demod is None:
                out.write(iq.astype(np.complex64).tobytes())
            else:
                out.write(float_to_pcm16(demod.process(iq)))

    client = HL2Client(ip)
    client.set_register(0x01, args.freq)
    client.set_register(0x02, args.freq)
    client.add_iq_callback(on_iq)
    client.start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        client.stop()
        if out is not sys.stdout.buffer:
            out.close()


if __name__ == "__main__":
    main()
