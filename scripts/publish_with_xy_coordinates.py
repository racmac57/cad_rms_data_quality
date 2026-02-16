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

# Heartbeat file for watchdog monitoring
HEARTBEAT_FILE = r"C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\heartbeat.txt"
OUT_DIR = r"C:\HPD ESRI\04_Scripts\_out"

# ============================================================================
# LOGGING & HEARTBEAT
# ============================================================================

def log(message, level="INFO"):
    """Print timestamped message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def log_separator():
    print("=" * 80)

def update_heartbeat(message=""):
    """Update heartbeat file for watchdog monitoring"""
    try:
        os.makedirs(os.path.dirname(HEARTBEAT_FILE), exist_ok=True)
        with open(HEARTBEAT_FILE, "w") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} | {message}\n")
    except Exception as e:
        log(f"Warning: Could not update heartbeat: {e}", "WARN")

# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def main():
    """Simplified backfill workflow using X/Y coordinates"""
    
    log_separator()
    log("CAD BACKFILL - USING EXISTING X/Y COORDINATES")
    log_separator()
    
    update_heartbeat("Script started")
    
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
        # STEP 2: Convert latitude/longitude to numeric (SAFE CONVERSION)
        # ====================================================================
        log("\n[STEP 2] Converting latitude/longitude to numeric fields (safe)...")
        
        update_heartbeat("Step 2: Converting coordinates to numeric")
        
        # Add numeric fields
        arcpy.management.AddField(TEMP_TABLE, "x_numeric", "DOUBLE")
        arcpy.management.AddField(TEMP_TABLE, "y_numeric", "DOUBLE")
        
        # Safe conversion function (handles NULL/blank/malformed)
        safe_float_code = """
def safe_float(val):
    '''Convert to float safely, return None for NULL/blank/malformed'''
    if val is None or val == '' or val == ' ':
        return None
    try:
        return float(val)
    except:
        return None
"""
        
        # Convert text to numeric with safe handling
        arcpy.management.CalculateField(
            in_table=TEMP_TABLE,
            field="x_numeric",
            expression="safe_float(!longitude!)",
            expression_type="PYTHON3",
            code_block=safe_float_code
        )
        
        arcpy.management.CalculateField(
            in_table=TEMP_TABLE,
            field="y_numeric",
            expression="safe_float(!latitude!)",
            expression_type="PYTHON3",
            code_block=safe_float_code
        )
        
        # Count NULL conversions
        null_count = 0
        with arcpy.da.SearchCursor(TEMP_TABLE, ["x_numeric", "y_numeric"]) as cursor:
            for row in cursor:
                if row[0] is None or row[1] is None:
                    null_count += 1
        
        if null_count > 0:
            log(f"⚠️  {null_count:,} records have NULL/malformed coordinates (will be skipped)", "WARN")
            # Write bad coord report
            os.makedirs(OUT_DIR, exist_ok=True)
            bad_coord_report = os.path.join(OUT_DIR, f"bad_coords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            arcpy.conversion.TableToTable(
                in_rows=TEMP_TABLE,
                out_path=OUT_DIR,
                out_name=os.path.basename(bad_coord_report),
                where_clause="x_numeric IS NULL OR y_numeric IS NULL"
            )
            log(f"   Bad coordinate report: {bad_coord_report}")
        
        log(f"✅ Numeric fields created: {record_count - null_count:,} valid, {null_count:,} NULL")
        
        # ====================================================================
        # STEP 3: XY Table To Point (Use numeric coordinates, SR 4326)
        # ====================================================================
        log("\n[STEP 3] Creating points from X/Y coordinates (WGS84/4326)...")
        log("   Note: XYTableToPoint preserves ALL attribute fields from source table")
        
        update_heartbeat("Step 3: XYTableToPoint (4326)")
        
        if arcpy.Exists(TEMP_FC):
            arcpy.management.Delete(TEMP_FC)
        
        # XYTableToPoint automatically carries over all fields from the input table
        # Filters out NULL coordinates automatically
        arcpy.management.XYTableToPoint(
            in_table=TEMP_TABLE,
            out_feature_class=TEMP_FC,
            x_field="x_numeric",
            y_field="y_numeric",
            coordinate_system=arcpy.SpatialReference(4326)  # WGS 1984
        )
        
        point_count = int(arcpy.management.GetCount(TEMP_FC)[0])
        log(f"✅ XY Table To Point complete: {point_count:,} features with geometry")
        log(f"   Records dropped due to NULL coords: {record_count - point_count:,}")
        
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
        # STEP 4: Project to Web Mercator (3857) for AGOL
        # ====================================================================
        log("\n[STEP 4] Projecting to Web Mercator (EPSG:3857)...")
        
        update_heartbeat("Step 4: Project to 3857")
        
        TEMP_FC_3857 = os.path.join(TEMP_GDB, "tempcalls_xy_points_3857")
        if arcpy.Exists(TEMP_FC_3857):
            arcpy.management.Delete(TEMP_FC_3857)
        
        arcpy.management.Project(
            in_dataset=TEMP_FC,
            out_dataset=TEMP_FC_3857,
            out_coor_system=arcpy.SpatialReference(3857)  # Web Mercator
        )
        
        projected_count = int(arcpy.management.GetCount(TEMP_FC_3857)[0])
        log(f"✅ Projected {projected_count:,} features to EPSG:3857")
        
        # Verify WKID
        spatial_ref = arcpy.Describe(TEMP_FC_3857).spatialReference
        log(f"   Spatial Reference: {spatial_ref.name} (WKID: {spatial_ref.factoryCode})")
        
        # ====================================================================
        # STEP 5: Append to Online Service (3857 geometry)
        # ====================================================================
        log("\n[STEP 5] Appending to online service...")
        log("⏱️  This may take 10-15 minutes for 754K records...")
        
        update_heartbeat("Step 5: Append to online service")
        
        append_start = datetime.now()
        
        arcpy.management.Append(
            inputs=TEMP_FC_3857,
            target=ONLINE_SERVICE,
            schema_type="NO_TEST",
            field_mapping=None
        )
        
        append_duration = (datetime.now() - append_start).total_seconds()
        log(f"✅ Append complete in {append_duration:.1f} seconds")
        
        update_heartbeat("Step 5 complete: Append finished")
        
        # ====================================================================
        # STEP 6: Post-Append Validation (Monitor Check)
        # ====================================================================
        log("\n[STEP 6] Running post-append validation...")
        
        update_heartbeat("Step 6: Post-append validation")
        
        # Call monitor script to validate geometry
        monitor_script = r"C:\HPD ESRI\04_Scripts\monitor_dashboard_health.py"
        propy_path = r"C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"
        
        import subprocess
        result = subprocess.run(
            [propy_path, monitor_script],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            log(f"❌ Post-append validation FAILED (exit code {result.returncode})", "ERROR")
            log(f"   Monitor output: {result.stdout}", "ERROR")
            raise Exception(f"Dashboard health validation failed after append (exit {result.returncode})")
        
        log(f"✅ Post-append validation passed (exit code 0)")
        
        # ====================================================================
        # STEP 7: Verify Final Count
        # ====================================================================
        log("\n[STEP 7] Verifying final count...")
        
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
