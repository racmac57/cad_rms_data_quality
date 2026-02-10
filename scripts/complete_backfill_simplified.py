# Complete CAD Backfill - SIMPLIFIED (copy fields instead of mapping)
# Author: R. A. Carucci
# Date: 2026-02-09
# Purpose: Copy source fields to target field names, then append

import arcpy
import os
import sys
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_EXCEL = r"C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx\Sheet1$"
TEMP_GDB = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb"
CFSTABLE = os.path.join(TEMP_GDB, "CFStable")
ONLINE_SERVICE = "https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0"

TEMP_TABLE = os.path.join(TEMP_GDB, "tempcalls_selection")
TEMP_FC = os.path.join(TEMP_GDB, "tempcalls_with_geometry")

# ============================================================================
# LOGGING
# ============================================================================

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def log_separator():
    print("=" * 80)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def convert_text_to_datetime(in_table, text_field, output_field, time_format="yyyy-MM-dd HH:mm:ss"):
    """Convert text datetime to proper datetime field"""
    log(f"   Converting {text_field} -> {output_field}")
    
    arcpy.management.AddField(in_table, output_field, "DATE")
    
    python_format = time_format.replace("yyyy", "%Y").replace("MM", "%m").replace("dd", "%d").replace("HH", "%H").replace("mm", "%M").replace("ss", "%S")
    
    code_block = f"""
def parse_date(date_str):
    if date_str is None or date_str == '':
        return None
    try:
        from datetime import datetime
        return datetime.strptime(str(date_str), '{python_format}')
    except:
        return None
"""
    
    arcpy.management.CalculateField(
        in_table=in_table,
        field=output_field,
        expression=f"parse_date(!{text_field}!)",
        expression_type="PYTHON3",
        code_block=code_block
    )

def copy_field_values(in_table, source_field, target_field, field_type="TEXT", field_length=255):
    """Create a new field and copy values from source field"""
    log(f"   Copying {source_field} -> {target_field}")
    
    # Add target field
    if field_type == "TEXT":
        arcpy.management.AddField(in_table, target_field, "TEXT", field_length=field_length)
    else:
        arcpy.management.AddField(in_table, target_field, field_type)
    
    # Copy values
    arcpy.management.CalculateField(
        in_table=in_table,
        field=target_field,
        expression=f"!{source_field}!",
        expression_type="PYTHON3"
    )

# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def main():
    log_separator()
    log("COMPLETE CAD BACKFILL - SIMPLIFIED FIELD COPY APPROACH")
    log_separator()
    
    start_time = datetime.now()
    log(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # ====================================================================
        # STEP 1: Table Select (Filter records)
        # ====================================================================
        log("\n[STEP 1] Filtering records with Table Select...")
        
        where_clause = """Time_Of_Call IS NOT NULL 
            AND Incident NOT IN ('Assist Own Agency (Backup)', 'assist Own Agency (Backup)') 
            AND Disposition NOT IN ('Assisted', 'assisted', 'c', 'canceled', 'Canceled', 'Cancelled')"""
        
        if arcpy.Exists(TEMP_TABLE):
            arcpy.management.Delete(TEMP_TABLE)
        
        arcpy.analysis.TableSelect(
            in_table=INPUT_EXCEL,
            out_table=TEMP_TABLE,
            where_clause=where_clause
        )
        
        record_count = int(arcpy.management.GetCount(TEMP_TABLE)[0])
        log(f"✅ Selected {record_count:,} records")
        
        # ====================================================================
        # STEP 2: Convert DateTime Fields
        # ====================================================================
        log("\n[STEP 2] Converting datetime fields...")
        
        convert_text_to_datetime(TEMP_TABLE, "Time_Of_Call", "calldate")
        convert_text_to_datetime(TEMP_TABLE, "Time_Dispatched", "dispatchdate")
        convert_text_to_datetime(TEMP_TABLE, "Time_Out", "enroutedate")
        convert_text_to_datetime(TEMP_TABLE, "Time_In", "cleardate")
        
        log("✅ All datetime fields converted")
        
        # ====================================================================
        # STEP 3: Clean FullAddress2 field
        # ====================================================================
        log("\n[STEP 3] Cleaning FullAddress2 field...")
        
        arcpy.management.CalculateField(
            in_table=TEMP_TABLE,
            field="FullAddress2",
            expression="iif(left(trim($feature.FullAddress2),1)=='&'||left(trim($feature.FullAddress2),1)==',',trim(Mid($feature.FullAddress2,2)),trim($feature.FullAddress2))",
            expression_type="ARCADE"
        )
        
        log("✅ Address field cleaned")
        
        # ====================================================================
        # STEP 4: Calculate Response Time Fields
        # ====================================================================
        log("\n[STEP 4] Calculating response time metrics...")
        
        for field_name in ["dispatchtime", "queuetime", "cleartime", "responsetime"]:
            arcpy.management.AddField(TEMP_TABLE, field_name, "DOUBLE")
        
        arcpy.management.CalculateField(
            in_table=TEMP_TABLE,
            field="dispatchtime",
            expression="(DateDiff($feature.dispatchdate,$feature.calldate,'seconds') / 60)",
            expression_type="ARCADE",
            field_type="DOUBLE"
        )
        
        arcpy.management.CalculateField(
            in_table=TEMP_TABLE,
            field="queuetime",
            expression="(DateDiff($feature.enroutedate,$feature.dispatchdate,'seconds')/60)",
            expression_type="ARCADE",
            field_type="DOUBLE"
        )
        
        arcpy.management.CalculateField(
            in_table=TEMP_TABLE,
            field="cleartime",
            expression="(DateDiff($feature.cleardate,$feature.enroutedate,'seconds')/60)",
            expression_type="ARCADE",
            field_type="DOUBLE"
        )
        
        arcpy.management.CalculateField(
            in_table=TEMP_TABLE,
            field="responsetime",
            expression="$feature.dispatchtime+$feature.queuetime",
            expression_type="ARCADE",
            field_type="DOUBLE"
        )
        
        log("✅ Response times calculated")
        
        # ====================================================================
        # STEP 5: Add Date Attributes
        # ====================================================================
        log("\n[STEP 5] Adding date attributes...")
        
        arcpy.ca.AddDateAttributes(
            in_table=TEMP_TABLE,
            date_field="calldate",
            date_attributes=[
                ["DAY_FULL_NAME", "calldow"],
                ["DAY_OF_WEEK", "calldownum"],
                ["HOUR", "callhour"],
                ["MONTH", "callmonth"],
                ["YEAR", "callyear"]
            ]
        )
        
        log("✅ Date attributes added")
        
        # ====================================================================
        # STEP 6: Convert lat/lon to numeric and create geometry
        # ====================================================================
        log("\n[STEP 6] Creating point geometry from X/Y coordinates...")
        
        arcpy.management.AddField(TEMP_TABLE, "x_numeric", "DOUBLE")
        arcpy.management.AddField(TEMP_TABLE, "y_numeric", "DOUBLE")
        
        arcpy.management.CalculateField(
            in_table=TEMP_TABLE,
            field="x_numeric",
            expression="float(!longitude!)",
            expression_type="PYTHON3"
        )
        
        arcpy.management.CalculateField(
            in_table=TEMP_TABLE,
            field="y_numeric",
            expression="float(!latitude!)",
            expression_type="PYTHON3"
        )
        
        if arcpy.Exists(TEMP_FC):
            arcpy.management.Delete(TEMP_FC)
        
        arcpy.management.XYTableToPoint(
            in_table=TEMP_TABLE,
            out_feature_class=TEMP_FC,
            x_field="x_numeric",
            y_field="y_numeric",
            coordinate_system=arcpy.SpatialReference(4326)
        )
        
        point_count = int(arcpy.management.GetCount(TEMP_FC)[0])
        log(f"✅ Created {point_count:,} point features")
        
        # ====================================================================
        # STEP 7: Copy fields to CFStable-compatible names
        # ====================================================================
        log("\n[STEP 7] Creating CFStable-compatible field names...")
        
        # Copy source fields to target field names
        copy_field_values(TEMP_FC, "ReportNumberNew", "callid", "TEXT", 50)
        copy_field_values(TEMP_FC, "Incident", "calltype", "TEXT", 100)
        copy_field_values(TEMP_FC, "How_Reported", "callsource", "TEXT", 50)
        copy_field_values(TEMP_FC, "FullAddress2", "fulladdr", "TEXT", 255)
        
        # Copy x_numeric and y_numeric to x and y
        copy_field_values(TEMP_FC, "x_numeric", "x", "DOUBLE")
        copy_field_values(TEMP_FC, "y_numeric", "y", "DOUBLE")
        
        log("✅ Field names matched to CFStable schema")
        
        # ====================================================================
        # STEP 8: Append to LOCAL CFStable (no field mapping needed!)
        # ====================================================================
        log("\n[STEP 8] Appending to local CFStable...")
        
        arcpy.management.TruncateTable(CFSTABLE)
        log("   Truncated CFStable")
        
        # Now append without field mapping - field names match!
        arcpy.management.Append(
            inputs=TEMP_FC,
            target=CFSTABLE,
            schema_type="NO_TEST"
        )
        
        cfstable_count = int(arcpy.management.GetCount(CFSTABLE)[0])
        log(f"✅ CFStable now has {cfstable_count:,} records")
        
        # Verify data in CFStable
        log("   Verifying data in CFStable...")
        with arcpy.da.SearchCursor(CFSTABLE, ['callid', 'calltype', 'callsource']) as cursor:
            row = next(cursor)
            log(f"   Sample: callid={row[0]}, calltype={row[1]}, callsource={row[2]}")
        
        # ====================================================================
        # STEP 9: Push CFStable to Online Service
        # ====================================================================
        log("\n[STEP 9] Pushing CFStable to ArcGIS Online service...")
        log("⏱️  This may take 10-15 minutes...")
        
        append_start = datetime.now()
        
        arcpy.management.Append(
            inputs=CFSTABLE,
            target=ONLINE_SERVICE,
            schema_type="NO_TEST"
        )
        
        append_duration = (datetime.now() - append_start).total_seconds()
        log(f"✅ Online append complete in {append_duration:.1f} seconds")
        
        # ====================================================================
        # STEP 10: Verify Results
        # ====================================================================
        log("\n[STEP 10] Verifying final count...")
        
        final_count = int(arcpy.management.GetCount(ONLINE_SERVICE)[0])
        log(f"   Online service count: {final_count:,} records")
        
        # Verify data in online service
        log("   Verifying data in online service...")
        with arcpy.da.SearchCursor(ONLINE_SERVICE, ['callid', 'calltype', 'callsource']) as cursor:
            row = next(cursor)
            log(f"   Sample: callid={row[0]}, calltype={row[1]}, callsource={row[2]}")
        
        # ====================================================================
        # SUCCESS
        # ====================================================================
        total_duration = (datetime.now() - start_time).total_seconds()
        
        log_separator()
        log("✅ BACKFILL COMPLETED SUCCESSFULLY!")
        log_separator()
        log(f"\nTotal records: {final_count:,}")
        log(f"Total duration: {total_duration/60:.1f} minutes")
        log(f"All field transformations applied")
        log(f"Field copying approach (no mapping needed)")
        log(f"No live geocoding (used existing coordinates)")
        log_separator()
        
        return 0
        
    except Exception as e:
        log(f"\n❌ ERROR: {str(e)}", "ERROR")
        log(arcpy.GetMessages(2), "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())
