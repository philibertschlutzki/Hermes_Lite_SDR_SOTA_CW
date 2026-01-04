# VNA Exports

This directory contains VNA measurement data (S-parameters) from NanoVNA-H4 characterization.

## Subdirectories

### att_chain/
Attenuator chain characterization (S21 transmission measurements):
- Measures insertion loss vs. frequency
- Used to correct power level readings
- Re-characterize when attenuator chain changes

### dut_s11/
Return loss (S11) measurements of HL2 output and TX chain:
- VSWR and impedance matching
- Identify resonances or mismatches
- Verify filter/matching network performance

### filters_s21/
Filter insertion loss and rejection (S21):
- In-band insertion loss
- Out-of-band rejection
- Validate external LPF/BPF performance

### screenshots/
VNA screenshots for documentation:
- Save display captures for reference
- Annotate key measurements
- Include in reports for visual confirmation

## File Naming Convention

Use descriptive names with date and configuration:
```
YYYY-MM-DD_<measurement_type>_<band>_<config>.s2p
YYYY-MM-DD_<measurement_type>_<band>_<config>.csv
```

Examples:
- `2026-01-04_att_chain_fullband.s2p`
- `2026-01-04_s11_hl2_40m_lpf.s1p`
- `2026-01-04_s21_lpf_40m.s2p`
- `2026-01-04_vna_display_40m.png`

## Data Format

### Touchstone Files (.s1p, .s2p)
Standard format from NanoVNA/NanoVNASaver:
- Binary or text format
- Contains frequency + complex S-parameters
- Can be re-imported into VNA software

### CSV Files (optional)
Tabular format for easier processing:
- Columns: Frequency (Hz or MHz), S11 Magnitude (dB), S11 Phase (deg), S21 Magnitude (dB), S21 Phase (deg)
- Use consistent units (document in header or filename)

## Calibration

Always document the calibration profile used:
- SOLT calibration reference plane
- Calibration kit used (if external)
- Frequency range and point count
- Date of calibration

Store calibration info in a companion `.cal_info.txt` file:
```
2026-01-04_att_chain_fullband.cal_info.txt
---
Calibration: SOLT
Calibration plane: End of SMA adapter (before DUT)
Cal kit: NanoVNA-H4 built-in
Frequency range: 1 MHz - 30 MHz
Points: 201
Date: 2026-01-04
Notes: Temperature ~20°C, indoor lab
```

## File Size Management

- VNA Touchstone files are typically small (< 100 KB for 201 points)
- Screenshots can be larger - use PNG compression
- If files exceed a few MB, consider Git LFS or external storage
