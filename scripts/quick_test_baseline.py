#!/usr/bin/env python3
"""
Quick Baseline Test - Single File Read

Fast test that reads the baseline file once and performs all checks.

Author: R. A. Carucci
Date: 2026-02-03
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

BASELINE_PATH = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx")

print(f"\n{'='*80}")
print(f"QUICK BASELINE TEST")
print(f"{'='*80}\n")

print(f"File: {BASELINE_PATH.name}")

# Test 1: File integrity
file_size_mb = BASELINE_PATH.stat().st_size / (1024**2)
print(f"Size: {file_size_mb:.1f} MB")

# Test 2: Load full file ONCE
print(f"\nLoading baseline file...")
start_time = datetime.now()
df = pd.read_excel(BASELINE_PATH, parse_dates=['Time of Call'])
load_time = (datetime.now() - start_time).total_seconds()
print(f"Loaded in {load_time:.1f} seconds")

# Test 3: Record count
print(f"\nTotal records: {len(df):,}")

# Test 4: Columns
print(f"Columns: {len(df.columns)}")
print(f"Column names: {list(df.columns[:5])}...")

# Test 5: Date range
min_date = df['Time of Call'].min()
max_date = df['Time of Call'].max()
print(f"\nDate range: {min_date} to {max_date}")

# Test 6: Null dates
null_dates = df['Time of Call'].isna().sum()
print(f"Null dates: {null_dates:,} ({(null_dates/len(df)*100):.2f}%)")

# Test 7: Jan 1-9 gap
jan_1_9 = df[(df['Time of Call'] >= '2026-01-01') & (df['Time of Call'] <= '2026-01-09 23:59:59')]
print(f"\nJan 1-9 records: {len(jan_1_9):,}")
if len(jan_1_9) > 0:
    print(f"  First: {jan_1_9['Time of Call'].min()}")
    print(f"  Last: {jan_1_9['Time of Call'].max()}")

# Test 8: Monthly distribution 2026
print(f"\n2026 Monthly Distribution:")
df_2026 = df[df['Time of Call'] >= '2026-01-01']
monthly = df_2026.groupby(df_2026['Time of Call'].dt.to_period('M')).size()
for month, count in monthly.items():
    print(f"  {month}: {count:,} records")

# Test 9: Duplicates
dupes = df['ReportNumberNew'].duplicated().sum()
print(f"\nDuplicate case numbers: {dupes:,}")

# Test 10: Case number format
valid_format = df['ReportNumberNew'].astype(str).str.match(r'^\d{2}-\d{6}[A-Z]?$').sum()
print(f"Valid case number format: {valid_format:,} ({(valid_format/len(df)*100):.1f}%)")

# Summary
print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")

issues = []
if null_dates > 0:
    issues.append(f"Has {null_dates:,} null dates")
if len(jan_1_9) == 0:
    issues.append("Missing Jan 1-9 data")
if len(jan_1_9) < 1000 and len(jan_1_9) > 0:
    issues.append(f"Jan 1-9 has only {len(jan_1_9):,} records (expected ~3,000)")
if valid_format < len(df) * 0.99:
    issues.append(f"Only {(valid_format/len(df)*100):.1f}% valid case numbers")

if issues:
    print(f"\n[!] Issues found:")
    for issue in issues:
        print(f"    - {issue}")
else:
    print(f"\n[OK] All checks passed! Baseline is ready.")

print(f"\n[OK] Test complete in {load_time:.1f} seconds")
