import pandas as pd

# Check one of the source Excel files for multi-line values
print("Loading 2024 CAD source file...")
df = pd.read_excel(r'C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\yearly\2024\2024_CAD_ALL.xlsx')

print(f"Total records: {len(df):,}\n")

# Find records with newlines in How Reported
multi = df[df['How Reported'].astype(str).str.contains('\n', na=False)]
print(f"Records with multiple values (newline): {len(multi)}\n")

if len(multi) > 0:
    print("Multi-value combinations:")
    counts = multi['How Reported'].value_counts()
    for val, count in counts.items():
        print(f"  {repr(val)}: {count}")
    
    print("\n" + "="*80)
    print("SAMPLE RECORDS")
    print("="*80)
    for idx, row in multi.head(10).iterrows():
        print(f"\nCase: {row['ReportNumberNew']}")
        print(f"How Reported: {repr(row['How Reported'])}")
        print(f"Incident: {row['Incident']}")
        print(f"Time: {row['TimeOfCall']}")

# Also check for comma-separated values
comma = df[df['How Reported'].astype(str).str.contains(',', na=False)]
print(f"\n\nRecords with comma-separated values: {len(comma)}")
if len(comma) > 0:
    print(comma['How Reported'].value_counts())

# And slash-separated
slash = df[df['How Reported'].astype(str).str.contains('/', na=False)]
print(f"\n\nRecords with slash-separated values: {len(slash)}")
if len(slash) > 0:
    print(slash['How Reported'].value_counts())
