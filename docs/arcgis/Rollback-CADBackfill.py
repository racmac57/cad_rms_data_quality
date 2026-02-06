#!/usr/bin/env python3
"""
Rollback CAD Backfill Script - Emergency Truncate

Purpose:
    Emergency truncate of ArcGIS Online/Enterprise feature layer to reset
    state for clean restart. Requires "WIPE" confirmation to prevent
    accidental data loss.

WARNING: This operation is DESTRUCTIVE and IRREVERSIBLE.
         All records in the feature layer will be deleted.

Features:
    - Truncates ArcGIS feature layer
    - Requires "WIPE" confirmation (prevents accidental execution)
    - Resets state for clean backfill restart
    - Creates backup report before truncation
    - Uses arcpy.management.TruncateTable()

Dependencies:
    - arcpy (ArcGIS Pro Python environment)

Usage:
    propy.bat "C:\HPD ESRI\04_Scripts\Rollback-CADBackfill.py"

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

# Geodatabase path (fallback if config missing)
GEODATABASE_PATH = r"C:\HPD ESRI\03_Data\CAD\CAD_Data.gdb"
FEATURE_CLASS_NAME = "CFSTable"  # Verify this name

# Reports directory
REPORTS_DIR = Path(r"C:\HPD ESRI\05_Reports")


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


def create_backup_report(feature_layer: str) -> Path:
    """
    Create backup report documenting state before truncation.

    Returns:
        Path: Report file path
    """
    print(f"\n[1/3] Creating backup report")

    if not arcpy.Exists(feature_layer):
        raise FileNotFoundError(f"Feature layer not found: {feature_layer}")

    # Get record count
    result = arcpy.management.GetCount(feature_layer)
    record_count = int(result.getOutput(0))

    # Get date range
    min_date = None
    max_date = None

    try:
        with arcpy.da.SearchCursor(
            feature_layer,
            ["TimeOfCall"],
            sql_clause=(None, "ORDER BY TimeOfCall ASC")
        ) as cursor:
            for row in cursor:
                min_date = row[0]
                break

        with arcpy.da.SearchCursor(
            feature_layer,
            ["TimeOfCall"],
            sql_clause=(None, "ORDER BY TimeOfCall DESC")
        ) as cursor:
            for row in cursor:
                max_date = row[0]
                break
    except Exception as e:
        print(f"      [WARNING] Could not extract date range: {e}")

    # Build backup report
    report_lines = [
        "=" * 70,
        "CAD BACKFILL ROLLBACK BACKUP REPORT",
        "=" * 70,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Feature Layer: {feature_layer}",
        "",
        "STATE BEFORE TRUNCATION:",
        f"  Record count: {record_count:,}",
        f"  Date range: {min_date} to {max_date}" if min_date and max_date else "  Date range: Unknown",
        "",
        "ACTION: TRUNCATE TABLE",
        "  This operation will delete ALL records from the feature layer.",
        "  This backup report is the ONLY record of the previous state.",
        "",
        "=" * 70,
    ]

    # Write report
    report_path = REPORTS_DIR / f"rollback_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report_text = "\n".join(report_lines)
    report_path.write_text(report_text)

    print(f"      Backup report created: {report_path.name}")
    print(f"      Current record count: {record_count:,}")

    return report_path


def confirm_truncation() -> bool:
    """
    Require "WIPE" confirmation to prevent accidental execution.

    Returns:
        bool: True if confirmed, False otherwise
    """
    print(f"\n[2/3] Confirmation required")
    print("")
    print("  +" + ("-" * 68) + "+")
    print("  | " + " " * 66 + " |")
    print("  |" + "WARNING: DESTRUCTIVE OPERATION".center(68) + "|")
    print("  | " + " " * 66 + " |")
    print("  +" + ("-" * 68) + "+")
    print("")
    print("  This operation will PERMANENTLY DELETE all records from the feature layer.")
    print("  This action is IRREVERSIBLE and will require a full backfill restart.")
    print("")
    print("  Type WIPE (all caps) to confirm truncation:")
    print("")

    try:
        response = input("  > ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n")
        print("  [ABORT] Rollback cancelled by user")
        return False

    if response == "WIPE":
        print("")
        print("  [CONFIRMED] Proceeding with truncation...")
        return True
    else:
        print("")
        print(f"  [ABORT] Incorrect confirmation (got: '{response}', expected: 'WIPE')")
        return False


def truncate_feature_layer(feature_layer: str) -> bool:
    """
    Truncate (delete all records) from feature layer.

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n[3/3] Truncating feature layer")
    print(f"      Layer: {feature_layer}")

    if not arcpy.Exists(feature_layer):
        print(f"      [ERROR] Feature layer not found: {feature_layer}")
        return False

    try:
        # Get count before truncation
        result = arcpy.management.GetCount(feature_layer)
        count_before = int(result.getOutput(0))

        print(f"      Records before: {count_before:,}")

        # Truncate table
        arcpy.management.TruncateTable(feature_layer)

        # Verify truncation
        result = arcpy.management.GetCount(feature_layer)
        count_after = int(result.getOutput(0))

        print(f"      Records after: {count_after:,}")

        if count_after == 0:
            print(f"      [SUCCESS] Truncation complete - {count_before:,} records deleted")
            return True
        else:
            print(f"      [WARNING] Truncation incomplete - {count_after:,} records remaining")
            return False

    except arcpy.ExecuteError as e:
        print(f"      [ERROR] ArcPy truncation failed: {e}")
        print(arcpy.GetMessages())
        return False
    except Exception as e:
        print(f"      [ERROR] Unexpected error during truncation: {e}")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("=" * 70)
    print("CAD BACKFILL ROLLBACK SCRIPT - EMERGENCY TRUNCATE")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    try:
        # Load configuration
        config = load_config(CONFIG_PATH)

        # Get feature layer path
        feature_layer = get_feature_layer_path(config)

        print(f"\nFeature layer: {feature_layer}")

        # Step 1: Create backup report
        backup_report_path = create_backup_report(feature_layer)

        # Step 2: Confirm truncation (requires "WIPE")
        if not confirm_truncation():
            print("")
            print("=" * 70)
            print("ROLLBACK CANCELLED")
            print("=" * 70)
            print("No changes made to feature layer.")
            print("=" * 70)
            return 1

        # Step 3: Truncate feature layer
        success = truncate_feature_layer(feature_layer)

        # Summary
        print("")
        print("=" * 70)
        if success:
            print("ROLLBACK COMPLETE")
            print("=" * 70)
            print("Feature layer truncated successfully.")
            print(f"Backup report: {backup_report_path}")
            print("")
            print("NEXT STEPS:")
            print("  1. Delete is_first_batch.txt marker from staging directory")
            print("  2. Clear Completed/ folder in batch directory")
            print("  3. Run Invoke-CADBackfillPublish.ps1 -Staged to restart backfill")
            print("=" * 70)
            return 0
        else:
            print("ROLLBACK FAILED")
            print("=" * 70)
            print("Truncation did not complete successfully.")
            print("Review error messages above.")
            print("=" * 70)
            return 1

    except Exception as e:
        print("")
        print("=" * 70)
        print("ROLLBACK FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
