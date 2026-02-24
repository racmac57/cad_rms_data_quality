#!/usr/bin/env python3
"""
Import CAD Polished Excel to ArcGIS Geodatabase
================================================================
Purpose: Import the consolidated CAD dataset (2019-2026) from Excel
         into an ArcGIS geodatabase table using arcpy.ExcelToTable

Author: R. A. Carucci
Date: 2026-02-01
Version: 1.0.0

IMPORTANT: This script must be run on the ArcGIS Pro server (HPD2022LAWSOFT)
           where arcpy is available. It will NOT work on a local machine
           without ArcGIS Pro installed.

Run Location: HPD2022LAWSOFT (10.0.0.157) via Remote Desktop
================================================================
"""

import arcpy
import os
import sys
import json
from datetime import datetime
from pathlib import Path


# ================================================================
# CONFIGURATION
# ================================================================

# Server paths (update if paths change on server)
CONFIG = {
    # Source Excel file (copied from network share)
    "excel_source_share": r"\\10.0.0.157\esri\CAD_Consolidated_2019_2026.xlsx",
    "excel_source_local": r"C:\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx",

    # Target geodatabase
    "geodatabase": r"C:\HPD ESRI\03_Data\CAD\CAD_Data.gdb",

    # Output table name
    "table_name": "CAD_Consolidated_2019_2026",

    # Sheet name in Excel (usually Sheet1 or first sheet)
    "sheet_name": "Sheet1$",

    # Expected record count for validation (from manifest)
    "expected_records": 724794,

    # Backup settings
    "backup_existing": True,
    "backup_suffix": "_backup",
}


# ================================================================
# FUNCTIONS
# ================================================================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def check_arcpy():
    """Verify arcpy is available."""
    try:
        log("Checking arcpy availability...")
        log(f"  ArcGIS version: {arcpy.GetInstallInfo()['Version']}")
        log(f"  Product: {arcpy.GetInstallInfo()['ProductName']}")
        return True
    except Exception as e:
        log(f"ERROR: arcpy not available: {e}", "ERROR")
        log("This script must be run on a machine with ArcGIS Pro installed", "ERROR")
        return False


def check_license():
    """Check ArcGIS license availability."""
    log("Checking ArcGIS license...")
    try:
        # Check out any necessary extension licenses
        arcpy.CheckOutExtension("Foundation")
        log("  License checkout: OK")
        return True
    except Exception as e:
        log(f"  License warning: {e}", "WARN")
        log("  Proceeding anyway - basic conversion doesn't require extensions", "WARN")
        return True


def verify_source_file(config: dict) -> str:
    """
    Find and verify the source Excel file exists.
    Tries network share first, then local path.

    Returns:
        Path to the source file
    """
    log("Verifying source Excel file...")

    # Try network share first
    if os.path.exists(config["excel_source_share"]):
        source_path = config["excel_source_share"]
        log(f"  Found on network share: {source_path}")
    elif os.path.exists(config["excel_source_local"]):
        source_path = config["excel_source_local"]
        log(f"  Found locally: {source_path}")
    else:
        log(f"ERROR: Source file not found at either location:", "ERROR")
        log(f"  Network: {config['excel_source_share']}", "ERROR")
        log(f"  Local:   {config['excel_source_local']}", "ERROR")
        raise FileNotFoundError("Source Excel file not found")

    # Get file info
    file_size_mb = os.path.getsize(source_path) / (1024 * 1024)
    log(f"  File size: {file_size_mb:.2f} MB")

    return source_path


def verify_geodatabase(config: dict):
    """Verify the target geodatabase exists."""
    log("Verifying target geodatabase...")

    gdb_path = config["geodatabase"]

    if arcpy.Exists(gdb_path):
        log(f"  OK: {gdb_path}")
    else:
        log(f"  Geodatabase not found, creating: {gdb_path}", "WARN")
        gdb_dir = os.path.dirname(gdb_path)
        gdb_name = os.path.basename(gdb_path)
        arcpy.management.CreateFileGDB(gdb_dir, gdb_name.replace(".gdb", ""))
        log(f"  Created geodatabase: {gdb_path}")


def backup_existing_table(config: dict):
    """Backup existing table if it exists."""
    table_path = os.path.join(config["geodatabase"], config["table_name"])

    if arcpy.Exists(table_path):
        if config["backup_existing"]:
            backup_name = f"{config['table_name']}{config['backup_suffix']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(config["geodatabase"], backup_name)

            log(f"Backing up existing table to: {backup_name}")
            arcpy.management.Copy(table_path, backup_path)
            log("  Backup complete")

        log(f"Deleting existing table: {config['table_name']}")
        arcpy.management.Delete(table_path)
        log("  Deleted")


def import_excel_to_geodatabase(source_path: str, config: dict):
    """
    Import Excel file to geodatabase using ExcelToTable.

    This is the core import function.
    """
    log("=" * 60)
    log("IMPORTING EXCEL TO GEODATABASE")
    log("=" * 60)

    output_table = os.path.join(config["geodatabase"], config["table_name"])

    log(f"  Source: {source_path}")
    log(f"  Target: {output_table}")
    log(f"  Sheet:  {config['sheet_name']}")

    # Start timing
    start_time = datetime.now()

    try:
        # Use ExcelToTable conversion
        log("Running arcpy.conversion.ExcelToTable...")
        arcpy.conversion.ExcelToTable(
            Input_Excel_File=source_path,
            Output_Table=output_table,
            Sheet=config["sheet_name"]
        )

        # Calculate elapsed time
        elapsed = datetime.now() - start_time
        log(f"  Import complete in {elapsed.total_seconds():.1f} seconds")

        return output_table

    except arcpy.ExecuteError as e:
        log(f"ERROR: ArcPy execution error: {e}", "ERROR")
        log(arcpy.GetMessages(2), "ERROR")
        raise
    except Exception as e:
        log(f"ERROR: Import failed: {e}", "ERROR")
        raise


def verify_import(table_path: str, config: dict) -> dict:
    """
    Verify the imported table has expected record count and fields.

    Returns:
        Dictionary with verification results
    """
    log("=" * 60)
    log("VERIFYING IMPORT")
    log("=" * 60)

    results = {
        "success": False,
        "record_count": 0,
        "expected_records": config["expected_records"],
        "field_count": 0,
        "fields": [],
        "date_range": {"min": None, "max": None}
    }

    # Get record count
    record_count = int(arcpy.management.GetCount(table_path)[0])
    results["record_count"] = record_count
    log(f"  Record count: {record_count:,}")

    if record_count == config["expected_records"]:
        log(f"  OK: Matches expected count ({config['expected_records']:,})")
    elif abs(record_count - config["expected_records"]) < 100:
        log(f"  WARN: Close to expected ({config['expected_records']:,}), diff: {abs(record_count - config['expected_records'])}", "WARN")
    else:
        log(f"  ERROR: Does not match expected ({config['expected_records']:,})", "ERROR")

    # Get fields
    fields = arcpy.ListFields(table_path)
    results["field_count"] = len(fields)
    results["fields"] = [f.name for f in fields]
    log(f"  Field count: {len(fields)}")

    # List key fields
    key_fields = ["ReportNumberNew", "Incident", "TimeOfCall", "Disposition", "Officer", "PDZone"]
    log("  Key fields check:")
    for field in key_fields:
        if field in results["fields"]:
            log(f"    {field}: OK")
        else:
            log(f"    {field}: MISSING", "WARN")

    # Check date range if TimeOfCall exists
    if "TimeOfCall" in results["fields"]:
        log("  Checking date range...")
        try:
            with arcpy.da.SearchCursor(table_path, ["TimeOfCall"]) as cursor:
                dates = [row[0] for row in cursor if row[0] is not None]
                if dates:
                    results["date_range"]["min"] = str(min(dates))
                    results["date_range"]["max"] = str(max(dates))
                    log(f"    Min date: {min(dates)}")
                    log(f"    Max date: {max(dates)}")
        except Exception as e:
            log(f"    Could not check date range: {e}", "WARN")

    # Determine success
    results["success"] = record_count > 0 and record_count >= config["expected_records"] * 0.99

    return results


def main():
    """Main execution function."""
    log("=" * 60)
    log("CAD POLISHED EXCEL TO GEODATABASE IMPORT")
    log("=" * 60)
    log(f"Start time: {datetime.now().isoformat()}")
    log("")

    # Pre-flight checks
    if not check_arcpy():
        sys.exit(1)

    check_license()

    try:
        # Verify source file
        source_path = verify_source_file(CONFIG)

        # Verify geodatabase
        verify_geodatabase(CONFIG)

        # Backup existing table
        backup_existing_table(CONFIG)

        # Import Excel to geodatabase
        table_path = import_excel_to_geodatabase(source_path, CONFIG)

        # Verify import
        results = verify_import(table_path, CONFIG)

        # Final summary
        log("")
        log("=" * 60)
        log("IMPORT SUMMARY")
        log("=" * 60)
        log(f"  Status: {'SUCCESS' if results['success'] else 'FAILED'}")
        log(f"  Table: {table_path}")
        log(f"  Records: {results['record_count']:,}")
        log(f"  Fields: {results['field_count']}")
        if results["date_range"]["min"]:
            log(f"  Date range: {results['date_range']['min']} to {results['date_range']['max']}")
        log("")

        if results["success"]:
            log("Import completed successfully!", "SUCCESS")
            log("")
            log("Next Steps:")
            log("  1. Refresh ArcGIS Pro project to see new table")
            log("  2. Update any layers/dashboards pointing to old data")
            log("  3. Verify data displays correctly in map")
        else:
            log("Import completed with warnings - please verify data", "WARN")

        return 0 if results["success"] else 1

    except Exception as e:
        log(f"FATAL ERROR: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
