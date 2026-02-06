import pandas as pd

file_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\monthly\2026\2026_01_CAD.xlsx"

print("Checking January 2026 file...")
df = pd.read_excel(file_path, usecols=['ReportNumberNew', 'Time of Call'], parse_dates=['Time of Call'])

print(f"\nTotal records: {len(df):,}")
print(f"Date range: {df['Time of Call'].min()} to {df['Time of Call'].max()}")

# Check Jan 1-9 gap
gap_data = df[(df['Time of Call'] >= '2026-01-01') & (df['Time of Call'] <= '2026-01-09 23:59:59')]
print(f"\nJan 1-9 records: {len(gap_data):,}")

if len(gap_data) > 0:
    print(f"First record: {gap_data['Time of Call'].min()}")
    print(f"Last record in gap: {gap_data['Time of Call'].max()}")
    print(f"\n[OK] Gap data IS present - ready to merge!")
else:
    print("\n[X] Gap data NOT found")
