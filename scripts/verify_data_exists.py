# Diagnostic: Check if CFStable has actual data
import arcpy

CFSTABLE = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb\CFStable"
ONLINE_SERVICE = "https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0"

print("\n" + "="*80)
print("DIAGNOSTIC: Checking if CFStable has actual data")
print("="*80)

# Check CFStable
print("\n[1] CFStable Sample Record:")
try:
    fields_to_check = ['callid', 'calltype', 'callsource', 'fulladdr', 'calldate']
    with arcpy.da.SearchCursor(CFSTABLE, fields_to_check) as cursor:
        row = next(cursor)
        for i, field_name in enumerate(fields_to_check):
            print(f"   {field_name}: {row[i]}")
except Exception as e:
    print(f"   ❌ Error reading CFStable: {e}")

# Check Online Service
print("\n[2] Online Service Sample Record:")
try:
    fields_to_check = ['callid', 'calltype', 'callsource', 'fulladdr', 'calldate']
    with arcpy.da.SearchCursor(ONLINE_SERVICE, fields_to_check) as cursor:
        row = next(cursor)
        for i, field_name in enumerate(fields_to_check):
            print(f"   {field_name}: {row[i]}")
except Exception as e:
    print(f"   ❌ Error reading online service: {e}")

print("\n" + "="*80)
