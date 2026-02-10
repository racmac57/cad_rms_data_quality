# Quick diagnostic: Check what fields are in the temp feature class
import arcpy

TEMP_FC = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb\tempcalls_xy_points"

print("\n" + "="*80)
print("DIAGNOSTIC: Fields in tempcalls_xy_points")
print("="*80)

if arcpy.Exists(TEMP_FC):
    fields = arcpy.ListFields(TEMP_FC)
    print(f"\nTotal fields: {len(fields)}\n")
    
    for field in fields:
        print(f"  {field.name:40} | Type: {field.type:15} | Length: {field.length}")
    
    # Check record count
    count = int(arcpy.management.GetCount(TEMP_FC)[0])
    print(f"\nRecord count: {count:,}")
    
    # Sample first record's attributes
    print("\n" + "="*80)
    print("SAMPLE RECORD (first 10 fields with values):")
    print("="*80)
    
    with arcpy.da.SearchCursor(TEMP_FC, "*") as cursor:
        row = next(cursor)
        field_names = cursor.fields
        
        count = 0
        for i, (field_name, value) in enumerate(zip(field_names, row)):
            if value is not None and count < 10:
                print(f"  {field_name}: {value}")
                count += 1
else:
    print(f"\n❌ Feature class not found: {TEMP_FC}")

print("\n" + "="*80)
