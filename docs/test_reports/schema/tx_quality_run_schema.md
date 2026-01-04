# TX Quality Run CSV Schema

**Version**: 1.0  
**Last Updated**: 2026-01-04

## Purpose

Defines the structure and validation rules for `tx_quality_runs.csv`, ensuring consistent and machine-readable test reports.

## Schema Version

The `SCHEMA_VERSION` field tracks breaking changes to the CSV structure:
- **1.0**: Initial schema (current)

When making incompatible changes (removing fields, changing types), increment the major version.

## CSV Format Rules

- **Delimiter**: Comma (`,`)
- **Encoding**: UTF-8
- **Line endings**: Unix (`\n`) or Windows (`\r\n`) - both acceptable
- **Decimal separator**: Period (`.`) for floating-point numbers
- **Date/Time**: ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ` for UTC)
- **Empty fields**: Use empty string for optional text fields, leave numeric fields empty or use `NA` for "not applicable"

## Field Definitions

| # | Column Name | Type | Unit | Required | Description | Example |
|---|-------------|------|------|----------|-------------|---------|
| 1 | SCHEMA_VERSION | string | - | Yes | Schema version (e.g., "1.0") | 1.0 |
| 2 | timestamp_utc | datetime | ISO8601 | Yes | Test date/time in UTC | 2026-01-04T15:30:00Z |
| 3 | operator | string | - | Yes | Operator callsign or name | HB9ABC |
| 4 | location | string | - | No | Test location description | HB9, portable |
| 5 | hl2_serial_or_id | string | - | Yes | HL2 unit identifier | HL2-001234 |
| 6 | hl2_firmware_version | string | - | No | HL2 firmware version | 4.0 |
| 7 | hl2_gateware_version | string | - | No | HL2 FPGA gateware version | 20231215 |
| 8 | tx_mode | enum | - | Yes | TX mode during test | CW_CARRIER |
| 9 | band_m | integer | meters | Yes | Amateur band in meters | 40 |
| 10 | tx_freq_hz | integer | Hz | Yes | TX frequency | 7100000 |
| 11 | tx_power_setting_w | float | W | Yes | Configured TX power | 5.0 |
| 12 | cw_wpm | integer | WPM | No | CW speed (words per minute) | 20 |
| 13 | cw_farnsworth_wpm | integer | WPM | No | Farnsworth spacing WPM (0 = disabled) | 15 |
| 14 | cw_weight_pct | integer | % | No | CW weighting percentage | 50 |
| 15 | ptt_lead_ms | integer | ms | No | PTT lead time | 80 |
| 16 | ptt_tail_ms | integer | ms | No | PTT tail time | 120 |
| 17 | att_chain_id | string | - | Yes | Attenuator chain identifier | ATT_CHAIN_01 |
| 18 | att_total_db_nominal | float | dB | Yes | Nominal total attenuation | 50.0 |
| 19 | att_total_db_measured_at_freq_db | float | dB | No | Measured attenuation at TX freq | 49.5 |
| 20 | nanovna_model | string | - | Yes | NanoVNA model | NanoVNA-H4 |
| 21 | nanovna_firmware | string | - | No | NanoVNA firmware version | v1.2.34 |
| 22 | vna_cal_profile_id | string | - | No | VNA calibration profile ID | SOLT_HF_2026-01-04 |
| 23 | vna_export_s2p_path | string | path | No | Relative path to S2P export | docs/test_reports/vna_exports/att_chain/2026-01-04_40m.s2p |
| 24 | vna_export_s1p_path | string | path | No | Relative path to S1P export | docs/test_reports/vna_exports/dut_s11/2026-01-04_40m.s1p |
| 25 | s11_return_loss_db | float | dB | No | S11 return loss (more negative = better) | -15.2 |
| 26 | s11_vswr | float | ratio | No | VSWR (< 2:1 is acceptable) | 1.4 |
| 27 | filter_id | string | - | No | External filter identifier | LPF_40M_01 |
| 28 | filter_s21_inband_loss_db | float | dB | No | Filter insertion loss in-band | 0.8 |
| 29 | filter_s21_oob_rejection_db | float | dB | No | Filter out-of-band rejection | 42.0 |
| 30 | peak_presence_check | enum | - | Yes | Peak visibility during TX | OBSERVED |
| 31 | peak_offset_hz | float | Hz | No | Peak frequency offset from expected | -5.0 |
| 32 | notes | string | - | No | Free-form notes | Temperature ~20C, slight drift observed |
| 33 | result_pass | boolean | - | Yes | Overall test result | TRUE |

## Field Details

### Enumerations

**tx_mode**:
- `CW_CARRIER`: Continuous carrier (no keying)
- `CW_KEYED`: Keyed CW (with actual message/pattern)
- `TUNE`: Tune mode

**peak_presence_check**:
- `NA`: Not applicable (test not performed)
- `OBSERVED`: Peak clearly visible at expected frequency
- `NOT_OBSERVED`: No peak detected (indicates problem)

### Boolean Fields

**result_pass**:
- `TRUE`: Test passed all criteria
- `FALSE`: Test failed one or more criteria

### Paths

All paths should be **relative to repository root**.

Example: `docs/test_reports/vna_exports/att_chain/2026-01-04_fullband.s2p`

### Validation Rules

1. **SCHEMA_VERSION**: Must match current schema (1.0)
2. **timestamp_utc**: Valid ISO 8601 datetime
3. **band_m**: Must be valid amateur band (160, 80, 60, 40, 30, 20, 17, 15, 12, 10, 6, ...)
4. **tx_freq_hz**: Must be within specified band
5. **tx_power_setting_w**: 0 < power ≤ 10 (HL2 typical max ~5W)
6. **cw_wpm**: 5 ≤ WPM ≤ 60 (if provided)
7. **cw_farnsworth_wpm**: 0 ≤ Farnsworth ≤ WPM (if provided)
8. **cw_weight_pct**: 0 ≤ weight ≤ 100 (50 = nominal)
9. **att_total_db_nominal**: Minimum 40 dB recommended for safety
10. **s11_return_loss_db**: Negative value (e.g., -10 to -40 dB)
11. **s11_vswr**: ≥ 1.0 (ideal = 1.0, acceptable < 2.0)
12. **peak_presence_check**: Must be one of {NA, OBSERVED, NOT_OBSERVED}
13. **result_pass**: Must be TRUE or FALSE

## Usage Example

```csv
SCHEMA_VERSION,timestamp_utc,operator,location,hl2_serial_or_id,hl2_firmware_version,hl2_gateware_version,tx_mode,band_m,tx_freq_hz,tx_power_setting_w,cw_wpm,cw_farnsworth_wpm,cw_weight_pct,ptt_lead_ms,ptt_tail_ms,att_chain_id,att_total_db_nominal,att_total_db_measured_at_freq_db,nanovna_model,nanovna_firmware,vna_cal_profile_id,vna_export_s2p_path,vna_export_s1p_path,s11_return_loss_db,s11_vswr,filter_id,filter_s21_inband_loss_db,filter_s21_oob_rejection_db,peak_presence_check,peak_offset_hz,notes,result_pass
1.0,2026-01-04T15:30:00Z,HB9ABC,HB9 portable,HL2-001234,4.0,20231215,CW_CARRIER,40,7100000,5.0,20,0,50,80,120,ATT_CHAIN_01,50.0,49.5,NanoVNA-H4,v1.2.34,SOLT_HF_2026-01-04,docs/test_reports/vna_exports/att_chain/2026-01-04_40m.s2p,docs/test_reports/vna_exports/dut_s11/2026-01-04_40m.s1p,-15.2,1.4,LPF_40M_01,0.8,42.0,OBSERVED,-5.0,Temperature ~20C,TRUE
```

## Breaking Changes Policy

When making breaking changes to the schema:
1. Increment `SCHEMA_VERSION` major number (e.g., 1.0 → 2.0)
2. Update this document with migration guide
3. Update validation tool to handle both old and new versions
4. Provide conversion script if needed

## Non-Breaking Changes

Non-breaking additions (new optional columns):
1. Add column to end of schema
2. Increment minor version (e.g., 1.0 → 1.1)
3. Update validation tool to accept new field
4. Mark as optional in this document
