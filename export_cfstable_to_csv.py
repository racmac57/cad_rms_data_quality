"""
Export CFStable from ArcGIS Geodatabase to CSV
Fixes the failed export from earlier session
"""
import arcpy
import os
from datetime import datetime

print("="*80)
print("Exporting CFStable from Geodatabase to CSV")
print("="*80)

# Correct paths
gdb_table = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb\CFStable"
output_dir = r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\consolidation\output"

# Verify source exists
if not arcpy.Exists(gdb_table):
    print(f"❌ ERROR: Source table not found: {gdb_table}")
    exit(1)

print(f"✅ Source table found: {gdb_table}")

# Create output directory if needed
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"✅ Created output directory: {output_dir}")

# Get record count
result = arcpy.management.GetCount(gdb_table)
record_count = int(result[0])
print(f"✅ Source table has {record_count:,} records")

# Generate filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_name = f"CFSTable_2019_2026_FULL_{timestamp}.csv"
output_path = os.path.join(output_dir, output_name)

print(f"\n📤 Starting export...")
print(f"   Output: {output_path}")

# Export using TableToTable
try:
    arcpy.conversion.TableToTable(
        in_rows=gdb_table,
        out_path=output_dir,
        out_name=output_name
    )
    
    # Verify export
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"\n✅ Export complete!")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size_mb:.2f} MB")
        print(f"   Records: {record_count:,}")
    else:
        print(f"\n❌ ERROR: Export completed but file not found at: {output_path}")
        
except Exception as e:
    print(f"\n❌ ERROR during export: {str(e)}")
    exit(1)

print("\n" + "="*80)
print("Export successful! CSV is ready for validation.")
print("="*80)
