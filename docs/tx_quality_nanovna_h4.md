# TX Quality Test Plan: NanoVNA-H4 + Attenuator

**Version**: 1.0  
**Last Updated**: 2026-01-04  
**Author**: SOTA CW HL2 Project

## Purpose

This document defines a reproducible procedure for validating HL2 TX quality using a NanoVNA-H4 vector network analyzer with an attenuator chain.

**Test Goals**:
1. Verify HL2 transmits on the correct frequency
2. Validate output matching (S11/VSWR) and filter performance
3. Confirm TX chain is properly configured and safe
4. Establish baseline measurements for troubleshooting

## Important Limitations

### NanoVNA-H4 is a VNA, NOT a Spectrum Analyzer

**What NanoVNA-H4 CAN do**:
- Measure impedance matching (S11, VSWR)
- Characterize filters (insertion loss, basic rejection)
- Detect presence of a signal at specific frequencies
- Measure attenuation/transmission (S21)

**What NanoVNA-H4 CANNOT do effectively**:
- **Harmonics/Spurious Analysis**: VNA sweeps discrete points, not continuous spectrum
- **Key Clicks / Transient Analysis**: No time-domain trigger or fast FFT
- **Wideband Spectrum Monitoring**: Limited frequency span and resolution
- **Phase Noise Measurement**: Not designed for this purpose

**Recommendation**: For comprehensive TX quality (harmonics, clicks, bandwidth), use:
- RTL-SDR / SDRplay / HackRF as wideband spectrum analyzer
- Dedicated spectrum analyzer (if available)
- See "Optional Extended Test" section below

## Safety and Equipment Protection

### CRITICAL SAFETY RULES

1. **NEVER connect HL2 TX output directly to NanoVNA**
   - HL2 output: 5W = +37 dBm
   - NanoVNA safe input: typically < +10 dBm
   - **Minimum attenuation**: 40 dB (50-60 dB recommended)

2. **Always use attenuator chain rated for power**
   - First stage must handle full 5W
   - Use at least 10W-rated attenuators

3. **Verify connections before transmitting**
   - Check all connectors are tight
   - Ensure 50Ω termination
   - Verify attenuator chain is in place

4. **Limit TX duty cycle**
   - Use short transmissions (< 10 seconds)
   - Allow cooling between tests
   - Monitor for overheating

### Equipment Damage Risk

Connecting high power to VNA input will **destroy** the VNA frontend. There is NO protection against this.

## Test Equipment

### Required Equipment

1. **Hermes Lite 2 (HL2)**
   - Configured and operational
   - Known good power supply (12-13.8V, 2A minimum)
   - Firmware/gateware version documented

2. **Attenuator Chain** (50Ω, SMA)
   - Minimum 40 dB total (recommend 50 dB)
   - Example: 20 dB + 20 dB + 10 dB (each ≥10W rated)
   - Must be characterized (see Attenuator Characterization section)

3. **NanoVNA-H4**
   - Firmware version documented
   - Calibration kit (SOLT: Short, Open, Load, Thru)
   - USB connection and NanoVNASaver software (optional for data export)

4. **50Ω Dummy Load**
   - Minimum 10W continuous rating
   - Use for initial tests and S11 measurements

5. **Cables and Adapters**
   - High-quality SMA cables (< 30 cm preferred)
   - SMA M-F adapters as needed
   - Optional: DC block (inline capacitor, if DC voltage on RF line)

6. **Optional: External Filters**
   - Band-specific LPF or BPF
   - Document filter ID and specs

### Recommended Accessories

- Torque wrench or calibrated finger-tight technique (5-8 in-lb for SMA)
- Anti-static mat
- Calibration certificate or verification standard
- Thermometer (monitor ambient temperature)

## Attenuator Chain Design

### Power Budget

```
HL2 TX Output: 5W = +37 dBm
Target at VNA input: -10 to 0 dBm (safe zone)
Required attenuation: ~47 dBm = 47 dB

Recommended: 50-60 dB total (provides safety margin)
```

### Example Attenuator Chain

**Configuration ID**: `ATT_CHAIN_01`

```
[HL2 TX] -- [20 dB, 10W] -- [20 dB, 10W] -- [10 dB, 5W] -- [DC Block*] -- [Cable] -- [NanoVNA Port]
           └─ Dissipates 4.95W   └─ 0.495W      └─ 49.5 mW
                               
Total nominal: 50 dB
Power at VNA: +37 dBm - 50 dB = -13 dBm (SAFE)

* DC Block optional - use if HL2 output has DC component
```

### Bill of Materials (Example)

| Item | Spec | Qty | Notes |
|------|------|-----|-------|
| SMA attenuator | 20 dB, 50Ω, 10W | 2 | First stage sees full 5W |
| SMA attenuator | 10 dB, 50Ω, 5W | 1 | Second stage sees ~50 mW |
| DC block | 1-30 MHz, SMA | 1 | Optional, prevents DC damage |
| SMA cable | RG-316, 15 cm | 2 | Low loss, flexible |
| SMA M-F adapter | 50Ω | 2 | As needed for fit |

**CRITICAL**: First attenuator in chain MUST be rated for full HL2 power (10W minimum).

## Pre-Test Setup

### 1. Attenuator Chain Characterization

**Objective**: Measure actual attenuation vs. frequency

**Procedure**:
1. Connect NanoVNA Port 1 -- [Attenuator Chain] -- Port 2
2. Perform SOLT calibration at both ends (before and after chain)
3. Measure S21 (transmission) from 1 MHz to 30 MHz
4. Export Touchstone (.s2p) and/or CSV
5. Save to `docs/test_reports/vna_exports/att_chain/YYYY-MM-DD_fullband.s2p`

**Expected Result**:
- S21 ≈ -50 dB (±2 dB) across HF
- Smooth curve (no resonances or dips)
- Document measured attenuation at each band center frequency

**Example Data**:
| Band | Frequency | S21 (dB) | Nominal | Deviation |
|------|-----------|----------|---------|-----------|
| 40m | 7.1 MHz | -49.5 | -50 | +0.5 |
| 20m | 14.1 MHz | -50.2 | -50 | -0.2 |
| 15m | 21.1 MHz | -50.8 | -50 | -0.8 |

Save this data - it's used for power level correction in actual tests.

### 2. Optional: External Filter Characterization

If using external LPF/BPF:

**S21 (Insertion Loss / Rejection)**:
1. Calibrate VNA at filter connection points
2. Measure S21 from DC to 3× highest operating frequency
3. Document in-band loss and out-of-band rejection
4. Save to `docs/test_reports/vna_exports/filters_s21/YYYY-MM-DD_<filter_id>.s2p`

**S11 (Matching)**:
1. Connect filter + load to Port 1
2. Measure S11 across operating band
3. Verify VSWR < 2:1 in passband

### 3. VNA Calibration for TX Tests

**Reference Plane**: At the point where HL2 TX connects (or after filters, before attenuator chain)

**Calibration Type**: SOLT (Short-Open-Load-Thru)

**Procedure**:
1. Connect calibration standards to measurement point
2. Run VNA cal wizard (SOLT)
3. Verify cal with known reference (e.g., 50Ω load shows S11 < -30 dB)
4. Save calibration profile: `SOLT_HF_YYYY-MM-DD`
5. Do NOT move cables or change setup after calibration

**Frequency Range**: 
- For single-band test: Center ± 500 kHz (fine resolution)
- For multi-band: 1 MHz - 30 MHz (coarse resolution)

**Point Count**:
- Fine scan: 201-401 points
- Coarse scan: 101 points

## Test Procedures

### Test 1: S11 Measurement (Matching / VSWR)

**Objective**: Verify HL2 output impedance and filter matching

**Setup**:
```
[HL2 TX] -- [External Filter*] -- [50Ω Dummy Load]
               ↑
         [NanoVNA Port 1]
         (calibrated at this point)

* Filter optional
```

**Procedure**:
1. Ensure HL2 is OFF or in RX mode (no TX)
2. Connect NanoVNA Port 1 to measurement point (after HL2, before/after filter)
3. Terminate with 50Ω dummy load
4. Set VNA to S11 measurement, frequency span covering band ± 1 MHz
5. Measure S11 and VSWR
6. Export data and screenshot

**Pass Criteria**:
- S11 < -10 dB across operating bandwidth (VSWR < 2:1)
- Preferred: S11 < -14 dB (VSWR < 1.5:1)
- No sharp resonances or anomalies

**Data to Record**:
- `s11_return_loss_db`: Worst-case S11 in band (most negative)
- `s11_vswr`: VSWR at band center
- Export: `docs/test_reports/vna_exports/dut_s11/YYYY-MM-DD_<band>_<config>.s1p`

### Test 2: TX Frequency Verification (Peak Presence Check)

**Objective**: Confirm HL2 transmits on correct frequency

**Setup**:
```
[HL2 TX] -- [Attenuator Chain] -- [NanoVNA Port 1]
                                  Port 2: 50Ω terminated or disconnected
```

**Procedure**:

1. **Connect Attenuator Chain**:
   - HL2 TX → Attenuator chain → NanoVNA Port 1
   - Verify all connections are secure
   - Triple-check attenuator chain is in place!

2. **Configure HL2**:
   - Set frequency (e.g., 7.100 MHz for 40m test)
   - Set mode: CW carrier or TUNE mode
   - Set power: 5W (or less for initial test)
   - Configure PTT/key to enable TX (via API or manual)

3. **Configure VNA**:
   - Frequency span: Center at expected TX freq ± 25 kHz (narrow span)
   - Format: Log Magnitude (dB)
   - Points: Maximum available (401 if supported)
   - Average: OFF or minimal (to see live changes)

4. **Baseline Measurement (RX mode)**:
   - Ensure HL2 is NOT transmitting
   - Take VNA sweep - should show noise floor (typically -60 to -80 dBm)
   - Note baseline level

5. **TX Measurement**:
   - **Start HL2 transmission** (CW carrier or TUNE)
   - Observe VNA display - a clear peak should appear at TX frequency
   - Wait 2-5 seconds for reading to stabilize
   - Place marker at peak and note frequency + level

6. **Record Data**:
   - Peak frequency (compare to expected)
   - Peak level (raw, before correction)
   - Offset from expected frequency
   - Screenshot of VNA display

7. **Stop TX**:
   - Stop HL2 transmission
   - Verify peak disappears (returns to noise floor)

8. **Export Data**:
   - Save sweep: `docs/test_reports/vna_exports/YYYY-MM-DD_tx_<band>_peak.s1p` (if applicable)
   - Save screenshot: `docs/test_reports/vna_exports/screenshots/YYYY-MM-DD_tx_<band>_peak.png`

**Pass Criteria**:
- `peak_presence_check`: OBSERVED (clear peak visible)
- `peak_offset_hz`: < ±50 Hz from expected (±100 Hz acceptable for initial tests)
- Peak level significantly above noise floor (>20 dB difference)

**Power Estimation (Optional)**:
```
P_out_HL2 = P_measured_VNA + A_total

Where:
  P_measured_VNA = VNA reading at peak (dBm)
  A_total = Attenuator chain loss at frequency (dB, from characterization)

Example:
  VNA reads -12 dBm at 7.1 MHz
  Att chain S21 = -49.5 dB at 7.1 MHz
  Estimated P_out = -12 + 49.5 = +37.5 dBm ≈ 5.6W

Note: This is APPROXIMATE - VNA is not calibrated as power meter!
```

**Troubleshooting**:
- **No peak visible**:
  - Verify TX is actually active (check PTT status)
  - Check attenuator connections
  - Verify VNA frequency span includes TX freq
  - Try wider span or higher averaging
- **Peak at wrong frequency**:
  - Check HL2 frequency setting
  - Verify VNA calibration
  - Check for LO leakage or mixer products
- **Very weak or very strong peak**:
  - Verify attenuator chain integrity
  - Check for missing/double attenuators
  - Verify HL2 power setting

### Test 3: Filter Performance (If External Filter Used)

**Objective**: Validate external LPF/BPF performance in TX chain

**Setup**:
```
[HL2 TX] -- [External Filter] -- [NanoVNA Port 1 & 2] -- [Load]
                                 (Thru measurement)
```

**Procedure**:
1. Connect filter between VNA Port 1 and Port 2
2. Calibrate SOLT with filter connection points as reference
3. Measure S21 from DC to 60 MHz (or higher)
4. Document in-band loss and out-of-band rejection

**Pass Criteria**:
- In-band insertion loss: < 1.5 dB (< 0.8 dB preferred)
- 2nd harmonic rejection: > 30 dB
- 3rd harmonic rejection: > 40 dB

**Data to Record**:
- `filter_id`: Filter identifier
- `filter_s21_inband_loss_db`: Worst case in-band loss
- `filter_s21_oob_rejection_db`: Best case out-of-band rejection (e.g., at 2nd harmonic)

## Data Recording

### CSV Entry

After completing all tests for a given configuration, add a row to:
`docs/test_reports/tx_quality/tx_quality_runs.csv`

See [schema documentation](test_reports/schema/tx_quality_run_schema.md) for field definitions.

**Example Entry**:
```csv
1.0,2026-01-04T15:30:00Z,HB9ABC,Lab bench,HL2-001234,4.0,20231215,CW_CARRIER,40,7100000,5.0,20,0,50,80,120,ATT_CHAIN_01,50.0,49.5,NanoVNA-H4,v1.2.34,SOLT_HF_2026-01-04,docs/test_reports/vna_exports/att_chain/2026-01-04_fullband.s2p,docs/test_reports/vna_exports/dut_s11/2026-01-04_40m.s1p,-15.2,1.4,LPF_40M_01,0.8,42.0,OBSERVED,-5.0,All tests passed,TRUE
```

### File Organization

**VNA Exports**: `docs/test_reports/vna_exports/`
- Attenuator characterization: `att_chain/`
- S11 measurements: `dut_s11/`
- Filter S21: `filters_s21/`
- Screenshots: `screenshots/`

**Naming Convention**: `YYYY-MM-DD_<type>_<band>_<config>.<ext>`

Examples:
- `2026-01-04_att_chain_fullband.s2p`
- `2026-01-04_s11_hl2_40m_lpf.s1p`
- `2026-01-04_s21_lpf_40m.s2p`
- `2026-01-04_tx_40m_peak_screenshot.png`

## Validation

Before committing test results:

```bash
cd /path/to/repo
python docs/test_reports/tools/validate_tx_quality_csv.py
```

This validates:
- CSV schema compliance
- Data types and ranges
- Required fields
- File references (paths exist)

## Optional Extended Test: Spectrum Analysis

**Motivation**: NanoVNA-H4 cannot effectively measure harmonics, key clicks, or wideband spurious emissions.

**Alternative Tools**:
1. **RTL-SDR / SDRplay / HackRF**: Wideband SDR as spectrum analyzer
2. **Dedicated Spectrum Analyzer**: If available
3. **Another SDR in RX mode**: Use waterfall display

### RTL-SDR Spectrum Analysis Procedure

**Equipment**:
- RTL-SDR dongle (V3 or similar)
- Attenuator: 20-30 dB (less than VNA, as RTL-SDR has higher max input)
- Software: SDR++, GQRX, or CubicSDR

**Procedure**:

1. **Setup**:
   ```
   [HL2 TX] -- [20-30 dB Attenuator] -- [RTL-SDR]
   ```

2. **Harmonics Check**:
   - Set RTL-SDR to view 0-60 MHz (or DC-1700 MHz if supported)
   - Start HL2 TX on fundamental (e.g., 7.1 MHz)
   - Observe waterfall:
     - Fundamental at 7.1 MHz (should be strongest)
     - 2nd harmonic at 14.2 MHz (should be -30 to -50 dBc)
     - 3rd harmonic at 21.3 MHz (should be -40 to -60 dBc)
   - Screenshot and record levels

3. **Key Clicks / Bandwidth**:
   - Transmit CW message (keyed, not carrier)
   - Observe bandwidth on waterfall
   - Measure occupied bandwidth (e.g., -40 dB points)
   - Check for excessive splatter or clicks

4. **Pass Criteria**:
   - Harmonics: 2nd harmonic < -30 dBc, 3rd harmonic < -40 dBc
   - Bandwidth: < 500 Hz for clean CW
   - No spurious emissions outside band

**Limitations**:
- RTL-SDR has limited dynamic range (~50 dB)
- Absolute power measurements require calibration
- Use as qualitative check, not absolute measurement

### Reporting Extended Tests

Add notes to `notes` field in CSV:
```
Extended test with RTL-SDR: 2nd harmonic -42 dBc, BW ~300 Hz @ -40dB, clean keying observed
```

Optionally save screenshots to `docs/test_reports/vna_exports/screenshots/` with `_rtlsdr_` in filename.

## Frequency Plan: Bands to Test

Recommended test coverage for HF SOTA operation:

| Band | Frequency | Priority | Notes |
|------|-----------|----------|-------|
| 40m | 7.100 MHz | High | Primary SOTA CW band |
| 20m | 14.060 MHz | High | Primary DX band |
| 30m | 10.130 MHz | Medium | CW-only, narrow band |
| 15m | 21.060 MHz | Medium | Good for portable |
| 17m | 18.096 MHz | Low | Less common |
| 12m | 24.906 MHz | Low | Less common |

Test at least 40m and 20m for basic validation. Full band coverage for comprehensive testing.

## Troubleshooting Guide

### Problem: No peak visible during TX

**Possible Causes**:
1. TX not actually active
   - Check PTT status via API
   - Verify ioboard KEY signal
   - Check HL2 LED indicators
2. Wrong frequency span on VNA
   - Use wider span (±100 kHz)
   - Verify HL2 frequency setting matches VNA
3. Attenuator failure or missing
   - Verify chain integrity
   - Re-measure attenuator S21
4. Cable/connection issue
   - Check all SMA connections
   - Verify no broken cables

### Problem: Peak at wrong frequency

**Possible Causes**:
1. HL2 misconfigured
   - Verify frequency setting in software
   - Check reference oscillator calibration
2. VNA calibration error
   - Re-calibrate VNA
   - Verify reference frequency
3. Measurement artifact
   - Could be LO leakage or mixer product
   - Try different frequency

### Problem: Poor S11 (high VSWR)

**Possible Causes**:
1. Filter mismatch
   - Measure filter S11 independently
   - Try different filter or bypass
2. Load not 50Ω
   - Verify dummy load with VNA
   - Try known-good load
3. Cable/connector issue
   - Check for damaged connectors
   - Try different cable

### Problem: Attenuator gets hot

**Possible Causes**:
1. Insufficient power rating
   - First stage must handle full 5W
   - Use 10W-rated attenuators
2. Excessive TX duty cycle
   - Limit transmissions to < 10 seconds
   - Allow cooling between tests
3. Attenuator failure
   - Replace suspect attenuator
   - Verify rating matches application

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-04 | Initial release |

## References

- NanoVNA-H4 User Manual
- [NanoVNASaver Software](https://github.com/NanoVNA-Saver/nanovna-saver)
- [Touchstone File Format Specification](https://en.wikipedia.org/wiki/Touchstone_file)
- [HL2 Protocol Documentation](https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol)
- Repository: [TX Quality Test Reports](test_reports/)
