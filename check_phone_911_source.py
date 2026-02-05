import pandas as pd

print("Checking for Phone/911 in raw consolidated CSV...")
df = pd.read_csv(r'C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\01_raw\2019_to_2026_01_30_CAD.csv', low_memory=False)

# Check for exact Phone/911
phone_911_exact = df[df['How Reported'].astype(str).str.upper() == 'PHONE/911']
print(f"Exact 'PHONE/911' match: {len(phone_911_exact)} records")

# Check for any pattern
phone_911_pattern = df[df['How Reported'].astype(str).str.contains('/', na=False)]
print(f"Any value with '/': {len(phone_911_pattern)} records")

if len(phone_911_pattern) > 0:
    print("\nValues containing '/':")
    print(phone_911_pattern['How Reported'].value_counts())
else:
    print("\n✅ NO '/' patterns in raw consolidated CSV")
    print("   Phone/911 is being CREATED during normalization/processing")
