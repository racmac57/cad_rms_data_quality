#!/usr/bin/env python3
"""
Quick Baseline Metadata Display

Shows date range, record count, and other metadata without fully loading the file.
Uses pandas to read only the TimeOfCall column for date range calculation.

Usage:
    python scripts/check_baseline_metadata.py
    python scripts/check_baseline_metadata.py --file "path/to/specific/file.xlsx"
"""

import pandas as pd
import json
from pathlib import Path
import argparse
from datetime import datetime

MANIFEST_PATH = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\manifest.json")
BASE_DIR = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base")


def load_manifest():
    """Load manifest.json if it exists."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    return None


def get_quick_metadata(file_path: Path):
    """
    Get metadata without fully loading the file.
    Only reads TimeOfCall column for date range.
    """
    print(f"\n{'='*80}")
    print(f"BASELINE METADATA: {file_path.name}")
    print(f"{'='*80}\n")
    
    # File info
    file_size_mb = file_path.stat().st_size / (1024**2)
    modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
    
    print(f"📁 File Information:")
    print(f"   Path: {file_path}")
    print(f"   Size: {file_size_mb:.1f} MB")
    print(f"   Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Extract dates from filename if present
    filename = file_path.name
    if "_" in filename:
        parts = filename.replace(".xlsx", "").split("_")
        if len(parts) >= 5:
            try:
                start_date_str = parts[-2]
                end_date_str = parts[-1]
                start_date = f"{start_date_str[:4]}-{start_date_str[4:6]}-{start_date_str[6:8]}"
                end_date = f"{end_date_str[:4]}-{end_date_str[4:6]}-{end_date_str[6:8]}"
                
                print(f"📅 Date Range (from filename):")
                print(f"   Start: {start_date}")
                print(f"   End:   {end_date}")
                
                # Calculate coverage
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                days = (end_dt - start_dt).days
                years = round(days / 365.25, 1)
                print(f"   Coverage: {days:,} days ({years} years)")
                print()
            except:
                pass
    
    # Quick record count (read first column only)
    print(f"📊 Record Count (reading file...):")
    try:
        df_count = pd.read_excel(file_path, usecols=[0])
        record_count = len(df_count)
        print(f"   Total Records: {record_count:,}")
        print()
    except Exception as e:
        print(f"   ⚠ Could not read record count: {e}")
        print()
    
    # Date range verification (read TimeOfCall column only)
    print(f"📅 Date Range (from data - verifying...):")
    try:
        df_dates = pd.read_excel(file_path, usecols=['TimeOfCall'], parse_dates=['TimeOfCall'])
        
        min_date = df_dates['TimeOfCall'].min()
        max_date = df_dates['TimeOfCall'].max()
        
        print(f"   Actual Start: {min_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Actual End:   {max_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Calculate coverage
        days = (max_date - min_date).days
        years = round(days / 365.25, 1)
        print(f"   Coverage: {days:,} days ({years} years)")
        print()
        
    except Exception as e:
        print(f"   ⚠ Could not verify date range: {e}")
        print()
    
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Check baseline file metadata")
    parser.add_argument('--file', type=Path, help='Specific file to check (default: use manifest)')
    args = parser.parse_args()
    
    if args.file:
        if not args.file.exists():
            print(f"✗ File not found: {args.file}")
            return 1
        get_quick_metadata(args.file)
    else:
        # Use manifest to find latest
        manifest = load_manifest()
        
        if manifest and 'latest' in manifest:
            latest_path = Path(manifest['latest']['full_path'])
            
            if latest_path.exists():
                get_quick_metadata(latest_path)
                
                # Also show generic pointer if different
                generic_path = Path(manifest['latest']['generic_path'])
                if generic_path.exists() and generic_path != latest_path:
                    print(f"\n{'='*80}")
                    print(f"Note: Generic pointer also exists at:")
                    print(f"      {generic_path}")
                    print(f"{'='*80}\n")
            else:
                print(f"✗ Latest file not found: {latest_path}")
                print(f"  Trying generic pointer...")
                
                generic_path = BASE_DIR / "CAD_ESRI_Polished_Baseline.xlsx"
                if generic_path.exists():
                    get_quick_metadata(generic_path)
                else:
                    print(f"✗ Generic pointer also not found")
                    return 1
        else:
            print("ℹ No manifest found. Checking for generic pointer...")
            generic_path = BASE_DIR / "CAD_ESRI_Polished_Baseline.xlsx"
            
            if generic_path.exists():
                get_quick_metadata(generic_path)
            else:
                print(f"✗ No baseline file found")
                print(f"\nSearching in: {BASE_DIR}")
                
                # List any Excel files found
                excel_files = list(BASE_DIR.glob("*.xlsx"))
                if excel_files:
                    print(f"\nFound {len(excel_files)} Excel file(s):")
                    for f in excel_files:
                        print(f"  - {f.name}")
                    print(f"\nRun with --file to check a specific file")
                return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
