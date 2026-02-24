# 🕒 2026-02-16-17-20-00 (EST)
# cad_rms_data_quality/Geocode_Baseline_With_NJ_Locator.py
# Author: R. A. Carucci
# Purpose: Geocode CAD baseline using NJ_Geocode.loc and add lat/lon to Excel

import arcpy
import os
import time
from datetime import datetime

# Paths
INPUT_EXCEL = r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline_20190101_20260215.xlsx"
OUTPUT_EXCEL = r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline_GEOCODED.xlsx"
NJ_LOCATOR = r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\GeographicData\NJ_Geocode\NJ_Geocode.loc"
WORKSPACE = r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\temp_geocode.gdb"

# Create temp geodatabase if needed
if not arcpy.Exists(WORKSPACE):
    arcpy.management.CreateFileGDB(os.path.dirname(WORKSPACE), os.path.basename(WORKSPACE))

arcpy.env.workspace = WORKSPACE
arcpy.env.overwriteOutput = True

print("="*80)
print("GEOCODING CAD BASELINE WITH NJ_GEOCODE.LOC")
print("="*80)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Input: {INPUT_EXCEL}")
print(f"Locator: {NJ_LOCATOR}")
print()

# Step 1: Import Excel to table
print("[STEP 1] Importing Excel to geodatabase table...")
start_time = time.time()

temp_table = os.path.join(WORKSPACE, "CAD_Baseline")
arcpy.conversion.TableToTable(INPUT_EXCEL, WORKSPACE, "CAD_Baseline")

record_count = int(arcpy.management.GetCount(temp_table)[0])
print(f"✅ Imported {record_count:,} records")
print(f"   Duration: {time.time() - start_time:.1f}s")
print()

# Step 2: Geocode addresses
print("[STEP 2] Geocoding addresses with NJ_Geocode.loc...")
print("   This will take ~30-45 minutes for 758K records")
print("   Progress updates every 50K records...")
start_time = time.time()

geocoded_fc = os.path.join(WORKSPACE, "CAD_Geocoded")

# Geocode with NJ locator
arcpy.geocoding.GeocodeAddresses(
    in_table=temp_table,
    address_locator=NJ_LOCATOR,
    in_address_fields="'Single Line Input' FullAddress2",
    out_feature_class=geocoded_fc,
    out_relationship_type="STATIC"
)

geocoded_count = int(arcpy.management.GetCount(geocoded_fc)[0])
match_rate = (geocoded_count / record_count) * 100

print(f"✅ Geocoded {geocoded_count:,} addresses ({match_rate:.1f}% match rate)")
print(f"   Duration: {time.time() - start_time:.1f}s")
print()

# Step 3: Add lat/lon fields to geocoded FC
print("[STEP 3] Calculating latitude/longitude from geometry...")
start_time = time.time()

arcpy.management.AddField(geocoded_fc, "latitude", "DOUBLE")
arcpy.management.AddField(geocoded_fc, "longitude", "DOUBLE")

arcpy.management.CalculateGeometryAttributes(
    geocoded_fc,
    [["latitude", "POINT_Y"], ["longitude", "POINT_X"]],
    coordinate_system=arcpy.SpatialReference(4326)  # WGS84
)

print(f"✅ Latitude/longitude calculated")
print(f"   Duration: {time.time() - start_time:.1f}s")
print()

# Step 4: Export to Excel with coordinates
print("[STEP 4] Exporting to Excel with coordinates...")
start_time = time.time()

arcpy.conversion.TableToExcel(geocoded_fc, OUTPUT_EXCEL)

print(f"✅ Excel created: {OUTPUT_EXCEL}")
print(f"   Duration: {time.time() - start_time:.1f}s")
print()

# Step 5: Quality check
print("[STEP 5] Quality check on coordinates...")
null_count = 0
sample_coords = []

with arcpy.da.SearchCursor(geocoded_fc, ["ReportNumberNew", "latitude", "longitude"]) as cursor:
    for i, row in enumerate(cursor):
        if i < 5:  # Sample first 5
            sample_coords.append((row[0], row[1], row[2]))
        
        if row[1] is None or row[2] is None:
            null_count += 1
        
        if i >= 1000:  # Check first 1000
            break

null_pct = (null_count / 1000) * 100

print("Sample coordinates:")
for call_id, lat, lon in sample_coords:
    if lat and lon:
        print(f"  {call_id}: {lat:.6f}, {lon:.6f}")
    else:
        print(f"  {call_id}: NULL, NULL")

print(f"\nNULL rate (first 1000): {null_pct:.1f}%")

if null_pct > 10:
    print("⚠️  WARNING: >10% NULL coordinates - geocoding may have issues")
else:
    print("✅ Good geocoding coverage")

print()
print("="*80)
print(f"COMPLETE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print()
print("NEXT STEPS:")
print("1. Verify OUTPUT_EXCEL has coordinates populated")
print("2. Convert OUTPUT_EXCEL to CSV")
print("3. Copy CSV to RDP staging")
print("4. Run backfill script")
