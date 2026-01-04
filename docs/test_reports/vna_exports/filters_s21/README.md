# Filter S21 (Insertion Loss / Rejection) Measurements

This directory contains S21 (transmission) measurements of external filters (LPF, BPF, or matching networks).

## Purpose

S21 measurements characterize:
- **In-band insertion loss** (should be minimal)
- **Out-of-band rejection** (should be high for harmonics suppression)
- Filter alignment and tuning

## Measurement Setup

1. Calibrate VNA (SOLT) at filter connection points
2. Connect filter between VNA Port 1 and Port 2
3. Measure S21 (transmission)
4. Scan full range (1 MHz - 200 MHz or higher for harmonic check)

## Interpretation

### In-Band (Passband)
- **Target**: < 1 dB insertion loss (< 0.5 dB for high-quality filters)
- Flat response across operating bandwidth

### Out-of-Band (Stopband)
- **Target**: > 30 dB rejection at 2nd harmonic
- > 40 dB rejection at 3rd harmonic and higher
- Sharp roll-off for good selectivity

## Examples

40m (7 MHz) Low-Pass Filter:
- Passband: DC - 8 MHz, insertion loss < 0.5 dB
- Stopband: > 14 MHz, rejection > 40 dB

20m (14 MHz) Band-Pass Filter:
- Passband: 13.5 - 14.5 MHz, insertion loss < 1 dB
- Stopband (lower): < 10 MHz, rejection > 30 dB
- Stopband (upper): > 20 MHz, rejection > 40 dB

## File Naming

Examples:
- `2026-01-04_s21_lpf_40m.s2p` - 40m low-pass filter
- `2026-01-04_s21_bpf_20m.s2p` - 20m band-pass filter
- `2026-01-04_s21_diplexer_hf.s2p` - HF diplexer

## Quality Criteria

**PASS** if:
- In-band loss < 1.5 dB (acceptable for portable)
- 2nd harmonic rejection > 30 dB
- No unexpected resonances in stopband

**FAIL** if:
- In-band loss > 2 dB (investigate: tuning, component damage)
- Harmonics rejection < 20 dB (insufficient suppression)
- Severe ripple or resonances

## Troubleshooting

Poor in-band performance:
- Check filter alignment/tuning
- Verify component values
- Check for cold solder joints

Poor out-of-band rejection:
- Increase filter order (more sections)
- Check grounding and shielding
- Verify filter design matches requirements
