#!/usr/bin/env python3
"""
IQ Replay Tool for SOTA CW HL2

Replays saved IQ data through the CW decoder pipeline for offline testing.

Usage:
    python replay_iq.py <iq_file.npy> [--output decoded.txt]

IQ file format:
    NumPy array (.npy) of complex64 samples at 48 kHz
    Can be captured using hl2_stream with save functionality
"""

import argparse
import sys
import numpy as np
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Replay IQ data through CW decoder")
    parser.add_argument("iq_file", type=Path, help="Input IQ file (.npy format, complex64)")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output text file (default: stdout)")
    parser.add_argument("--sample-rate", "-r", type=int, default=48000, help="Sample rate (default: 48000 Hz)")
    parser.add_argument("--cw-pitch", type=int, default=600, help="CW tone frequency (default: 600 Hz)")
    
    args = parser.parse_args()
    
    if not args.iq_file.exists():
        print(f"Error: IQ file not found: {args.iq_file}", file=sys.stderr)
        return 1
    
    print(f"Loading IQ data from {args.iq_file}...", file=sys.stderr)
    iq_data = np.load(args.iq_file)
    
    if iq_data.dtype != np.complex64:
        print(f"Warning: Converting from {iq_data.dtype} to complex64", file=sys.stderr)
        iq_data = iq_data.astype(np.complex64)
    
    print(f"Loaded {len(iq_data)} samples ({len(iq_data) / args.sample_rate:.2f} seconds)", file=sys.stderr)
    print("\nNote: This tool provides signal analysis.", file=sys.stderr)
    print("Full CW decoding requires multimon-ng integration.", file=sys.stderr)
    
    # Import decoder components
    sys.path.insert(0, str(Path(__file__).parent.parent / "pi" / "backend" / "src"))
    from sota_cw.hl2_stream import FIRFilter
    
    print("Processing IQ data...", file=sys.stderr)
    fir = FIRFilter(cutoff_hz=args.cw_pitch * 2, sample_rate=args.sample_rate, num_taps=101)
    filtered = fir.filter(iq_data)
    envelope = np.abs(filtered)
    
    threshold = np.mean(envelope) + 2 * np.std(envelope)
    keyed = envelope > threshold
    transitions = np.diff(keyed.astype(int))
    key_on = np.where(transitions > 0)[0]
    key_off = np.where(transitions < 0)[0]
    
    output_lines = [
        f"# IQ Replay Analysis: {args.iq_file}",
        f"# Duration: {len(iq_data) / args.sample_rate:.2f} seconds",
        f"# Key Events: {len(key_on)} on, {len(key_off)} off",
        f"# Envelope: Peak={np.max(envelope):.3f}, Mean={np.mean(envelope):.3f}",
    ]
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write('\n'.join(output_lines))
        print(f"\nWrote analysis to {args.output}", file=sys.stderr)
    else:
        print('\n'.join(output_lines))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
