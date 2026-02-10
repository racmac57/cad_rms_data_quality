# 🕒 2026-02-09-09-00-00
# CAD_Backfill_Option_C/backup_current_layer.py
# Author: R. A. Carucci
# Purpose: Backup current CFStable layer (561,740 records) to local geodatabase before truncate operation

import arcpy
import os
import sys
from datetime import datetime
import hashlib

# ============================================================================
# CONFIGURATION - UPDATE SERVICE_URL FROM get_service_url.py OUTPUT
# ============================================================================

SERVICE_URL = "PASTE_URL_HERE"  # Get this from get_service_url.py output

BACKUP_FOLDER = r"C:\HPD ESRI\00_Backups\CAD_Backfill_20260209"
BACKUP_GDB_NAME = "Backup.gdb"
BACKUP_FC_NAME = "CFStable_PreBackfill_561740"
EXPECTED_COUNT = 561740  # Current dashboard count

# ============================================================================
# LOGGING SETUP
# ============================================================================

LOG_FILE = os.path.join(BACKUP_FOLDER, "backup_log.txt")

def log(message, level="INFO"):
    """Write message to console and log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    print(log_message)
    
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_message + "\n")

def log_separator():
    """Print visual separator"""
    separator = "=" * 80
    print(separator)
    with open(LOG_FILE, "a") as f:
        f.write(separator + "\n")

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_service_url():
    """Ensure service URL has been configured"""
    if "PASTE_URL_HERE" in SERVICE_URL:
        log("❌ ERROR: SERVICE_URL not configured!", "ERROR")
        log("   Run get_service_url.py first, then paste the URL into this script", "ERROR")
        return False
    
    log(f"✅ Service URL configured: {SERVICE_URL}")
    return True

def test_connection():
    """Test connection to online service"""
    log("Testing connection to online service...")
    
    try:
        desc = arcpy.Describe(SERVICE_URL)
        log(f"✅ Connection successful")
        log(f"   Data type: {desc.dataType}")
        log(f"   Shape type: {desc.shapeType if hasattr(desc, 'shapeType') else 'N/A'}")
        return True
    except Exception as e:
        log(f"❌ Connection failed: {str(e)}", "ERROR")
        log("   Verify the SERVICE_URL is correct and you're connected to the internet", "ERROR")
        return False

def get_current_count():
    """Get current record count from online service"""
    log("Querying current record count...")
    
    try:
        count = int(arcpy.management.GetCount(SERVICE_URL)[0])
        log(f"✅ Current online count: {count:,} records")
        return count
    except Exception as e:
        log(f"❌ Failed to get count: {str(e)}", "ERROR")
        return None

def calculate_checksum(fc_path):
    """Calculate checksum of feature class for integrity verification"""
    log("Calculating backup checksum...")
    
    try:
        # Count records
        count = int(arcpy.management.GetCount(fc_path)[0])
        
        # Sample 100 records for hash (full hash would be too slow)
        sample_size = min(100, count)
        hash_md5 = hashlib.md5()
        
        fields = ["OBJECTID", "ReportNumberNew"]  # Use key fields
        sample_interval = max(1, count // sample_size)
        
        with arcpy.da.SearchCursor(fc_path, fields) as cursor:
            for i, row in enumerate(cursor):
                if i % sample_interval == 0:
                    hash_md5.update(str(row).encode())
        
        checksum = hash_md5.hexdigest()
        log(f"✅ Checksum: {checksum} (based on {sample_size} sample records)")
        return checksum
    except Exception as e:
        log(f"⚠️  Checksum calculation failed: {str(e)}", "WARNING")
        return None

# ============================================================================
# BACKUP FUNCTIONS
# ============================================================================

def create_backup_geodatabase():
    """Create backup geodatabase if it doesn't exist"""
    backup_gdb_path = os.path.join(BACKUP_FOLDER, BACKUP_GDB_NAME)
    
    if arcpy.Exists(backup_gdb_path):
        log(f"✅ Geodatabase already exists: {backup_gdb_path}")
        return backup_gdb_path
    
    log(f"Creating backup geodatabase: {backup_gdb_path}")
    
    try:
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        arcpy.management.CreateFileGDB(BACKUP_FOLDER, BACKUP_GDB_NAME)
        log(f"✅ Geodatabase created successfully")
        return backup_gdb_path
    except Exception as e:
        log(f"❌ Failed to create geodatabase: {str(e)}", "ERROR")
        return None

def export_to_backup(backup_gdb_path):
    """Export current online layer to backup geodatabase"""
    backup_fc_path = os.path.join(backup_gdb_path, BACKUP_FC_NAME)
    
    # Delete existing backup if present
    if arcpy.Exists(backup_fc_path):
        log(f"⚠️  Existing backup found, deleting: {backup_fc_path}", "WARNING")
        arcpy.management.Delete(backup_fc_path)
    
    log(f"Exporting {SERVICE_URL} to {backup_fc_path}...")
    log("⏱️  This may take 5-10 minutes for 561K records...")
    
    start_time = datetime.now()
    
    try:
        arcpy.conversion.ExportFeatures(SERVICE_URL, backup_fc_path)
        
        duration = (datetime.now() - start_time).total_seconds()
        log(f"✅ Export completed in {duration:.1f} seconds")
        
        return backup_fc_path
    except Exception as e:
        log(f"❌ Export failed: {str(e)}", "ERROR")
        return None

def validate_backup(backup_fc_path, expected_count):
    """Validate backup integrity"""
    log("Validating backup integrity...")
    
    # Check existence
    if not arcpy.Exists(backup_fc_path):
        log(f"❌ Backup does not exist: {backup_fc_path}", "ERROR")
        return False
    
    # Check record count
    try:
        backup_count = int(arcpy.management.GetCount(backup_fc_path)[0])
        log(f"   Backup count: {backup_count:,} records")
        log(f"   Expected: {expected_count:,} records")
        
        if backup_count != expected_count:
            log(f"❌ Count mismatch! Expected {expected_count:,}, got {backup_count:,}", "ERROR")
            return False
        
        log(f"✅ Record count matches expected value")
        
        # Check for required fields
        field_names = [f.name for f in arcpy.ListFields(backup_fc_path)]
        required_fields = ["OBJECTID", "ReportNumberNew", "Time_Of_Call", "How_Reported"]
        
        missing_fields = [f for f in required_fields if f not in field_names]
        if missing_fields:
            log(f"⚠️  Missing expected fields: {missing_fields}", "WARNING")
        else:
            log(f"✅ All required fields present")
        
        # Sample data check
        log("Checking sample records...")
        with arcpy.da.SearchCursor(backup_fc_path, ["OBJECTID", "ReportNumberNew"], 
                                     sql_clause=(None, "ORDER BY OBJECTID FETCH FIRST 5 ROWS ONLY")) as cursor:
            for i, row in enumerate(cursor):
                log(f"   Sample {i+1}: OBJECTID={row[0]}, ReportNumberNew={row[1]}")
        
        log("✅ Backup validation passed")
        return True
        
    except Exception as e:
        log(f"❌ Validation failed: {str(e)}", "ERROR")
        return False

def save_backup_metadata(backup_fc_path, checksum):
    """Save backup metadata for future reference"""
    metadata_file = os.path.join(BACKUP_FOLDER, "backup_metadata.txt")
    
    try:
        backup_count = int(arcpy.management.GetCount(backup_fc_path)[0])
        
        metadata = f"""CAD Backfill Backup Metadata
================================
Backup Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Source: {SERVICE_URL}
Backup Path: {backup_fc_path}
Record Count: {backup_count:,}
Checksum: {checksum or "N/A"}
Expected Count: {EXPECTED_COUNT:,}
Status: {"✅ VALID" if backup_count == EXPECTED_COUNT else "❌ COUNT MISMATCH"}

Purpose: Pre-truncate backup before loading 754,409 historical records
Retention: Keep until backfill verified successful (at least 1 week)
"""
        
        with open(metadata_file, "w") as f:
            f.write(metadata)
        
        log(f"✅ Metadata saved: {metadata_file}")
        
    except Exception as e:
        log(f"⚠️  Failed to save metadata: {str(e)}", "WARNING")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main backup execution"""
    log_separator()
    log("CAD BACKFILL - PHASE 1: BACKUP CURRENT LAYER")
    log_separator()
    
    log(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"User: {os.getenv('USERNAME')}")
    log(f"Machine: {os.getenv('COMPUTERNAME')}\n")
    
    # Step 1: Validate configuration
    log("STEP 1: Validating configuration...")
    if not validate_service_url():
        sys.exit(1)
    
    # Step 2: Test connection
    log("\nSTEP 2: Testing connection to online service...")
    if not test_connection():
        sys.exit(1)
    
    # Step 3: Get current count
    log("\nSTEP 3: Querying current record count...")
    current_count = get_current_count()
    if current_count is None:
        sys.exit(1)
    
    if current_count != EXPECTED_COUNT:
        log(f"⚠️  WARNING: Current count ({current_count:,}) differs from expected ({EXPECTED_COUNT:,})", "WARNING")
        response = input(f"\nContinue with backup of {current_count:,} records? (yes/no): ")
        if response.lower() != "yes":
            log("Backup cancelled by user")
            sys.exit(0)
    
    # Step 4: Create backup geodatabase
    log("\nSTEP 4: Creating backup geodatabase...")
    backup_gdb_path = create_backup_geodatabase()
    if not backup_gdb_path:
        sys.exit(1)
    
    # Step 5: Export to backup
    log("\nSTEP 5: Exporting current layer to backup...")
    backup_fc_path = export_to_backup(backup_gdb_path)
    if not backup_fc_path:
        sys.exit(1)
    
    # Step 6: Validate backup
    log("\nSTEP 6: Validating backup integrity...")
    if not validate_backup(backup_fc_path, current_count):
        log("❌ BACKUP VALIDATION FAILED - DO NOT PROCEED WITH TRUNCATE!", "ERROR")
        sys.exit(1)
    
    # Step 7: Calculate checksum
    log("\nSTEP 7: Calculating backup checksum...")
    checksum = calculate_checksum(backup_fc_path)
    
    # Step 8: Save metadata
    log("\nSTEP 8: Saving backup metadata...")
    save_backup_metadata(backup_fc_path, checksum)
    
    # Success!
    log_separator()
    log("✅ BACKUP COMPLETED SUCCESSFULLY")
    log_separator()
    log(f"\nBackup Location: {backup_fc_path}")
    log(f"Record Count: {current_count:,}")
    log(f"Checksum: {checksum or 'N/A'}")
    log(f"\n⚠️  DO NOT DELETE THIS BACKUP until backfill is verified successful!")
    log(f"\nNext step: Run truncate_online_layer.py")
    log_separator()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\n\n❌ Backup cancelled by user (Ctrl+C)", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"\n\n❌ Unexpected error: {str(e)}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        sys.exit(1)
