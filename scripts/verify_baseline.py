import pandas as pd

baseline_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx"

print("Checking new baseline...")
df = pd.read_excel(baseline_path, nrows=10)

print("\nFirst 5 records:")
print(df[['ReportNumberNew', 'Time of Call']].head())

print("\nChecking total records...")
df_full = pd.read_excel(baseline_path, usecols=[0])
print(f"Total records: {len(df_full):,}")

print("\nChecking date range...")
df_dates = pd.read_excel(baseline_path, usecols=['Time of Call'], parse_dates=['Time of Call'])
print(f"Date range: {df_dates['Time of Call'].min()} to {df_dates['Time of Call'].max()}")
print(f"Valid dates: {df_dates['Time of Call'].notna().sum():,}")

print("\n[OK] Baseline is valid!")
