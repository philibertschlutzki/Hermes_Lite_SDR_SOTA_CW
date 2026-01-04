# Test Reports

This directory contains structured test reports for TX quality validation and HF measurements.

## Purpose

Provides a consistent, version-controlled structure for:
- TX quality test runs (NanoVNA-H4 measurements)
- VNA S-parameter exports (attenuator characterization, S11/S21 measurements)
- Reproducible test procedures and validation

## Structure

```
test_reports/
├── README.md (this file)
├── schema/
│   └── tx_quality_run_schema.md    # CSV schema definition
├── tx_quality/
│   ├── README.md                    # TX quality test documentation
│   ├── tx_quality_runs.csv          # Actual test run data
│   └── templates/
│       └── tx_quality_run_template.csv  # Template with example data
├── vna_exports/
│   ├── README.md                    # VNA export documentation
│   ├── att_chain/                   # Attenuator characterization
│   ├── dut_s11/                     # DUT return loss measurements
│   ├── filters_s21/                 # Filter insertion loss/rejection
│   └── screenshots/                 # VNA screenshots for documentation
└── tools/
    └── validate_tx_quality_csv.py   # CSV validation script
```

## Related Documentation

- [TX Quality Test Plan (NanoVNA-H4)](../tx_quality_nanovna_h4.md) - Complete test procedure
- [CSV Schema Definition](schema/tx_quality_run_schema.md) - Field definitions and validation rules
- [Validation Tool](tools/validate_tx_quality_csv.py) - Automated CSV validation

## Usage

### Recording a Test Run

1. Follow the procedure in [tx_quality_nanovna_h4.md](../tx_quality_nanovna_h4.md)
2. Fill in a new row in `tx_quality/tx_quality_runs.csv` with your measurements
3. Export VNA data (Touchstone .s1p/.s2p and/or CSV) to `vna_exports/`
4. Run validation: `python tools/validate_tx_quality_csv.py`
5. Commit the results

### VNA Data Format

- **Touchstone files** (.s1p, .s2p): Standard S-parameter format from NanoVNA/NanoVNASaver
- **CSV files**: Optional tabular exports for easier processing
- Use relative paths in CSV (e.g., `docs/test_reports/vna_exports/att_chain/...`)

### CI Integration

The validation tool runs automatically in CI to ensure data quality:
- Checks CSV schema compliance
- Validates data types and ranges
- Prevents broken test reports from being merged

## File Size Considerations

VNA exports can be large. Keep files under 2-5 MB where possible:
- Use appropriate frequency spans
- Compress screenshots
- Consider Git LFS for large datasets (optional)
