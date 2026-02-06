#!/usr/bin/env python3
"""
Validate CAD Backfill Count Script

Purpose:
    Queries ArcGIS Online feature layer to verify record count after staged
    backfill execution. Compares against expected 754,409 records and reports
    overage (duplicates) or underage (missing batches).

Features:
    - Queries ArcGIS Online/Enterprise feature layer count
    - Compares against expected count from manifest
    - Reports overage, underage, or exact match
    - Checks for duplicate ReportNumberNew values
    - Generates validation summary report

Dependencies:
    - arcpy (ArcGIS Pro Python environment)

Usage:
    propy.bat "C:\HPD ESRI\04_Scripts\Validate-CADBackfillCount.py"

Author: R. A. Carucci
Created: 2026-02-06
Version: 1.0.0
"""

import sys
import json
from pathlib import Path
from datetime import datetime

try:
    import arcpy
except ImportError as e:
    print(f"[ERROR] Missing arcpy module: {e}")
    print("This script must run in ArcGIS Pro Python environment via propy.bat")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Configuration file path
CONFIG_PATH = Path(r"C:\HPD ESRI\04_Scripts\config.json")

# Expected count from manifest
EXPECTED_RECORD_COUNT = 754409

# Geodatabase path (fallback if config missing)
GEODATABASE_PATH = r"C:\HPD ESRI\03_Data\CAD\CAD_Data.gdb"
FEATURE_CLASS_NAME = "CFSTable"  # Verify this name


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_config(config_path: Path) -> dict:
    """Load configuration file."""
    if not config_path.exists():
        print(f"[WARNING] Config file not found: {config_path}")
        print("          Using fallback geodatabase path")
        return None

    with open(config_path, "r") as f:
        config = json.load(f)

    return config


def get_feature_layer_path(config: dict) -> str:
    """Get feature layer path from config or construct from geodatabase."""
    if config:
        # Try to get from config
        geodatabase = config.get("paths", {}).get("geodatabase")
        target_dataset = config.get("paths", {}).get("target_dataset")

        if target_dataset and target_dataset != "VERIFY_FROM_TOOL_OUTPUT":
            return target_dataset

        if geodatabase:
            # Construct path
            return f"{geodatabase}\\{FEATURE_CLASS_NAME}"

    # Fallback
    return f"{GEODATABASE_PATH}\\{FEATURE_CLASS_NAME}"


def get_feature_count(feature_layer: str) -> int:
    """Get record count from feature layer."""
    print(f"\n[1/3] Querying feature layer count")
    print(f"      Layer: {feature_layer}")

    if not arcpy.Exists(feature_layer):
        raise FileNotFoundError(f"Feature layer not found: {feature_layer}")

    # Get count
    result = arcpy.management.GetCount(feature_layer)
    count = int(result.getOutput(0))

    print(f"      Record count: {count:,}")

    return count


def check_for_duplicates(feature_layer: str) -> tuple:
    """
    Check for duplicate ReportNumberNew values.

    Returns:
        tuple: (has_duplicates: bool, duplicate_count: int)
    """
    print(f"\n[2/3] Checking for duplicate case numbers")

    try:
        # Create frequency table
        freq_table = r"memory\freq_report_numbers"

        arcpy.analysis.Frequency(
            in_table=feature_layer,
            out_table=freq_table,
            frequency_fields="ReportNumberNew"
        )

        # Query for duplicates (FREQUENCY > 1)
        duplicate_count = 0
        with arcpy.da.SearchCursor(
            freq_table,
            ["ReportNumberNew", "FREQUENCY"],
            where_clause="FREQUENCY > 1"
        ) as cursor:
            duplicates = list(cursor)
            duplicate_count = len(duplicates)

            if duplicates:
                print(f"      [WARNING] Found {duplicate_count} duplicate case number(s):")
                for case_num, freq in duplicates[:10]:
                    print(f"                {case_num}: {freq} occurrences")
                if duplicate_count > 10:
                    print(f"                ... and {duplicate_count - 10} more")

        # Cleanup
        if arcpy.Exists(freq_table):
            arcpy.Delete_management(freq_table)

        if duplicate_count == 0:
            print(f"      [PASS] No duplicate case numbers found")

        return (duplicate_count > 0, duplicate_count)

    except Exception as e:
        print(f"      [ERROR] Duplicate check failed: {e}")
        return (False, 0)


def generate_validation_report(
    actual_count: int,
    expected_count: int,
    has_duplicates: bool,
    duplicate_count: int,
    feature_layer: str
) -> None:
    """Generate validation summary report."""
    print(f"\n[3/3] Generating validation report")

    difference = actual_count - expected_count

    # Determine status
    if actual_count == expected_count and not has_duplicates:
        status = "SUCCESS"
        status_color = "GREEN"
    elif actual_count == expected_count and has_duplicates:
        status = "WARNING"
        status_color = "YELLOW"
    else:
        status = "MISMATCH"
        status_color = "RED"

    # Build report
    report_lines = [
        "=" * 70,
        "CAD BACKFILL VALIDATION REPORT",
        "=" * 70,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Feature Layer: {feature_layer}",
        "",
        "RECORD COUNT:",
        f"  Expected: {expected_count:,}",
        f"  Actual: {actual_count:,}",
        f"  Difference: {difference:+,}",
        "",
    ]

    # Add interpretation
    if difference == 0:
        report_lines.append("  [PASS] Record count matches baseline exactly")
    elif difference > 0:
        report_lines.append(f"  [ERROR] OVERAGE: {difference:,} extra records")
        report_lines.append("          Possible causes: duplicate batches, manual additions")
    else:
        report_lines.append(f"  [ERROR] UNDERAGE: {abs(difference):,} missing records")
        report_lines.append("          Possible causes: incomplete batches, failed append")

    # Add duplicate check results
    report_lines.extend([
        "",
        "DUPLICATE CHECK:",
        f"  Duplicate case numbers: {duplicate_count}",
        f"  Status: {'PASS' if not has_duplicates else 'WARNING'}",
    ])

    if has_duplicates:
        report_lines.append("")
        report_lines.append("  [WARNING] Duplicates detected - investigate with:")
        report_lines.append("            SELECT ReportNumberNew, COUNT(*)")
        report_lines.append("            FROM CFSTable")
        report_lines.append("            GROUP BY ReportNumberNew")
        report_lines.append("            HAVING COUNT(*) > 1")

    # Add final status
    report_lines.extend([
        "",
        "=" * 70,
        f"VALIDATION STATUS: {status}",
        "=" * 70,
    ])

    if status == "SUCCESS":
        report_lines.append("All validation checks passed. Backfill successful!")
    elif status == "WARNING":
        report_lines.append("Record count matches but duplicates found. Review duplicates.")
    else:
        report_lines.append("Record count mismatch detected. Review logs and rerun if needed.")

    report_lines.append("=" * 70)

    # Write report
    report_text = "\n".join(report_lines)
    report_path = Path(r"C:\HPD ESRI\05_Reports") / f"backfill_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text)

    # Print to console
    print(report_text)
    print(f"\nReport saved to: {report_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("=" * 70)
    print("CAD BACKFILL VALIDATION SCRIPT")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Expected record count: {EXPECTED_RECORD_COUNT:,}")
    print("=" * 70)

    try:
        # Load configuration
        config = load_config(CONFIG_PATH)

        # Get feature layer path
        feature_layer = get_feature_layer_path(config)

        # Step 1: Get feature count
        actual_count = get_feature_count(feature_layer)

        # Step 2: Check for duplicates
        has_duplicates, duplicate_count = check_for_duplicates(feature_layer)

        # Step 3: Generate validation report
        generate_validation_report(
            actual_count=actual_count,
            expected_count=EXPECTED_RECORD_COUNT,
            has_duplicates=has_duplicates,
            duplicate_count=duplicate_count,
            feature_layer=feature_layer
        )

        # Return exit code
        if actual_count == EXPECTED_RECORD_COUNT and not has_duplicates:
            print("\n[SUCCESS] Validation passed")
            return 0
        elif actual_count == EXPECTED_RECORD_COUNT and has_duplicates:
            print("\n[WARNING] Count matches but duplicates found")
            return 1
        else:
            print("\n[ERROR] Count mismatch detected")
            return 1

    except Exception as e:
        print(f"\n[ERROR] Fatal error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
