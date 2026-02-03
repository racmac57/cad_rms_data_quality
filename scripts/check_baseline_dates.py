import pandas as pd

baseline_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx"

print("Loading baseline file...")
df = pd.read_excel(baseline_path, usecols=['ReportNumberNew', 'Time of Call'], parse_dates=['Time of Call'])

print(f"\nBaseline Stats:")
print(f"Total records: {len(df):,}")
print(f"Date range: {df['Time of Call'].min()} to {df['Time of Call'].max()}")

# Check January 2026
jan_2026 = df[(df['Time of Call'] >= '2026-01-01') & (df['Time of Call'] < '2026-02-01')]
print(f"\nJanuary 2026 records in baseline: {len(jan_2026):,}")

if len(jan_2026) > 0:
    print(f"First Jan record: {jan_2026['Time of Call'].min()}")
    print(f"Last Jan record: {jan_2026['Time of Call'].max()}")
    
    # Check Jan 1-9 specifically
    jan_1_9 = df[(df['Time of Call'] >= '2026-01-01') & (df['Time of Call'] <= '2026-01-09 23:59:59')]
    print(f"\nJan 1-9 records: {len(jan_1_9):,}")
    
    if len(jan_1_9) > 0:
        print(f"First: {jan_1_9['Time of Call'].min()}")
        print(f"Last: {jan_1_9['Time of Call'].max()}")

# Check February 2026
feb_2026 = df[(df['Time of Call'] >= '2026-02-01') & (df['Time of Call'] < '2026-03-01')]
print(f"\nFebruary 2026 records in baseline: {len(feb_2026):,}")
