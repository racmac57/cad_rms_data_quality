"""
Quick quality check of exported CFSTable CSV
Verifies Phone/911 fix and data integrity
"""
import pandas as pd
from collections import Counter
import os
import sys

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("CFSTable CSV Quality Verification")
print("="*80)

csv_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\consolidation\output\CFSTable_2019_2026_FULL_20260203_231437.csv"

# File info
if os.path.exists(csv_path):
    file_size = os.path.getsize(csv_path)
    file_size_mb = file_size / (1024 * 1024)
    print(f"\n✅ File exists: {csv_path}")
    print(f"   Size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
else:
    print(f"\n❌ File not found: {csv_path}")
    exit(1)

print(f"\n📊 Loading CSV...")
df = pd.read_csv(csv_path, low_memory=False)

print(f"\n✅ CSV loaded successfully")
print(f"   Total records: {len(df):,}")
print(f"   Total columns: {len(df.columns)}")

# Column names
print(f"\n📋 Column Names:")
for i, col in enumerate(df.columns, 1):
    print(f"   {i:2d}. {col}")

# CRITICAL: Verify Phone/911 fix
print(f"\n" + "="*80)
print("🎯 PHONE/911 FIX VERIFICATION")
print("="*80)

if 'callsource' in df.columns:
    # Get value counts
    callsource_counts = df['callsource'].value_counts()
    
    print(f"\nTop 15 Call Source values:")
    print("-" * 60)
    for val, count in callsource_counts.head(15).items():
        pct = (count / len(df)) * 100
        print(f"  {str(val):25s}: {count:7,} ({pct:5.2f}%)")
    
    # Check for Phone/911
    phone_911_count = callsource_counts.get('Phone/911', 0)
    phone_count = callsource_counts.get('Phone', 0)
    nine_one_one_count = callsource_counts.get('9-1-1', 0)
    
    print("\n" + "="*80)
    print("VERIFICATION RESULTS:")
    print("="*80)
    
    if phone_911_count > 0:
        print(f"❌ PROBLEM: 'Phone/911' still exists: {phone_911_count:,} records")
        print(f"   The fix did NOT work!")
    else:
        print(f"✅ SUCCESS: No 'Phone/911' combined values found!")
    
    if phone_count > 0:
        print(f"✅ 'Phone' found: {phone_count:,} records ({(phone_count/len(df)*100):.2f}%)")
    else:
        print(f"⚠️  'Phone' not found - this is unexpected")
    
    if nine_one_one_count > 0:
        print(f"✅ '9-1-1' found: {nine_one_one_count:,} records ({(nine_one_one_count/len(df)*100):.2f}%)")
    else:
        print(f"⚠️  '9-1-1' not found - this is unexpected")
    
    # Calculate total that should have been combined
    total_separated = phone_count + nine_one_one_count
    print(f"\n📊 Total separated values: {total_separated:,} records")
    print(f"   (These were previously combined as 'Phone/911')")
    
else:
    print("❌ ERROR: 'callsource' column not found in CSV!")

# Date range check
print(f"\n" + "="*80)
print("📅 DATE RANGE VERIFICATION")
print("="*80)

if 'calldate' in df.columns:
    df['calldate'] = pd.to_datetime(df['calldate'], errors='coerce')
    
    min_date = df['calldate'].min()
    max_date = df['calldate'].max()
    
    print(f"   Earliest call: {min_date}")
    print(f"   Latest call:   {max_date}")
    print(f"   Date span:     {(max_date - min_date).days} days")

# Year distribution
if 'callyear' in df.columns:
    print(f"\n📊 Records by Year:")
    year_counts = df['callyear'].value_counts().sort_index()
    for year, count in year_counts.items():
        print(f"   {int(year)}: {count:7,} records")

# Check for nulls in critical fields
print(f"\n" + "="*80)
print("🔍 NULL VALUE CHECK (Critical Fields)")
print("="*80)

critical_fields = ['callid', 'calldate', 'callsource', 'disposition']
for field in critical_fields:
    if field in df.columns:
        null_count = df[field].isna().sum()
        null_pct = (null_count / len(df)) * 100
        status = "✅" if null_count == 0 else "⚠️"
        print(f"{status} {field:15s}: {null_count:7,} nulls ({null_pct:5.2f}%)")

print(f"\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"✅ CSV file is valid and readable")
print(f"✅ {len(df):,} records loaded")
print(f"✅ Date range: {min_date.date()} to {max_date.date()}")

if phone_911_count == 0 and phone_count > 0 and nine_one_one_count > 0:
    print(f"✅ Phone/911 fix VERIFIED - data is clean!")
else:
    print(f"⚠️  Phone/911 fix verification needs review")

print(f"\n🚀 CSV is ready for comprehensive validation!")
print("="*80)
