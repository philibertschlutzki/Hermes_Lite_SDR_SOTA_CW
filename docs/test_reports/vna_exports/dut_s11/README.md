# DUT S11 (Return Loss / VSWR) Measurements

This directory contains S11 (reflection) measurements of the HL2 TX output and associated TX chain components.

## Purpose

S11 measurements verify:
- Output impedance matching (50Ω nominal)
- VSWR at TX frequencies
- Proper filter/matching network operation
- Absence of severe resonances or mismatches

## Measurement Setup

1. Calibrate VNA (SOLT) at the measurement reference plane
2. Connect DUT (HL2 output + filters/relays) to VNA Port 1
3. Terminate unused ports with 50Ω load
4. Measure S11 (reflection coefficient)

## Interpretation

- **S11 (dB)**: Return loss - more negative is better (less reflection)
  - < -10 dB: Acceptable (VSWR < 2:1)
  - < -14 dB: Good (VSWR < 1.5:1)
  - < -20 dB: Excellent (VSWR < 1.2:1)

- **VSWR**: Voltage Standing Wave Ratio
  - < 2:1: Acceptable for amateur use
  - < 1.5:1: Good
  - < 1.2:1: Excellent

## Expected Results

HL2 output is typically well-matched (close to 50Ω) across HF bands when:
- Using appropriate bandpass/lowpass filters
- Proper antenna matching
- Good quality connectors and cables

## File Naming

Examples:
- `2026-01-04_s11_hl2_bareoutput.s1p` - HL2 output alone
- `2026-01-04_s11_hl2_40m_lpf.s1p` - With 40m LPF
- `2026-01-04_s11_complete_txchain_20m.s1p` - Full TX path for 20m

## Troubleshooting

If S11 shows poor matching:
- Check connector torque and cleanliness
- Verify filter is correct for band
- Check for damaged cables or adapters
- Ensure dummy load or antenna is 50Ω
- Measure filter independently (see filters_s21/)
