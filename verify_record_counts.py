#!/usr/bin/env python3
"""
CAD Record Count Verification Script
Computes actual record counts from CAD XLSX files and compares against expected counts.

Generates:
  - outputs/consolidation/record_count_verification.txt (summary report)
  - outputs/consolidation/record_counts_actual.json (JSON data)

Author: R.A.C. | 2026-01-30
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
CAD_YEARLY_PATH = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\yearly")
OUTPUT_DIR = Path(r"c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\outputs\consolidation")

# Expected counts from Claude chat (2019-2025 consolidation target)
EXPECTED_COUNTS = {
    2019: 26000,
    2020: 28000,
    2021: 30000,
    2022: 31000,
    2023: 32000,
    2024: 33000,
    2025: 34000,
}

# Tolerance for count deviation (±5%)
TOLERANCE_PERCENT = 5.0

def compute_file_counts(xlsx_path: Path) -> Dict:
    """
    Compute record counts for a single XLSX file.
    
    Returns dict with:
      - total_rows: Total row count
      - unique_cases: Unique ReportNumberNew count
      - file_size: File size in bytes
    """
    try:
        df = pd.read_excel(xlsx_path, engine="openpyxl")
        
        total_rows = len(df)
        unique_cases = df['ReportNumberNew'].nunique() if 'ReportNumberNew' in df.columns else 0
        file_size = xlsx_path.stat().st_size
        
        return {
            "total_rows": total_rows,
            "unique_cases": unique_cases,
            "file_size": file_size,
            "status": "success"
        }
    except Exception as e:
        return {
            "total_rows": 0,
            "unique_cases": 0,
            "file_size": 0,
            "status": "error",
            "error": str(e)
        }

def format_deviation(actual: int, expected: int) -> str:
    """Format deviation as ±X% and ±X rows."""
    if expected == 0:
        return "N/A"
    
    diff = actual - expected
    percent = (diff / expected) * 100
    
    return f"{diff:+,} ({percent:+.1f}%)"

def main():
    print("=" * 80)
    print("CAD RECORD COUNT VERIFICATION")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: {CAD_YEARLY_PATH}")
    print()
    
    results = []
    consolidated_target_actual = 0
    consolidated_target_expected = 0
    
    # Process each year directory
    for year in range(2012, 2026):
        year_dir = CAD_YEARLY_PATH / str(year)
        
        if not year_dir.exists():
            print(f"⚠ {year}: Directory not found")
            continue
        
        # Find XLSX file in year directory
        xlsx_files = list(year_dir.glob("*.xlsx"))
        if not xlsx_files:
            print(f"⚠ {year}: No XLSX file found")
            continue
        
        xlsx_file = xlsx_files[0]
        print(f"Processing {year}: {xlsx_file.name}...", end=" ")
        
        # Compute counts
        counts = compute_file_counts(xlsx_file)
        
        if counts["status"] == "error":
            print(f"❌ ERROR: {counts['error']}")
            results.append({
                "year": year,
                "file": xlsx_file.name,
                "status": "error",
                "error": counts["error"]
            })
            continue
        
        # Compare against expected (if defined)
        expected = EXPECTED_COUNTS.get(year)
        actual = counts["total_rows"]
        
        if expected:
            # Calculate deviation
            tolerance = expected * (TOLERANCE_PERCENT / 100)
            within_tolerance = abs(actual - expected) <= tolerance
            
            deviation = format_deviation(actual, expected)
            status = "[OK]" if within_tolerance else "[WARN]"
            
            print(f"{status} Actual: {actual:,} | Expected: {expected:,} | Deviation: {deviation}")
            
            # Add to consolidation target totals (2019-2025)
            consolidated_target_actual += actual
            consolidated_target_expected += expected
        else:
            print(f"[OK] Actual: {actual:,} (no expected count)")
        
        # Store result
        results.append({
            "year": year,
            "file": xlsx_file.name,
            "total_rows": actual,
            "unique_cases": counts["unique_cases"],
            "file_size": counts["file_size"],
            "expected_rows": expected,
            "deviation": format_deviation(actual, expected) if expected else None,
            "within_tolerance": abs(actual - expected) <= (expected * TOLERANCE_PERCENT / 100) if expected else None,
            "status": "success"
        })
    
    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_all_years = sum(r["total_rows"] for r in results if r["status"] == "success")
    total_unique_all = sum(r["unique_cases"] for r in results if r["status"] == "success")
    
    print(f"\nAll Years (2012-2025):")
    print(f"  Total Records: {total_all_years:,}")
    print(f"  Unique Cases:  {total_unique_all:,}")
    
    if consolidated_target_actual > 0:
        print(f"\nConsolidation Target (2019-2025):")
        print(f"  Actual Records:   {consolidated_target_actual:,}")
        print(f"  Expected Records: {consolidated_target_expected:,}")
        print(f"  Deviation:        {format_deviation(consolidated_target_actual, consolidated_target_expected)}")
        
        # Check if within tolerance
        overall_tolerance = consolidated_target_expected * (TOLERANCE_PERCENT / 100)
        within_tolerance = abs(consolidated_target_actual - consolidated_target_expected) <= overall_tolerance
        
        if within_tolerance:
            print(f"  Status: [OK] WITHIN TOLERANCE (+/-{TOLERANCE_PERCENT}%)")
        else:
            print(f"  Status: [WARN] OUTSIDE TOLERANCE (+/-{TOLERANCE_PERCENT}%)")
    
    # Issues
    errors = [r for r in results if r["status"] == "error"]
    out_of_tolerance = [r for r in results if r.get("within_tolerance") == False]
    
    if errors:
        print(f"\n[WARN] Errors: {len(errors)} files")
        for r in errors:
            print(f"  - {r['year']}: {r['error']}")
    
    if out_of_tolerance:
        print(f"\n[WARN] Out of Tolerance: {len(out_of_tolerance)} files (+/-{TOLERANCE_PERCENT}%)")
        for r in out_of_tolerance:
            print(f"  - {r['year']}: Expected {r['expected_rows']:,}, Actual {r['total_rows']:,}, {r['deviation']}")
    
    # Write reports
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # JSON output
    json_path = OUTPUT_DIR / "record_counts_actual.json"
    with open(json_path, 'w') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "source_directory": str(CAD_YEARLY_PATH),
            "tolerance_percent": TOLERANCE_PERCENT,
            "summary": {
                "all_years_total": total_all_years,
                "all_years_unique": total_unique_all,
                "consolidation_target_actual": consolidated_target_actual,
                "consolidation_target_expected": consolidated_target_expected,
                "within_tolerance": within_tolerance if consolidated_target_actual > 0 else None
            },
            "yearly_counts": results,
            "errors": len(errors),
            "out_of_tolerance": len(out_of_tolerance)
        }, f, indent=2)
    
    print(f"\n[OK] JSON output: {json_path}")
    
    # Text report
    txt_path = OUTPUT_DIR / "record_count_verification.txt"
    with open(txt_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("CAD RECORD COUNT VERIFICATION REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: {CAD_YEARLY_PATH}\n")
        f.write(f"Tolerance: ±{TOLERANCE_PERCENT}%\n")
        f.write("\n")
        
        f.write("YEARLY COUNTS\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Year':<6} {'Total Rows':<12} {'Unique Cases':<14} {'Expected':<12} {'Deviation':<20} {'Status':<10}\n")
        f.write("-" * 80 + "\n")
        
        for r in results:
            if r["status"] == "error":
                f.write(f"{r['year']:<6} {'ERROR':<12} {'':<14} {'':<12} {'':<20} {'❌':<10}\n")
            else:
                expected_str = f"{r['expected_rows']:,}" if r['expected_rows'] else "N/A"
                deviation_str = r['deviation'] if r['deviation'] else "N/A"
                status_str = "✓" if r.get('within_tolerance') != False else "⚠"
                
                f.write(f"{r['year']:<6} {r['total_rows']:<12,} {r['unique_cases']:<14,} {expected_str:<12} {deviation_str:<20} {status_str:<10}\n")
        
        f.write("\n")
        f.write("SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"All Years (2012-2025):          {total_all_years:,} total rows\n")
        f.write(f"Unique Cases (all years):       {total_unique_all:,}\n")
        f.write(f"\n")
        f.write(f"Consolidation Target (2019-2025):\n")
        f.write(f"  Actual Records:               {consolidated_target_actual:,}\n")
        f.write(f"  Expected Records:             {consolidated_target_expected:,}\n")
        f.write(f"  Deviation:                    {format_deviation(consolidated_target_actual, consolidated_target_expected)}\n")
        f.write(f"  Within Tolerance (±{TOLERANCE_PERCENT}%):     {'YES' if within_tolerance else 'NO'}\n")
    
    print(f"[OK] Text report: {txt_path}")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    
    return 0 if len(errors) == 0 and within_tolerance else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
