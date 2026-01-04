#!/usr/bin/env python3
"""
TX Quality CSV Validation Tool

Validates tx_quality_runs.csv against the schema defined in
docs/test_reports/schema/tx_quality_run_schema.md

Usage:
    python validate_tx_quality_csv.py [path/to/tx_quality_runs.csv]

Exit codes:
    0: Validation passed
    1: Validation failed
    2: File not found or invalid
"""

import csv
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Schema version this validator supports
SUPPORTED_SCHEMA_VERSION = "1.0"

# Field definitions (name, type, required, validator_func)
FIELD_SCHEMA = [
    ("SCHEMA_VERSION", str, True, lambda v: v == SUPPORTED_SCHEMA_VERSION),
    ("timestamp_utc", str, True, lambda v: validate_iso8601(v)),
    ("operator", str, True, lambda v: len(v) > 0),
    ("location", str, False, None),
    ("hl2_serial_or_id", str, True, lambda v: len(v) > 0),
    ("hl2_firmware_version", str, False, None),
    ("hl2_gateware_version", str, False, None),
    ("tx_mode", str, True, lambda v: v in ["CW_CARRIER", "CW_KEYED", "TUNE"]),
    ("band_m", int, True, lambda v: v in [160, 80, 60, 40, 30, 20, 17, 15, 12, 10, 6, 4, 2]),
    ("tx_freq_hz", int, True, lambda v: 1_000_000 <= v <= 30_000_000),
    ("tx_power_setting_w", float, True, lambda v: 0 < v <= 10),
    ("cw_wpm", int, False, lambda v: v is None or (5 <= v <= 60)),
    ("cw_farnsworth_wpm", int, False, lambda v: v is None or (0 <= v <= 60)),
    ("cw_weight_pct", int, False, lambda v: v is None or (0 <= v <= 100)),
    ("ptt_lead_ms", int, False, None),
    ("ptt_tail_ms", int, False, None),
    ("att_chain_id", str, True, lambda v: len(v) > 0),
    ("att_total_db_nominal", float, True, lambda v: v >= 40.0),
    ("att_total_db_measured_at_freq_db", float, False, lambda v: v is None or v >= 30.0),
    ("nanovna_model", str, True, lambda v: len(v) > 0),
    ("nanovna_firmware", str, False, None),
    ("vna_cal_profile_id", str, False, None),
    ("vna_export_s2p_path", str, False, None),
    ("vna_export_s1p_path", str, False, None),
    ("s11_return_loss_db", float, False, lambda v: v is None or v < 0),
    ("s11_vswr", float, False, lambda v: v is None or v >= 1.0),
    ("filter_id", str, False, None),
    ("filter_s21_inband_loss_db", float, False, lambda v: v is None or v >= 0),
    ("filter_s21_oob_rejection_db", float, False, lambda v: v is None or v >= 0),
    ("peak_presence_check", str, True, lambda v: v in ["NA", "OBSERVED", "NOT_OBSERVED"]),
    ("peak_offset_hz", float, False, None),
    ("notes", str, False, None),
    ("result_pass", bool, True, lambda v: v in [True, False]),
]

EXPECTED_HEADER = [field[0] for field in FIELD_SCHEMA]


def validate_iso8601(value: str) -> bool:
    """Validate ISO 8601 datetime format."""
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False


def parse_value(value: str, field_type: type) -> Any:
    """Parse and convert field value to expected type."""
    value = value.strip()
    
    if not value or value.upper() == "NA":
        return None
    
    try:
        if field_type == bool:
            if value.upper() in ["TRUE", "1", "YES"]:
                return True
            elif value.upper() in ["FALSE", "0", "NO"]:
                return False
            else:
                raise ValueError(f"Invalid boolean value: {value}")
        elif field_type == int:
            return int(value)
        elif field_type == float:
            return float(value)
        else:  # str
            return value
    except (ValueError, TypeError) as e:
        raise ValueError(f"Cannot convert '{value}' to {field_type.__name__}: {e}")


def validate_row(row: Dict[str, str], row_num: int, csv_dir: Path) -> List[str]:
    """Validate a single row. Returns list of error messages."""
    errors = []
    
    for field_name, field_type, required, validator in FIELD_SCHEMA:
        value_str = row.get(field_name, "").strip()
        
        # Check required fields
        if required and not value_str:
            errors.append(f"Row {row_num}: Required field '{field_name}' is empty")
            continue
        
        # Skip optional empty fields
        if not required and not value_str:
            continue
        
        # Parse value
        try:
            value = parse_value(value_str, field_type)
        except ValueError as e:
            errors.append(f"Row {row_num}: Field '{field_name}' - {e}")
            continue
        
        # Run custom validator
        if validator and value is not None:
            try:
                if not validator(value):
                    errors.append(
                        f"Row {row_num}: Field '{field_name}' failed validation. "
                        f"Value: {value}"
                    )
            except Exception as e:
                errors.append(
                    f"Row {row_num}: Field '{field_name}' validator error: {e}"
                )
    
    # Additional cross-field validations
    if row.get("cw_farnsworth_wpm") and row.get("cw_wpm"):
        try:
            farn = int(row["cw_farnsworth_wpm"])
            wpm = int(row["cw_wpm"])
            if farn > 0 and farn > wpm:
                errors.append(
                    f"Row {row_num}: cw_farnsworth_wpm ({farn}) cannot exceed "
                    f"cw_wpm ({wpm})"
                )
        except ValueError:
            pass  # Already caught by type validation
    
    # Validate file paths exist (relative to repo root or CSV dir)
    for path_field in ["vna_export_s2p_path", "vna_export_s1p_path"]:
        path_str = row.get(path_field, "").strip()
        if path_str:
            # Try relative to CSV directory first, then repo root
            path_abs = csv_dir / path_str
            if not path_abs.exists():
                # Try from repo root (go up 2 levels from test_reports/tx_quality)
                repo_root = csv_dir.parent.parent.parent
                path_abs = repo_root / path_str
                if not path_abs.exists():
                    errors.append(
                        f"Row {row_num}: File not found: {path_field} = '{path_str}' "
                        f"(checked relative to CSV and repo root)"
                    )
    
    return errors


def validate_csv(csv_path: Path) -> Tuple[bool, List[str]]:
    """Validate the CSV file. Returns (success, errors)."""
    errors = []
    
    if not csv_path.exists():
        errors.append(f"CSV file not found: {csv_path}")
        return False, errors
    
    csv_dir = csv_path.parent
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate header
            if reader.fieldnames != EXPECTED_HEADER:
                errors.append("CSV header does not match expected schema")
                errors.append(f"Expected: {EXPECTED_HEADER}")
                errors.append(f"Got: {reader.fieldnames}")
                return False, errors
            
            # Validate each row
            row_count = 0
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                row_errors = validate_row(row, row_num, csv_dir)
                errors.extend(row_errors)
                row_count += 1
            
            if row_count == 0:
                print(f"Warning: CSV file is empty (no data rows)")
    
    except Exception as e:
        errors.append(f"Error reading CSV: {e}")
        return False, errors
    
    success = len(errors) == 0
    return success, errors


def main():
    """Main entry point."""
    # Determine CSV path
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        # Default: assume running from tools/ directory
        script_dir = Path(__file__).parent
        csv_path = script_dir.parent / "tx_quality" / "tx_quality_runs.csv"
    
    print(f"Validating: {csv_path}")
    print(f"Schema version: {SUPPORTED_SCHEMA_VERSION}")
    print("-" * 60)
    
    success, errors = validate_csv(csv_path)
    
    if success:
        print("✓ Validation PASSED")
        print(f"  CSV file is valid according to schema v{SUPPORTED_SCHEMA_VERSION}")
        return 0
    else:
        print("✗ Validation FAILED")
        print(f"\nFound {len(errors)} error(s):\n")
        for error in errors:
            print(f"  - {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
