import socket
import struct
import time
import sys
import argparse
import logging
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Metis/HL2 Protocol Constants
METIS_PORT = 1024
METIS_DISCOVERY = b'\xef\xfe\x02' + b'\x00' * 61
METIS_START = b'\xef\xfe\x04\x01' + b'\x00' * 60
METIS_STOP = b'\xef\xfe\x04\x00' + b'\x00' * 60

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

class HL2Streamer:
    def __init__(self, interface_ip="0.0.0.0", hl2_ip=None):
        self.interface_ip = interface_ip
        self.hl2_ip = hl2_ip
        self.sock = None
        self.running = False
        self.sequence = 0
        
        # Audio processing state
        self.sample_rate = 48000 # Default HL2
        self.cw_pitch = 600
        self.filter = None

    def _setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.interface_ip, METIS_PORT))
        self.sock.settimeout(1.0)

    def discover(self):
        logger.info("Sending discovery broadcast...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(2.0)
        sock.sendto(METIS_DISCOVERY, ('<broadcast>', METIS_PORT))
        
        try:
            data, addr = sock.recvfrom(1024)
            if data.startswith(b'\xef\xfe\x02'):
                logger.info(f"Found HL2 at {addr[0]}")
                self.hl2_ip = addr[0]
                return True
        except socket.timeout:
            logger.warning("No HL2 response found during discovery.")
        finally:
            sock.close()
        return False

    def send_command(self, cmd):
        if not self.hl2_ip:
            logger.error("HL2 IP not set. Cannot send command.")
            return
        self.sock.sendto(cmd, (self.hl2_ip, METIS_PORT))

    def _process_iq_block(self, iq_data):
        """
        Convert raw bytes to numpy complex array.
        HL2 sends 16-bit big-endian integers.
        """
        raw = np.frombuffer(iq_data, dtype='>i2')
        i_samples = raw[0::2].astype(np.float32)
        q_samples = raw[1::2].astype(np.float32)
        return i_samples + 1j * q_samples

    def _demod_cw(self, complex_iq):
        # Initialize filter if needed
        if self.filter is None:
            # Lowpass at 800Hz (CW bandwidth)
            self.filter = FIRFilter(cutoff_hz=800, sample_rate=self.sample_rate)

        # 1. Frequency Shift (Mixing) to baseband/pitch
        num_samples = len(complex_iq)
        t = (np.arange(num_samples) + self.sequence) / self.sample_rate
        self.sequence += num_samples
        
        # Mix with sidetone pitch to make it audible as a tone
        mixer = np.exp(1j * 2 * np.pi * self.cw_pitch * t)
        shifted = complex_iq * mixer
        
        # 2. Apply FIR Filter (Bandpass/Lowpass)
        # Since we shifted the signal, the "tone" is now at DC + Pitch?
        # Actually:
        # If signal is at 0Hz (tuned exactly), we want to hear it at 600Hz.
        # We mixed it UP by 600Hz.
        # So the wanted signal is at 600Hz.
        # Noise is everywhere else.
        # We should have filtered at Baseband (0Hz) BEFORE mixing if we wanted a narrow filter.
        # OR: We filter around the tone frequency (Bandpass).
        # Let's simplify: 
        # Shift so signal is at DC. Lowpass filter. Then Shift up to Pitch.
        # Efficient approach for Python script:
        # Just mix to audio freq (600Hz) and use the Lowpass (800Hz) as a crude "everything below 800Hz" filter.
        # This keeps the 600Hz tone and kills high frequency noise.
        # For better selectivity, we'd need a Bandpass centered at 600Hz.
        # Let's stick to the Lowpass < 800Hz. It passes the 600Hz tone.
        
        filtered = self.filter.filter(shifted)
        
        # 3. Take Real part for Audio
        audio = np.real(filtered)
        
        # Normalize/Clip
        # Simple AGC / Scaling could go here
        audio = np.clip(audio, -32767, 32767)
        return audio.astype(np.int16)

    def stream(self, out_file=None, demod=False):
        if not self.sock:
            self._setup_socket()
            
        if not self.hl2_ip:
            if not self.discover():
                logger.error("Could not find HL2. Exiting.")
                return

        logger.info(f"Starting stream from {self.hl2_ip}. Demod={demod}")
        self.send_command(METIS_START)
        self.running = True
        
        try:
            while self.running:
                try:
                    data, _ = self.sock.recvfrom(2048)
                    
                    # Check for Metis Header
                    if data.startswith(b'\xef\xfe\x01'):
                        # Standard HL2 data packet
                        # Payload starts after header (usually 8 bytes, but let's be safe with standard offsets)
                        # Depending on protocol version. Assuming standard HPSDR
                        payload = data[8:]
                        
                        if out_file:
                            if demod:
                                complex_iq = self._process_iq_block(payload)
                                audio_pcm = self._demod_cw(complex_iq)
                                out_file.write(audio_pcm.tobytes())
                                out_file.flush()
                            else:
                                out_file.write(payload)
                                out_file.flush()
                                
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    break
        finally:
            self.send_command(METIS_STOP)
            logger.info("Stream stopped.")

    def stop(self):
        self.running = False

def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Hermes Lite 2 Headless Streamer/Recorder")
    parser.add_argument("--ip", help="Specific HL2 IP Address (optional)")
    parser.add_argument("--out", help="Output file (or '-' for stdout)", required=True)
    parser.add_argument("--demod", help="Demodulation mode", choices=['cw', 'none'], default='none')
    parser.add_argument("--pitch", help="CW Pitch in Hz", type=int, default=600)
    
    args = parser.parse_args()
    
    streamer = HL2Streamer(hl2_ip=args.ip)
    streamer.cw_pitch = args.pitch
    
    if args.out == '-':
        out_handle = sys.stdout.buffer
    else:
        out_handle = open(args.out, 'wb')
        
    try:
        streamer.stream(out_file=out_handle, demod=(args.demod == 'cw'))
    except KeyboardInterrupt:
        pass
    finally:
        if args.out != '-':
            out_handle.close()

if __name__ == "__main__":
    main()
