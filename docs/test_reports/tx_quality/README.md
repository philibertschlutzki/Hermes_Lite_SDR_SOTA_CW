# TX Quality Test Runs

This directory contains TX quality test run data following the procedure defined in [tx_quality_nanovna_h4.md](../../tx_quality_nanovna_h4.md).

## Files

- `tx_quality_runs.csv` - Actual test run records (append new rows here)
- `templates/tx_quality_run_template.csv` - Template with example data and field descriptions

## Recording a Test Run

1. Perform the test following the [TX Quality Test Plan](../../tx_quality_nanovna_h4.md)
2. Copy the template or add a new row to `tx_quality_runs.csv`
3. Fill in all required fields (see [schema](../schema/tx_quality_run_schema.md))
4. Export and save VNA data to appropriate `vna_exports/` subdirectories
5. Update paths in CSV to reference exported files
6. Validate using `python ../tools/validate_tx_quality_csv.py`
7. Commit changes

## Data Retention

- Keep all test runs in the CSV for historical tracking
- Mark outdated/invalid runs with notes in the `notes` field rather than deleting
- Use `result_pass` field to quickly filter passing runs

## Analysis

The CSV format enables:
- Trend analysis over time
- Comparison across different bands/configurations
- Identification of degradation or improvements
- Correlation with hardware/software changes
