import socket
import struct
import time
import sys
import argparse
import signal
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)
logger = logging.getLogger(__name__)

# Metis/HL2 Protocol Constants
METIS_PORT = 1024
METIS_DISCOVERY = b'\xef\xfe\x02' + b'\x00' * 61
METIS_START = b'\xef\xfe\x04\x01' + b'\x00' * 60
METIS_STOP = b'\xef\xfe\x04\x00' + b'\x00' * 60

class HL2Streamer:
    def __init__(self, interface_ip="0.0.0.0", hl2_ip=None):
        self.interface_ip = interface_ip
        self.hl2_ip = hl2_ip
        self.sock = None
        self.running = False
        self.sequence = 0
        
        # Audio processing state
        self.phase = 0
        self.sample_rate = 48000 # Default HL2
        self.cw_pitch = 600
        self.b, self.a = None, None # Filter coefficients

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
        HL2 sends 16-bit big-endian integers: I (16), Q (16), I (16), Q (16)...
        """
        # Convert buffer to numpy array of int16, big-endian
        raw = np.frombuffer(iq_data, dtype='>i2')
        
        # Separate I and Q
        # raw is [I0, Q0, I1, Q1, ...]
        i_samples = raw[0::2].astype(np.float32)
        q_samples = raw[1::2].astype(np.float32)
        
        # Create complex signal
        return i_samples + 1j * q_samples

    def _demod_cw(self, complex_iq):
        """
        Simple CW demodulation:
        1. Mix (frequency shift) to center the signal at pitch.
           Actually, if we tune the VFO exactly, CW is at DC. 
           But usually we want an audio tone.
           So we shift by cw_pitch Hz.
        2. Low pass filter? (Optional, relying on multimon-ng's robustness for now or simple averaging)
        3. Real component or Magnitude? For CW, we want the beat note.
           Wait, if we tune to the carrier, we get DC. We need to receive with an offset (CWR) or mix digitally.
           Let's assume the VFO is set to f_carrier. 
           We mix with e^(j*2*pi*pitch*t) to get the tone.
        """
        # Time vector for this block
        num_samples = len(complex_iq)
        t = (np.arange(num_samples) + self.sequence) / self.sample_rate
        self.sequence += num_samples
        
        # Mixing for CW sidetone generation (if VFO is zero-beat)
        # tone = complex_iq * np.exp(1j * 2 * np.pi * self.cw_pitch * t)
        
        # Simplified: Just take the Real part of the mixed signal? 
        # Or magnitude? Magnitude gives the envelope (no tone).
        # We need a TONE for multimon-ng (which expects audio tones).
        # So we mix IQ with the pitch frequency.
        # Result is complex audio. Real part is mono audio.
        
        mixer = np.exp(1j * 2 * np.pi * self.cw_pitch * t)
        shifted = complex_iq * mixer
        
        # Take real part for audio output
        audio = np.real(shifted)
        
        # Normalize/Clip
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
                    data, _ = self.sock.recvfrom(2048) # Typically 1032 bytes
                    
                    # Check for Metis Header
                    if data.startswith(b'\xef\xfe\x01'):
                        # Data packet
                        # Sequence number is byte 3
                        # Payload starts at byte 8 (usually)
                        # Actually standard: 8 bytes header, then data.
                        # data len is usually 1024 or 512.
                        # Protocol 1: 8 header + 512 data (EP6) + 512 data (EP6)? 
                        # Or just 8 + 1024.
                        # Let's assume standard HL2: 1032 bytes total.
                        
                        payload = data[16:] # Skip header (8) + ? 
                        # Wait, standard HPSDR packet:
                        # 8 bytes header.
                        # Then 512 bytes of samples (L/R).
                        # Then maybe another 512 bytes?
                        # HL2 usually fills the UDP packet.
                        # Let's just grab from byte 16 to end for safety or check spec.
                        # Standard: Header (8 bytes). Data (1024 bytes).
                        # Let's try skipping 8 bytes.
                        payload = data[8:]
                        
                        if out_file:
                            if demod:
                                # Process IQ -> Audio
                                complex_iq = self._process_iq_block(payload)
                                audio_pcm = self._demod_cw(complex_iq)
                                out_file.write(audio_pcm.tobytes())
                            else:
                                # Raw IQ Recording
                                out_file.write(payload)
                                
                except socket.timeout:
                    continue
                except KeyboardInterrupt:
                    break
        finally:
            self.send_command(METIS_STOP)
            logger.info("Stream stopped.")

def main():
    parser = argparse.ArgumentParser(description="Hermes Lite 2 Headless Streamer/Recorder")
    parser.add_argument("--ip", help="Specific HL2 IP Address (optional)")
    parser.add_argument("--out", help="Output file (or '-' for stdout)", required=True)
    parser.add_argument("--demod", help="Demodulation mode", choices=['cw', 'none'], default='none')
    parser.add_argument("--pitch", help="CW Pitch in Hz", type=int, default=600)
    
    args = parser.parse_args()
    
    streamer = HL2Streamer(hl2_ip=args.ip)
    streamer.cw_pitch = args.pitch
    
    # Handle Output
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
