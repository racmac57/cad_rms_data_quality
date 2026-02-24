#!/usr/bin/env python3
"""
Backfill Gap Analysis & Safe Merge Script

Analyzes missing data gaps and safely merges backfill data with deduplication.

PROBLEM: Missing CAD data for 01/01/2026 - 01/09/2026
SOLUTION: Download backfill file, check for overlaps, merge safely

Author: R. A. Carucci
Created: 2026-02-03
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse
import sys

# Paths
PROCESSED_DATA_ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA")
BASELINE_PATH = PROCESSED_DATA_ROOT / "ESRI_Polished" / "base" / "CAD_ESRI_Polished_Baseline.xlsx"
OUTPUT_PATH = PROCESSED_DATA_ROOT / "ESRI_Polished" / "base"

# Map common raw-CAD / alternate column names to ESRI polished baseline names.
# Merge output must match baseline schema so backfill (complete_backfill_simplified.py) works.
BACKFILL_TO_BASELINE_RENAME = {
    "Time_Of_Call": "Time of Call",
    "How_Reported": "How Reported",
    "Time_Dispatched": "Time Dispatched",
    "Time_Out": "Time Out",
    "Time_In": "Time In",
    "PDZone": "ZoneCalc",  # some exports use PDZone, baseline uses ZoneCalc
}


def analyze_gap(baseline_file: Path, gap_start: str = "2026-01-01", gap_end: str = "2026-01-09"):
    """
    Analyze the gap in the baseline file.
    
    Args:
        baseline_file: Path to baseline Excel file
        gap_start: Start of gap period (YYYY-MM-DD)
        gap_end: End of gap period (YYYY-MM-DD)
    """
    print(f"\n{'='*80}")
    print(f"GAP ANALYSIS: {gap_start} to {gap_end}")
    print(f"{'='*80}\n")
    
    print(f"[1] Loading baseline file...")
    print(f"    {baseline_file.name}")
    
    # Read TimeOfCall column only for speed
    df = pd.read_excel(baseline_file, usecols=['ReportNumberNew', 'Time of Call'], parse_dates=['Time of Call'])
    
    # Rename for easier use
    df.rename(columns={'Time of Call': 'TimeOfCall'}, inplace=True)
    
    print(f"    [OK] Loaded {len(df):,} records")
    print()
    
    # Convert gap dates to timestamps
    gap_start_dt = pd.Timestamp(gap_start)
    gap_end_dt = pd.Timestamp(gap_end + " 23:59:59")
    
    # Find records in gap period
    in_gap = df[(df['TimeOfCall'] >= gap_start_dt) & (df['TimeOfCall'] <= gap_end_dt)]
    
    print(f"[2] Records in gap period ({gap_start} to {gap_end}):")
    print(f"    Found: {len(in_gap):,} records")
    
    if len(in_gap) > 0:
        print(f"    [OK] Gap period HAS data (no missing records)")
        print(f"    Date range in gap: {in_gap['TimeOfCall'].min()} to {in_gap['TimeOfCall'].max()}")
        print()
        print(f"    First record: {in_gap['TimeOfCall'].min()}")
        print(f"    Last record: {in_gap['TimeOfCall'].max()}")
        print()
        print(f"[!] If you believe data is missing, check:")
        print(f"   1. Is the gap period correct? (currently {gap_start} to {gap_end})")
        print(f"   2. Do you have a separate backfill file for this period?")
        print(f"   3. Check the monthly export file: 2026_01_CAD.xlsx")
    else:
        print(f"    [X] Gap period is EMPTY (data is missing!)")
        print()
        print(f"[!] MISSING DATA CONFIRMED")
        print(f"   You need to obtain a backfill file for {gap_start} to {gap_end}")
        print(f"   Expected filename: 2026_01_01_to_2026_01_09_CAD.xlsx")
    
    print()
    
    # Find records before and after gap
    print(f"[3] Context records:")
    
    before_gap = df[df['TimeOfCall'] < gap_start_dt].sort_values('TimeOfCall', ascending=False).head(5)
    after_gap = df[df['TimeOfCall'] > gap_end_dt].sort_values('TimeOfCall', ascending=True).head(5)
    
    if len(before_gap) > 0:
        print(f"    Last 5 records BEFORE gap:")
        for idx, row in before_gap.iterrows():
            print(f"      {row['TimeOfCall']} - {row['ReportNumberNew']}")
    
    if len(after_gap) > 0:
        print(f"\n    First 5 records AFTER gap:")
        for idx, row in after_gap.iterrows():
            print(f"      {row['TimeOfCall']} - {row['ReportNumberNew']}")
    
    print()
    print(f"{'='*80}\n")
    
    return len(in_gap) == 0


def merge_backfill_data(
    baseline_file: Path,
    backfill_file: Path,
    output_file: Path = None,
    dry_run: bool = False
):
    """
    Safely merge backfill data with baseline, checking for duplicates.
    
    Args:
        baseline_file: Path to current baseline
        backfill_file: Path to backfill Excel file (new data to add)
        output_file: Path for merged output (if None, creates versioned file)
        dry_run: If True, only show what would happen
    """
    print(f"\n{'='*80}")
    print(f"BACKFILL DATA MERGE")
    print(f"{'='*80}\n")
    
    # Step 1: Load baseline
    print(f"[1] Loading baseline file...")
    print(f"    {baseline_file.name}")
    
    df_baseline = pd.read_excel(baseline_file)
    baseline_count = len(df_baseline)
    baseline_has_time_of_call = 'Time of Call' in df_baseline.columns
    # Normalize time column (ESRI polished uses "Time of Call", exports may use TimeOfCall)
    if 'Time of Call' in df_baseline.columns and 'TimeOfCall' not in df_baseline.columns:
        df_baseline['TimeOfCall'] = df_baseline['Time of Call']
    baseline_time_col = 'TimeOfCall' if 'TimeOfCall' in df_baseline.columns else ('Time of Call' if 'Time of Call' in df_baseline.columns else None)
    
    # Canonical schema: output will match baseline columns exactly (required for backfill script)
    baseline_columns = [c for c in df_baseline.columns if c != 'TimeOfCall']
    
    print(f"    [OK] Loaded {baseline_count:,} records")
    
    if 'ReportNumberNew' in df_baseline.columns:
        baseline_unique = df_baseline['ReportNumberNew'].nunique()
        print(f"    Unique cases: {baseline_unique:,}")
    
    if baseline_time_col and baseline_time_col in df_baseline.columns:
        df_baseline['TimeOfCall'] = pd.to_datetime(df_baseline[baseline_time_col])
        baseline_min = df_baseline['TimeOfCall'].min()
        baseline_max = df_baseline['TimeOfCall'].max()
        print(f"    Date range: {baseline_min} to {baseline_max}")
    
    print()
    
    # Step 2: Load backfill
    print(f"[2] Loading backfill file...")
    print(f"    {backfill_file.name}")
    
    df_backfill = pd.read_excel(backfill_file)
    backfill_count = len(df_backfill)
    # Normalize backfill column names to match baseline (ESRI polished schema)
    rename_map = {k: v for k, v in BACKFILL_TO_BASELINE_RENAME.items()
                  if k in df_backfill.columns and v in baseline_columns}
    if rename_map:
        df_backfill = df_backfill.rename(columns=rename_map)
        print(f"    Renamed columns to match baseline: {list(rename_map.keys())} -> {list(rename_map.values())}")
    # Align to baseline schema: same columns and order; missing cols become NaN
    for c in baseline_columns:
        if c not in df_backfill.columns:
            df_backfill[c] = pd.NA
    df_backfill = df_backfill[baseline_columns]
    if 'Time of Call' in df_backfill.columns and 'TimeOfCall' not in df_backfill.columns:
        df_backfill['TimeOfCall'] = df_backfill['Time of Call']
    
    print(f"    [OK] Loaded {backfill_count:,} records (schema aligned to baseline)")
    
    if 'ReportNumberNew' in df_backfill.columns:
        backfill_unique = df_backfill['ReportNumberNew'].nunique()
        print(f"    Unique cases: {backfill_unique:,}")
    
    if 'TimeOfCall' in df_backfill.columns:
        df_backfill['TimeOfCall'] = pd.to_datetime(df_backfill['TimeOfCall'])
        backfill_min = df_backfill['TimeOfCall'].min()
        backfill_max = df_backfill['TimeOfCall'].max()
        print(f"    Date range: {backfill_min} to {backfill_max}")
    
    print()
    
    # Step 3: Check for duplicates
    print(f"[3] Checking for duplicate case numbers...")
    
    if 'ReportNumberNew' not in df_baseline.columns or 'ReportNumberNew' not in df_backfill.columns:
        print(f"    [!] WARNING: ReportNumberNew column not found")
        print(f"    Cannot check for duplicates!")
        print()
        duplicate_count = 0
    else:
        baseline_ids = set(df_baseline['ReportNumberNew'].dropna())
        backfill_ids = set(df_backfill['ReportNumberNew'].dropna())
        
        duplicates = baseline_ids & backfill_ids
        duplicate_count = len(duplicates)
        
        print(f"    Baseline cases: {len(baseline_ids):,}")
        print(f"    Backfill cases: {len(backfill_ids):,}")
        print(f"    Duplicate cases: {duplicate_count:,}")
        
        if duplicate_count > 0:
            print()
            print(f"    [!] Found {duplicate_count:,} duplicate case numbers!")
            print(f"    These will be KEPT from baseline (backfill duplicates discarded)")
            print()
            print(f"    Sample duplicates:")
            for case_id in list(duplicates)[:10]:
                print(f"      - {case_id}")
            if duplicate_count > 10:
                print(f"      ... and {duplicate_count - 10:,} more")
        else:
            print(f"    [OK] No duplicates found - safe to merge!")
    
    print()
    
    # Step 4: Merge (remove duplicates from backfill)
    print(f"[4] Merging data...")
    
    if duplicate_count > 0 and 'ReportNumberNew' in df_backfill.columns:
        # Remove duplicates from backfill
        df_backfill_unique = df_backfill[~df_backfill['ReportNumberNew'].isin(baseline_ids)]
        removed_count = len(df_backfill) - len(df_backfill_unique)
        
        print(f"    Removed {removed_count:,} duplicate records from backfill")
        print(f"    Adding {len(df_backfill_unique):,} new records")
    else:
        df_backfill_unique = df_backfill
        print(f"    Adding {len(df_backfill_unique):,} records (no duplicates)")
    
    # Concatenate
    df_merged = pd.concat([df_baseline, df_backfill_unique], ignore_index=True)
    
    # Sort by TimeOfCall
    if 'TimeOfCall' in df_merged.columns:
        df_merged = df_merged.sort_values('TimeOfCall').reset_index(drop=True)
    
    merged_count = len(df_merged)
    
    print(f"    [OK] Merged dataset: {merged_count:,} records")
    
    if 'ReportNumberNew' in df_merged.columns:
        merged_unique = df_merged['ReportNumberNew'].nunique()
        print(f"    Unique cases: {merged_unique:,}")
    
    if 'TimeOfCall' in df_merged.columns:
        merged_min = df_merged['TimeOfCall'].min()
        merged_max = df_merged['TimeOfCall'].max()
        print(f"    Date range: {merged_min} to {merged_max}")
    
    print()
    
    # Step 5: Save
    if output_file is None:
        # Create versioned filename
        if 'TimeOfCall' in df_merged.columns:
            start_date = df_merged['TimeOfCall'].min().strftime('%Y%m%d')
            end_date = df_merged['TimeOfCall'].max().strftime('%Y%m%d')
            output_file = OUTPUT_PATH / f"CAD_ESRI_Polished_Baseline_{start_date}_{end_date}.xlsx"
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = OUTPUT_PATH / f"CAD_ESRI_Polished_Baseline_{timestamp}.xlsx"
    
    print(f"[5] Saving merged data...")
    print(f"    Output: {output_file.name}")
    print(f"    (Writing 758k+ rows to Excel can take 5-15 minutes...)")
    
    if not dry_run:
        # Output exactly baseline schema (columns and order) so backfill script succeeds
        out_cols = [c for c in baseline_columns if c in df_merged.columns]
        out_df = df_merged[out_cols].copy()
        out_df.to_excel(output_file, index=False, engine='openpyxl')
        
        file_size_mb = output_file.stat().st_size / (1024**2)
        print(f"    [OK] Saved: {file_size_mb:.1f} MB (schema matches baseline)")
        
        # Also update generic pointer
        generic_path = OUTPUT_PATH / "CAD_ESRI_Polished_Baseline.xlsx"
        out_df.to_excel(generic_path, index=False, engine='openpyxl')
        print(f"    [OK] Updated generic pointer: {generic_path.name}")
    else:
        print(f"    [DRY RUN] Would save here")
    
    print()
    print(f"{'='*80}")
    print(f"[OK] MERGE COMPLETE")
    print(f"{'='*80}")
    print()
    print(f"Summary:")
    print(f"  Baseline records: {baseline_count:,}")
    print(f"  Backfill records: {backfill_count:,}")
    print(f"  Duplicates removed (backfill vs baseline): {duplicate_count:,} cases")
    print(f"  New records added: {len(df_backfill_unique):,}")
    print(f"  Final total: {merged_count:,} rows")
    if 'ReportNumberNew' in df_merged.columns:
        u = df_merged['ReportNumberNew'].nunique()
        print(f"  Unique ReportNumberNew: {u:,} (multiple rows per case is normal if baseline had them)")
    print()
    
    if not dry_run:
        print(f"Next steps:")
        print(f"  1. Verify output file: {output_file}")
        print(f"  2. Update manifest: python scripts/update_baseline_from_polished.py --source \"{output_file}\"")
        print(f"  3. Deploy to server for backfill")
    
    print()
    
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Analyze gaps and merge backfill data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze gap (default baseline, gap 2026-01-01 to 2026-01-09)
  python scripts/backfill_gap_analysis.py
  python scripts/backfill_gap_analysis.py --analyze

  # Analyze with custom gap range
  python scripts/backfill_gap_analysis.py --analyze --gap-start 2026-01-01 --gap-end 2026-01-09

  # Merge backfill data (dry run first!)
  python scripts/backfill_gap_analysis.py --merge --backfill "path/to/2026_01_01_to_2026_01_09_CAD.xlsx" --dry-run

  # Actual merge
  python scripts/backfill_gap_analysis.py --merge --backfill "path/to/2026_01_01_to_2026_01_09_CAD.xlsx"
        """
    )
    
    parser.add_argument('--analyze', action='store_true', help='Analyze gap in baseline')
    parser.add_argument('--merge', action='store_true', help='Merge backfill data with baseline')
    parser.add_argument('--baseline', type=Path, default=BASELINE_PATH, help='Path to baseline file')
    parser.add_argument('--backfill', type=Path, help='Path to backfill file (for merge)')
    parser.add_argument('--output', type=Path, help='Output file path (default: auto-generate versioned name)')
    parser.add_argument('--gap-start', default='2026-01-01', help='Gap start date (YYYY-MM-DD)')
    parser.add_argument('--gap-end', default='2026-01-09', help='Gap end date (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true', help='Preview merge without saving')
    
    args = parser.parse_args()
    
    # Default to analyze if no mode given (e.g. "python backfill_gap_analysis.py")
    if not args.analyze and not args.merge:
        args.analyze = True
    
    try:
        if args.analyze:
            if not args.baseline.exists():
                print(f"[X] Baseline file not found: {args.baseline}")
                return 1
            
            has_gap = analyze_gap(args.baseline, args.gap_start, args.gap_end)
            
            if has_gap:
                print("[!] ACTION REQUIRED:")
                print("   1. Obtain backfill file for the gap period")
                print("   2. Run with --merge to add the data")
            else:
                print("[OK] No action needed - gap period already has data")
        
        if args.merge:
            if not args.baseline.exists():
                print(f"[X] Baseline file not found: {args.baseline}")
                return 1
            
            if not args.backfill:
                print(f"[X] Must specify --backfill file for merge operation")
                return 1
            
            if not args.backfill.exists():
                print(f"[X] Backfill file not found: {args.backfill}")
                return 1
            
            output_file = merge_backfill_data(
                args.baseline,
                args.backfill,
                args.output,
                args.dry_run
            )
        
        return 0
        
    except Exception as e:
        print(f"\n[X] ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
