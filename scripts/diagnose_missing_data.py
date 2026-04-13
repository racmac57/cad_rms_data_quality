# Diagnostic: Why is the online table showing no data?
import arcpy

print("\n" + "="*80)
print("DIAGNOSTIC: Checking for missing attribute data")
print("="*80)

# Check the temp feature class that was appended
TEMP_FC = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb\tempcalls_xy_points"
ONLINE_SERVICE = "https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0"

# Step 1: Check fields in temp FC
print("\n[1] Checking temporary feature class fields...")
if arcpy.Exists(TEMP_FC):
    fields = [f.name for f in arcpy.ListFields(TEMP_FC) if f.type not in ['OID', 'Geometry']]
    print(f"    Total non-system fields: {len(fields)}")
    print(f"    Sample fields: {fields[:10]}")
    
    # Check if data exists in temp FC
    with arcpy.da.SearchCursor(TEMP_FC, ['OBJECTID', 'SHAPE@']) as cursor:
        row = next(cursor)
        print(f"    First record OBJECTID: {row[0]}")
        print(f"    First record has geometry: {row[1] is not None}")
else:
    print(f"    ❌ Temp FC not found")

# Step 2: Check online service
print("\n[2] Checking online service...")
try:
    online_count = int(arcpy.management.GetCount(ONLINE_SERVICE)[0])
    print(f"    Online record count: {online_count:,}")
    
    # Try to read a sample record
    online_fields = [f.name for f in arcpy.ListFields(ONLINE_SERVICE) if f.type not in ['OID', 'Geometry', 'GlobalID']]
    print(f"    Online service fields: {len(online_fields)}")
    print(f"    Sample online fields: {online_fields[:10]}")
    
    # Check if first record has attributes
    with arcpy.da.SearchCursor(ONLINE_SERVICE, ['OBJECTID'] + online_fields[:5]) as cursor:
        row = next(cursor)
        print(f"\n    First record sample:")
        print(f"      OBJECTID: {row[0]}")
        for i, field_name in enumerate(online_fields[:5], start=1):
            print(f"      {field_name}: {row[i]}")
            
except Exception as e:
    print(f"    ❌ Error reading online service: {e}")

print("\n" + "="*80)
