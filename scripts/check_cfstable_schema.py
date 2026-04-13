# Quick diagnostic: Check CFStable schema
import arcpy

CFSTABLE = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb\CFStable"

print("\n" + "="*80)
print("CFStable Field Schema")
print("="*80)

if arcpy.Exists(CFSTABLE):
    fields = arcpy.ListFields(CFSTABLE)
    print(f"\nTotal fields: {len(fields)}\n")
    
    for field in fields:
        if field.type not in ['OID', 'Geometry', 'GlobalID']:
            print(f"  {field.name:30} | Type: {field.type:10} | Alias: {field.aliasName}")
    
    count = int(arcpy.management.GetCount(CFSTABLE)[0])
    print(f"\n\nRecord count in CFStable: {count:,}")
else:
    print("\n❌ CFStable not found")

print("\n" + "="*80)
