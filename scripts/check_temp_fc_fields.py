# Check what fields exist in temp feature class
import arcpy

TEMP_FC = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb\tempcalls_with_geometry"

print("\n" + "="*80)
print("Fields in tempcalls_with_geometry")
print("="*80)

if arcpy.Exists(TEMP_FC):
    fields = [f.name for f in arcpy.ListFields(TEMP_FC) if f.type not in ['OID', 'Geometry', 'GlobalID']]
    print(f"\nTotal non-system fields: {len(fields)}\n")
    
    # Show all fields
    for field in fields:
        print(f"  {field}")
    
    # Check if our expected source fields exist
    print("\n" + "="*80)
    print("Checking for expected source fields:")
    print("="*80)
    
    expected = ['ReportNumberNew', 'Incident', 'How_Reported', 'FullAddress2', 
                'calldate', 'dispatchdate', 'x_numeric', 'y_numeric']
    
    for field_name in expected:
        exists = field_name in fields
        status = "✅" if exists else "❌"
        print(f"  {status} {field_name}")
    
    # Sample a record to see what data is there
    print("\n" + "="*80)
    print("Sample record (first 10 fields with non-NULL values):")
    print("="*80)
    
    with arcpy.da.SearchCursor(TEMP_FC, "*") as cursor:
        row = next(cursor)
        field_names = cursor.fields
        
        count = 0
        for i, (field_name, value) in enumerate(zip(field_names, row)):
            if value is not None and count < 15 and field_name not in ['OBJECTID', 'SHAPE', 'Shape']:
                print(f"  {field_name}: {value}")
                count += 1
else:
    print(f"\n❌ Feature class not found: {TEMP_FC}")

print("\n" + "="*80)
