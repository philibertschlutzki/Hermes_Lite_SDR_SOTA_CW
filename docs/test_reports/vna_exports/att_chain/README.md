# Attenuator Chain Characterization

This directory contains S21 (transmission) measurements of the attenuator chain used for TX quality testing.

## Purpose

The attenuator chain reduces HL2 TX output (5W = +37 dBm) to safe levels for NanoVNA-H4 input.

**CRITICAL SAFETY**: Never connect HL2 TX output directly to NanoVNA. Use at least 40-50 dB attenuation.

## Characterization Data

Measure S21 (insertion loss) across all relevant amateur bands to obtain frequency-dependent attenuation A(f).

### Required Measurements

File: `att_chain_characterization.s2p` (or .csv)

- Frequency range: 1 MHz - 30 MHz (covers all HF bands)
- Points: At least 101 (more for higher resolution)
- Measurement: S21 transmission (dB)

### Bill of Materials

Document the exact attenuator chain used:

Example:
```
Attenuator Chain BOM (ID: ATT_CHAIN_01)
-----------------------------------
1. HL2 TX output (SMA F)
2. SMA adapter M-F (if needed)
3. 20 dB SMA attenuator (50Ω, 10W rated)
4. 20 dB SMA attenuator (50Ω, 10W rated)
5. 10 dB SMA attenuator (50Ω, 5W rated)
6. Optional: DC block capacitor (SMA inline)
7. Short SMA cable (RG-316, < 30 cm)
8. NanoVNA Port 1 (SMA F)

Total nominal: 50 dB
Actual measured: ~48-51 dB (frequency dependent)
Power rating: First stage sees max ~17 dBm (50 mW), well within 10W rating
```

## Usage

1. Connect the attenuator chain as it will be used in actual tests
2. Perform SOLT calibration at the DUT connection point (before HL2)
3. Measure S21 (NanoVNA Port 1 -> Port 2 through chain, or use transmission mode)
4. Export Touchstone (.s2p) and/or CSV
5. Save to this directory with descriptive filename
6. Reference this file in `tx_quality_runs.csv` via `att_chain_id` field

## Validation

The characterization should show:
- Relatively flat attenuation across HF (minor frequency dependence expected)
- Total attenuation close to nominal sum (e.g., 48-52 dB for 20+20+10 dB attenuators)
- No unexpected resonances or dips

If measured values deviate significantly from nominal, check:
- Connector tightness
- DC continuity (cold solder joints)
- Attenuator specifications and ratings
