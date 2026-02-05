import pandas as pd
import sys

print("Loading baseline Excel file...")
print("(This may take 1-2 minutes for 724K records)\n")

try:
    df = pd.read_excel(
        r'C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx',
        sheet_name='Sheet1'
    )
    
    print(f"Loaded {len(df):,} records\n")
    
    # Check for Phone/911
    phone_911 = df[df['How Reported'].astype(str).str.contains('/', na=False)]
    
    print(f"Records with '/' in How Reported: {len(phone_911):,}")
    
    if len(phone_911) > 0:
        print("\nUnique values:")
        print(phone_911['How Reported'].value_counts())
        
        print("\nSample records:")
        for idx, row in phone_911.head(10).iterrows():
            print(f"  {row['ReportNumberNew']}: '{row['How Reported']}'")
    else:
        print("\nNO '/' patterns found in baseline!")
        print("Phone/911 must be created AFTER the baseline,")
        print("during the ArcGIS publishing process.")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
