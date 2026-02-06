import pandas as pd

# Load raw consolidated data
print("Loading raw CAD data...")
df = pd.read_csv(r'C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\01_raw\2019_to_2026_01_30_CAD.csv', low_memory=False)

print(f"Total records: {len(df):,}\n")

# Get all How Reported values
vals = df['How Reported'].value_counts()
print(f"Total unique How Reported values: {len(vals)}\n")

# Export to file for review
with open('how_reported_full_analysis.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total records: {len(df):,}\n")
    f.write(f"Total unique values: {len(vals)}\n\n")
    f.write("="*80 + "\n")
    f.write("ALL HOW REPORTED VALUES\n")
    f.write("="*80 + "\n\n")
    
    for val, count in vals.items():
        pct = (count / len(df)) * 100
        f.write(f"{repr(val):40s} : {count:>8,} ({pct:>6.2f}%)\n")

print("Analysis written to: how_reported_full_analysis.txt")

# Also check for specific patterns
print("\nChecking for Phone+911 combinations...")
phone_911_patterns = df[df['How Reported'].astype(str).str.contains('Phone.*911|911.*Phone', case=False, regex=True, na=False)]
print(f"Records with Phone+911 pattern: {len(phone_911_patterns)}")

if len(phone_911_patterns) > 0:
    print("\nPhone+911 patterns found:")
    print(phone_911_patterns['How Reported'].value_counts())
