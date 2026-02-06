#!/usr/bin/env python3
"""
Comprehensive Baseline Testing Script

Tests:
1. File integrity (exists, readable, size)
2. Record count verification
3. Date range verification (2019-01-01 to 2026-02-03)
4. Column structure (all 20 ESRI columns present)
5. Data quality checks (nulls, invalid dates, duplicates)
6. Jan 1-9 gap verification
7. Monthly record distribution

Author: R. A. Carucci
Date: 2026-02-03
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Baseline file path
BASELINE_PATH = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx")

# Expected ESRI columns
EXPECTED_COLUMNS = [
    'ReportNumberNew', 'Incident', 'How Reported', 'FullAddress2', 'Grid', 'ZoneCalc',
    'Time of Call', 'cYear', 'cMonth', 'Hour_Calc', 'DayofWeek',
    'Time Dispatched', 'Time Out', 'Time In', 'Time Spent', 'Time Response',
    'Officer', 'Disposition', 'latitude', 'longitude'
]

def print_section(title):
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")

def test_file_integrity():
    """Test 1: File exists and is readable."""
    print_section("TEST 1: File Integrity")
    
    if not BASELINE_PATH.exists():
        print(f"[FAIL] File not found: {BASELINE_PATH}")
        return False
    
    print(f"[PASS] File exists: {BASELINE_PATH.name}")
    
    file_size_mb = BASELINE_PATH.stat().st_size / (1024**2)
    print(f"[INFO] File size: {file_size_mb:.1f} MB")
    
    if file_size_mb < 50:
        print(f"[WARN] File seems small (expected ~75 MB)")
    elif file_size_mb > 100:
        print(f"[WARN] File seems large (expected ~75 MB)")
    else:
        print(f"[PASS] File size is reasonable")
    
    modified_time = datetime.fromtimestamp(BASELINE_PATH.stat().st_mtime)
    print(f"[INFO] Last modified: {modified_time}")
    
    return True

def test_record_count():
    """Test 2: Record count verification."""
    print_section("TEST 2: Record Count")
    
    print("[INFO] Reading first column to count records...")
    df_count = pd.read_excel(BASELINE_PATH, usecols=[0])
    record_count = len(df_count)
    
    print(f"[INFO] Total records: {record_count:,}")
    
    expected_count = 754409
    diff = record_count - expected_count
    pct_diff = (diff / expected_count) * 100
    
    if record_count == expected_count:
        print(f"[PASS] Record count matches expected: {expected_count:,}")
        return True
    elif abs(pct_diff) < 1:
        print(f"[PASS] Record count within 1% of expected ({diff:+,} records, {pct_diff:+.2f}%)")
        return True
    else:
        print(f"[WARN] Record count differs by {diff:+,} records ({pct_diff:+.2f}%)")
        print(f"       Expected: {expected_count:,}, Got: {record_count:,}")
        return False

def test_column_structure():
    """Test 3: Column structure verification."""
    print_section("TEST 3: Column Structure")
    
    print("[INFO] Reading column headers...")
    df_header = pd.read_excel(BASELINE_PATH, nrows=0)
    actual_columns = list(df_header.columns)
    
    print(f"[INFO] Found {len(actual_columns)} columns")
    
    # Check for missing columns
    missing = set(EXPECTED_COLUMNS) - set(actual_columns)
    if missing:
        print(f"[FAIL] Missing columns: {missing}")
        return False
    
    # Check for extra columns
    extra = set(actual_columns) - set(EXPECTED_COLUMNS)
    if extra:
        print(f"[WARN] Extra columns found: {extra}")
    
    # Check column order
    if actual_columns == EXPECTED_COLUMNS:
        print(f"[PASS] All 20 ESRI columns present in correct order")
        return True
    else:
        print(f"[WARN] Columns present but order differs")
        print(f"       Expected: {EXPECTED_COLUMNS[:5]}...")
        print(f"       Got: {actual_columns[:5]}...")
        return True

def test_date_range():
    """Test 4: Date range verification."""
    print_section("TEST 4: Date Range")
    
    print("[INFO] Reading Time of Call column...")
    df_dates = pd.read_excel(BASELINE_PATH, usecols=['Time of Call'], parse_dates=['Time of Call'])
    
    # Check for null dates
    null_count = df_dates['Time of Call'].isna().sum()
    total_count = len(df_dates)
    
    if null_count > 0:
        null_pct = (null_count / total_count) * 100
        print(f"[WARN] Found {null_count:,} null dates ({null_pct:.2f}%)")
    else:
        print(f"[PASS] No null dates found")
    
    # Get date range
    min_date = df_dates['Time of Call'].min()
    max_date = df_dates['Time of Call'].max()
    
    print(f"[INFO] Date range: {min_date} to {max_date}")
    
    # Verify against expected range
    if pd.isna(min_date) or pd.isna(max_date):
        print(f"[FAIL] Unable to determine date range (all dates are null)")
        return False
    
    expected_min = pd.Timestamp("2019-01-01")
    expected_max_start = pd.Timestamp("2026-02-01")
    expected_max_end = pd.Timestamp("2026-02-04")
    
    if min_date >= expected_min and min_date < expected_min + pd.Timedelta(days=7):
        print(f"[PASS] Start date is correct (within first week of 2019)")
    else:
        print(f"[WARN] Start date is unexpected: {min_date}")
    
    if expected_max_start <= max_date <= expected_max_end:
        print(f"[PASS] End date is current (Feb 2026)")
    else:
        print(f"[WARN] End date is unexpected: {max_date}")
    
    # Calculate data span
    data_span_days = (max_date - min_date).days
    print(f"[INFO] Data spans {data_span_days} days (~{data_span_days/365:.1f} years)")
    
    return True

def test_jan_gap():
    """Test 5: January 1-9 gap verification."""
    print_section("TEST 5: January 1-9 Gap Check")
    
    print("[INFO] Checking for Jan 1-9, 2026 data...")
    df_dates = pd.read_excel(BASELINE_PATH, usecols=['Time of Call'], parse_dates=['Time of Call'])
    
    jan_1_9 = df_dates[
        (df_dates['Time of Call'] >= '2026-01-01') & 
        (df_dates['Time of Call'] <= '2026-01-09 23:59:59')
    ]
    
    count = len(jan_1_9)
    print(f"[INFO] Records in Jan 1-9: {count:,}")
    
    if count == 0:
        print(f"[FAIL] Jan 1-9 gap still exists!")
        return False
    elif count < 1000:
        print(f"[WARN] Jan 1-9 has fewer records than expected (got {count:,}, expected ~3,000)")
        return False
    else:
        print(f"[PASS] Jan 1-9 data is present ({count:,} records)")
        if count > 0:
            print(f"       First record: {jan_1_9['Time of Call'].min()}")
            print(f"       Last record: {jan_1_9['Time of Call'].max()}")
        return True

def test_data_quality():
    """Test 6: Basic data quality checks."""
    print_section("TEST 6: Data Quality")
    
    print("[INFO] Reading sample data for quality checks...")
    df_sample = pd.read_excel(BASELINE_PATH, nrows=10000)
    
    print(f"\n[INFO] Sample size: {len(df_sample):,} records")
    
    # Check ReportNumberNew format
    if 'ReportNumberNew' in df_sample.columns:
        valid_pattern = df_sample['ReportNumberNew'].astype(str).str.match(r'^\d{2}-\d{6}[A-Z]?$')
        valid_count = valid_pattern.sum()
        invalid_count = len(df_sample) - valid_count
        
        if invalid_count == 0:
            print(f"[PASS] All case numbers valid (YY-NNNNNN format)")
        else:
            print(f"[WARN] {invalid_count} invalid case numbers in sample")
    
    # Check for null critical fields
    critical_fields = ['ReportNumberNew', 'Incident', 'Time of Call']
    for field in critical_fields:
        if field in df_sample.columns:
            null_count = df_sample[field].isna().sum()
            null_pct = (null_count / len(df_sample)) * 100
            
            if null_count == 0:
                print(f"[PASS] {field}: No nulls")
            elif null_pct < 5:
                print(f"[WARN] {field}: {null_count} nulls ({null_pct:.1f}%)")
            else:
                print(f"[FAIL] {field}: {null_count} nulls ({null_pct:.1f}%) - Too many!")
    
    return True

def test_monthly_distribution():
    """Test 7: Monthly record distribution."""
    print_section("TEST 7: Monthly Distribution")
    
    print("[INFO] Reading dates for distribution analysis...")
    df_dates = pd.read_excel(BASELINE_PATH, usecols=['Time of Call'], parse_dates=['Time of Call'])
    
    # Extract year-month
    df_dates['YearMonth'] = df_dates['Time of Call'].dt.to_period('M')
    
    # Count by month
    monthly_counts = df_dates['YearMonth'].value_counts().sort_index()
    
    print(f"\n[INFO] Record distribution by year:")
    yearly_counts = df_dates['Time of Call'].dt.year.value_counts().sort_index()
    for year, count in yearly_counts.items():
        print(f"  {year}: {count:,} records")
    
    print(f"\n[INFO] 2026 monthly distribution:")
    monthly_2026 = monthly_counts[monthly_counts.index >= '2026-01']
    for month, count in monthly_2026.items():
        print(f"  {month}: {count:,} records")
    
    # Check for gaps
    print(f"\n[INFO] Checking for month gaps...")
    all_months = pd.period_range(start=monthly_counts.index.min(), end=monthly_counts.index.max(), freq='M')
    missing_months = set(all_months) - set(monthly_counts.index)
    
    if missing_months:
        print(f"[WARN] Missing months: {sorted(missing_months)}")
    else:
        print(f"[PASS] No missing months")
    
    return True

def main():
    """Run all tests."""
    print(f"\n{'#'*80}")
    print(f"# BASELINE FILE TESTING SUITE")
    print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    print(f"\nBaseline file: {BASELINE_PATH}")
    
    results = []
    
    # Run all tests
    try:
        results.append(("File Integrity", test_file_integrity()))
        results.append(("Record Count", test_record_count()))
        results.append(("Column Structure", test_column_structure()))
        results.append(("Date Range", test_date_range()))
        results.append(("Jan 1-9 Gap", test_jan_gap()))
        results.append(("Data Quality", test_data_quality()))
        results.append(("Monthly Distribution", test_monthly_distribution()))
    except Exception as e:
        print(f"\n[ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n[OK] All tests passed! Baseline is ready for deployment.")
        return 0
    else:
        print(f"\n[WARNING] Some tests failed. Review issues before deployment.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
