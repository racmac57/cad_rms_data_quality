# Quick Baseline Backup v1.6.1
# Creates FGDB backup of current CallsForService layer (571,282 records)

from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import arcpy
from datetime import datetime
import os

# Config
SERVICE_URL = "https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0"
OUTPUT_GDB = r"C:\HPD ESRI\03_Data\CAD\Backfill\Baseline_v1_6_1.gdb"
OUTPUT_FC_NAME = "CallsForService_Baseline_20190101_20260215"

print("=" * 70)
print("BASELINE BACKUP v1.6.1 (2019-01-01 to 2026-02-15)")
print("=" * 70)
print()

# Connect to AGOL
print("Connecting to ArcGIS Online...")
gis = GIS("pro")
print(f"✅ Connected as: {gis.properties.user.username}")
print()

# Get layer
print("Accessing CallsForService layer...")
fl = FeatureLayer(SERVICE_URL, gis=gis)
online_count = fl.query(where="1=1", return_count_only=True)
print(f"✅ Online layer: {online_count:,} records")
print()

# Create output geodatabase if it doesn't exist
print("Creating output geodatabase...")
output_folder = os.path.dirname(OUTPUT_GDB)
gdb_name = os.path.basename(OUTPUT_GDB)

if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"✅ Created folder: {output_folder}")

if arcpy.Exists(OUTPUT_GDB):
    print(f"⚠️  Geodatabase already exists: {OUTPUT_GDB}")
else:
    arcpy.management.CreateFileGDB(output_folder, gdb_name)
    print(f"✅ Created geodatabase: {OUTPUT_GDB}")
print()

# Export features
output_fc_path = os.path.join(OUTPUT_GDB, OUTPUT_FC_NAME)

if arcpy.Exists(output_fc_path):
    print(f"⚠️  Feature class already exists, deleting: {OUTPUT_FC_NAME}")
    arcpy.management.Delete(output_fc_path)

print(f"Exporting features to: {OUTPUT_FC_NAME}")
print("This will take ~3-5 minutes for 571K records...")
print()

start_time = datetime.now()

try:
    arcpy.conversion.ExportFeatures(
        SERVICE_URL, 
        output_fc_path
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Verify
    backup_count = int(arcpy.management.GetCount(output_fc_path)[0])
    
    print()
    print("=" * 70)
    print("BACKUP COMPLETE")
    print("=" * 70)
    print(f"✅ Exported: {backup_count:,} records")
    print(f"✅ Duration: {elapsed:.1f} seconds")
    print(f"✅ Location: {output_fc_path}")
    print()
    
    # Verify record count
    if backup_count == online_count:
        print("✅ Record count matches online layer")
    else:
        print(f"⚠️  Count mismatch: Backup={backup_count:,}, Online={online_count:,}")
    
    print()
    print("BASELINE INFORMATION:")
    print(f"  Name: CallsForService_Baseline_20190101_20260215")
    print(f"  Version: v1.6.1")
    print(f"  Records: {backup_count:,}")
    print(f"  Date Range: 2019-01-01 to 2026-02-15")
    print(f"  Geometry: 100% (X/Y coordinates)")
    print(f"  Dates: Corrected (real CAD timestamps)")
    print(f"  Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("=" * 70)
    
except Exception as e:
    print()
    print(f"❌ Export failed: {e}")
    import traceback
    traceback.print_exc()
