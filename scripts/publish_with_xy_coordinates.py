# 🕒 2026-02-09-18-45-00 (EST)
# cad_rms_data_quality/publish_with_xy_coordinates.py
# Author: R. A. Carucci
# Purpose: Publish CAD backfill using existing X/Y coordinates (bypasses live geocoding)

import arcpy
import os
import sys
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input file (staging location)
INPUT_EXCEL = r"C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx\Sheet1$"

# Output locations
TEMP_GDB = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb"
TEMP_TABLE = os.path.join(TEMP_GDB, "tempcalls_selection")
TEMP_FC = os.path.join(TEMP_GDB, "tempcalls_xy_points")
TARGET_TABLE = os.path.join(TEMP_GDB, "CFStable")

# Online feature service (from earlier)
ONLINE_SERVICE = "https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0"

# ============================================================================
# LOGGING
# ============================================================================

def log(message, level="INFO"):
    """Print timestamped message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def log_separator():
    print("=" * 80)

# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def main():
    """Simplified backfill workflow using X/Y coordinates"""
    
    log_separator()
    log("CAD BACKFILL - USING EXISTING X/Y COORDINATES")
    log_separator()
    
    start_time = datetime.now()
    log(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"User: {os.getenv('USERNAME')}")
    log(f"Machine: {os.getenv('COMPUTERNAME')}")
    
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
        log(f"✅ Table Select complete: {record_count:,} records")
        
        # ====================================================================
        # STEP 2: Convert latitude/longitude to numeric (if needed)
        # ====================================================================
        log("\n[STEP 2] Converting latitude/longitude to numeric fields...")
        
        # Add numeric fields
        arcpy.management.AddField(TEMP_TABLE, "x_numeric", "DOUBLE")
        arcpy.management.AddField(TEMP_TABLE, "y_numeric", "DOUBLE")
        
        # Convert text to numeric
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
        
        log(f"✅ Numeric fields created: x_numeric, y_numeric")
        
        # ====================================================================
        # STEP 3: XY Table To Point (Use numeric coordinates)
        # ====================================================================
        log("\n[STEP 3] Creating points from X/Y coordinates...")
        log("   Note: XYTableToPoint preserves ALL attribute fields from source table")
        
        if arcpy.Exists(TEMP_FC):
            arcpy.management.Delete(TEMP_FC)
        
        # XYTableToPoint automatically carries over all fields from the input table
        arcpy.management.XYTableToPoint(
            in_table=TEMP_TABLE,
            out_feature_class=TEMP_FC,
            x_field="x_numeric",  # Use the numeric fields we just created
            y_field="y_numeric",
            coordinate_system=arcpy.SpatialReference(4326)  # WGS 1984
        )
        
        point_count = int(arcpy.management.GetCount(TEMP_FC)[0])
        log(f"✅ XY Table To Point complete: {point_count:,} features with geometry")
        
        # Verify attributes were preserved
        fields = [f.name for f in arcpy.ListFields(TEMP_FC)]
        log(f"   Feature class contains {len(fields)} fields")
        
        # Check for critical fields
        critical_fields = ["ReportNumberNew", "Time_Of_Call", "How_Reported", "Incident"]
        missing = [f for f in critical_fields if f not in fields]
        if missing:
            raise Exception(f"Critical fields missing from feature class: {missing}")
        log(f"   ✅ All critical attribute fields present")
        
        # ====================================================================
        # STEP 4: Append to Online Service (No matching!)
        # ====================================================================
        log("\n[STEP 4] Appending to online service...")
        log("⏱️  This may take 10-15 minutes for 754K records...")
        
        append_start = datetime.now()
        
        arcpy.management.Append(
            inputs=TEMP_FC,
            target=ONLINE_SERVICE,
            schema_type="NO_TEST",
            field_mapping=None
        )
        
        append_duration = (datetime.now() - append_start).total_seconds()
        log(f"✅ Append complete in {append_duration:.1f} seconds")
        
        # ====================================================================
        # STEP 5: Verify Final Count
        # ====================================================================
        log("\n[STEP 5] Verifying final count...")
        
        final_count = int(arcpy.management.GetCount(ONLINE_SERVICE)[0])
        log(f"   Online service count: {final_count:,} records")
        
        # ====================================================================
        # SUCCESS!
        # ====================================================================
        total_duration = (datetime.now() - start_time).total_seconds()
        
        log_separator()
        log("✅ BACKFILL COMPLETED SUCCESSFULLY!")
        log_separator()
        log(f"\nTotal records: {final_count:,}")
        log(f"Total duration: {total_duration/60:.1f} minutes")
        log(f"No live geocoding performed (used existing X/Y coordinates)")
        log_separator()
        
        return 0
        
    except Exception as e:
        log(f"\n❌ ERROR: {str(e)}", "ERROR")
        log(arcpy.GetMessages(2), "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())
