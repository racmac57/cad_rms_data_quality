#!/usr/bin/env python3
"""
Update Baseline File After Polished Output Generation

This script:
1. Finds the latest polished Excel file from CAD_Data_Cleaning_Engine
2. Copies it to 13_PROCESSED_DATA/ESRI_Polished/base/
3. Updates manifest.json
4. Creates both a versioned archive AND updates the generic baseline pointer

Author: R. A. Carucci
Created: 2026-02-03
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
import argparse
import sys

# Paths
CLEANING_ENGINE_OUTPUT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final")
PROCESSED_DATA_ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA")
BASE_DIR = PROCESSED_DATA_ROOT / "ESRI_Polished" / "base"
MANIFEST_PATH = PROCESSED_DATA_ROOT / "manifest.json"

# File patterns
GENERIC_BASELINE_NAME = "CAD_ESRI_Polished_Baseline.xlsx"
POLISHED_PATTERN = "CAD_ESRI_POLISHED_*.xlsx"


def find_latest_polished_file(source_dir: Path = CLEANING_ENGINE_OUTPUT) -> Path:
    """
    Find the most recently created polished Excel file.
    
    Returns:
        Path to latest polished file
    """
    polished_files = list(source_dir.glob(POLISHED_PATTERN))
    
    if not polished_files:
        raise FileNotFoundError(f"No polished files found in {source_dir}")
    
    # Sort by modification time, newest first
    latest_file = max(polished_files, key=lambda p: p.stat().st_mtime)
    return latest_file


def get_file_metadata(file_path: Path) -> dict:
    """Extract metadata from Excel file for manifest."""
    try:
        # Read just the header to get column count and first few rows for date range
        df_sample = pd.read_excel(file_path, nrows=1000)
        
        # Get full record count (more efficient - just count rows)
        df_full = pd.read_excel(file_path, usecols=[0])  # Read only first column
        record_count = len(df_full)
        
        # Try to get date range if TimeOfCall column exists
        date_range = None
        if 'TimeOfCall' in df_sample.columns:
            df_dates = pd.read_excel(file_path, usecols=['TimeOfCall'], parse_dates=['TimeOfCall'])
            date_range = {
                'start': df_dates['TimeOfCall'].min().strftime('%Y-%m-%d'),
                'end': df_dates['TimeOfCall'].max().strftime('%Y-%m-%d')
            }
        
        return {
            'record_count': record_count,
            'date_range': date_range,
            'columns': list(df_sample.columns),
            'column_count': len(df_sample.columns)
        }
    except Exception as e:
        print(f"Warning: Could not extract metadata: {e}")
        return {
            'record_count': None,
            'date_range': None,
            'columns': [],
            'column_count': None
        }


def create_versioned_filename(source_file: Path, date_range: dict = None) -> str:
    """
    Create a versioned filename based on date range.
    
    Examples:
        CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx
        CAD_ESRI_Polished_Baseline_20190101_20260202.xlsx
    """
    if date_range:
        start_date = date_range['start'].replace('-', '')
        end_date = date_range['end'].replace('-', '')
        return f"CAD_ESRI_Polished_Baseline_{start_date}_{end_date}.xlsx"
    else:
        # Fallback: use current timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"CAD_ESRI_Polished_Baseline_{timestamp}.xlsx"


def update_baseline(source_file: Path = None, dry_run: bool = False):
    """
    Update baseline file in 13_PROCESSED_DATA.
    
    Args:
        source_file: Path to polished file (if None, finds latest)
        dry_run: If True, only show what would happen
    """
    print("=" * 80)
    print("UPDATE BASELINE FROM POLISHED OUTPUT")
    print("=" * 80)
    
    # Step 1: Find source file
    if source_file is None:
        print("\n[Step 1] Finding latest polished file...")
        source_file = find_latest_polished_file()
    else:
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
    
    print(f"  Source: {source_file.name}")
    print(f"  Size: {source_file.stat().st_size / (1024**2):.1f} MB")
    print(f"  Modified: {datetime.fromtimestamp(source_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 2: Extract metadata
    print("\n[Step 2] Extracting metadata...")
    metadata = get_file_metadata(source_file)
    print(f"  Records: {metadata['record_count']:,}" if metadata['record_count'] else "  Records: Unknown")
    if metadata['date_range']:
        print(f"  Date range: {metadata['date_range']['start']} to {metadata['date_range']['end']}")
    print(f"  Columns: {metadata['column_count']}" if metadata['column_count'] else "  Columns: Unknown")
    
    # Step 3: Create versioned filename
    print("\n[Step 3] Creating versioned filename...")
    versioned_name = create_versioned_filename(source_file, metadata['date_range'])
    print(f"  Versioned: {versioned_name}")
    
    # Step 4: Copy to base directory
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    versioned_path = BASE_DIR / versioned_name
    generic_path = BASE_DIR / GENERIC_BASELINE_NAME
    
    print(f"\n[Step 4] Copying to base directory...")
    print(f"  Target (versioned): {versioned_path}")
    print(f"  Target (generic): {generic_path}")
    
    if not dry_run:
        # Copy as versioned archive
        shutil.copy2(source_file, versioned_path)
        print(f"  ✓ Copied to versioned archive")
        
        # Copy/overwrite generic baseline
        shutil.copy2(source_file, generic_path)
        print(f"  ✓ Updated generic baseline pointer")
    else:
        print("  [DRY RUN] Would copy files here")
    
    # Step 5: Update manifest.json
    print(f"\n[Step 5] Updating manifest...")
    
    manifest_data = {
        'latest': {
            'filename': versioned_name,
            'generic_pointer': GENERIC_BASELINE_NAME,
            'full_path': str(versioned_path),
            'generic_path': str(generic_path),
            'record_count': metadata['record_count'],
            'date_range': metadata['date_range'],
            'file_size_mb': round(source_file.stat().st_size / (1024**2), 1),
            'updated': datetime.now().isoformat(),
            'source_file': str(source_file),
            'run_type': 'baseline_update'
        },
        'baseline': {
            'path': str(generic_path),
            'versioned_path': str(versioned_path),
            'record_count': metadata['record_count'],
            'date_range': metadata['date_range']
        },
        'history': {
            'last_update': datetime.now().isoformat(),
            'update_method': 'update_baseline_from_polished.py'
        }
    }
    
    if not dry_run:
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2)
        print(f"  ✓ Updated manifest: {MANIFEST_PATH}")
    else:
        print("  [DRY RUN] Would update manifest here")
        print(f"  Preview:\n{json.dumps(manifest_data, indent=2)[:500]}...")
    
    # Summary
    print("\n" + "=" * 80)
    print("✓ BASELINE UPDATE COMPLETE")
    print("=" * 80)
    print(f"\nBaseline files:")
    print(f"  Generic: {generic_path}")
    print(f"  Versioned: {versioned_path}")
    print(f"\nManifest: {MANIFEST_PATH}")
    if metadata['date_range']:
        print(f"\nDate range: {metadata['date_range']['start']} to {metadata['date_range']['end']}")
    print(f"Records: {metadata['record_count']:,}" if metadata['record_count'] else "Records: Unknown")
    
    return versioned_path


def main():
    parser = argparse.ArgumentParser(
        description="Update baseline file from latest polished output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update from latest polished file
  python update_baseline_from_polished.py
  
  # Dry run to preview
  python update_baseline_from_polished.py --dry-run
  
  # Specify source file
  python update_baseline_from_polished.py --source "path/to/CAD_ESRI_POLISHED_20260203_123456.xlsx"
        """
    )
    
    parser.add_argument(
        '--source',
        type=Path,
        help='Path to polished Excel file (default: find latest in 03_final/)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would happen without making changes'
    )
    
    args = parser.parse_args()
    
    try:
        update_baseline(source_file=args.source, dry_run=args.dry_run)
        return 0
    except Exception as e:
        print(f"\n✗ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
