# 🕒 2026-02-09-09-00-00
# CAD_Backfill_Option_C/restore_from_backup.py
# Author: R. A. Carucci
# Purpose: Emergency restore from backup if truncate or backfill fails - ROLLBACK OPERATION

import arcpy
import os
import sys
from datetime import datetime

# ============================================================================
# CONFIGURATION - MUST MATCH backup_current_layer.py
# ============================================================================

SERVICE_URL = "PASTE_URL_HERE"  # Same URL from backup script

BACKUP_FOLDER = r"C:\HPD ESRI\00_Backups\CAD_Backfill_20260209"
BACKUP_GDB_NAME = "Backup.gdb"
BACKUP_FC_NAME = "CFStable_PreBackfill_561740"
EXPECTED_BACKUP_COUNT = 561740

# ============================================================================
# LOGGING SETUP
# ============================================================================

LOG_FILE = os.path.join(BACKUP_FOLDER, "restore_log.txt")

def log(message, level="INFO"):
    """Write message to console and log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    print(log_message)
    
    with open(LOG_FILE, "a") as f:
        f.write(log_message + "\n")

def log_separator():
    """Print visual separator"""
    separator = "=" * 80
    print(separator)
    with open(LOG_FILE, "a") as f:
        f.write(separator + "\n")

# ============================================================================
# RESTORE FUNCTIONS
# ============================================================================

def validate_backup_exists():
    """Verify backup is available for restore"""
    log("Validating backup availability...")
    
    backup_gdb_path = os.path.join(BACKUP_FOLDER, BACKUP_GDB_NAME)
    backup_fc_path = os.path.join(backup_gdb_path, BACKUP_FC_NAME)
    
    if not arcpy.Exists(backup_fc_path):
        log(f"❌ ABORT: Backup not found at {backup_fc_path}", "ERROR")
        log("   Cannot restore without backup!", "ERROR")
        return None
    
    try:
        backup_count = int(arcpy.management.GetCount(backup_fc_path)[0])
        log(f"✅ Backup found: {backup_fc_path}")
        log(f"   Backup count: {backup_count:,} records")
        
        if backup_count != EXPECTED_BACKUP_COUNT:
            log(f"⚠️  WARNING: Backup count ({backup_count:,}) differs from expected ({EXPECTED_BACKUP_COUNT:,})", "WARNING")
        
        return backup_fc_path
        
    except Exception as e:
        log(f"❌ Failed to validate backup: {str(e)}", "ERROR")
        return None

def check_online_status():
    """Check current state of online layer"""
    log("Checking current online layer status...")
    
    try:
        current_count = int(arcpy.management.GetCount(SERVICE_URL)[0])
        log(f"   Current online count: {current_count:,} records")
        return current_count
    except Exception as e:
        log(f"❌ Cannot connect to online service: {str(e)}", "ERROR")
        return None

def truncate_current_data():
    """Truncate current data before restore (ensures clean slate)"""
    log("\n⚠️  Truncating current online data before restore...")
    
    try:
        arcpy.management.TruncateTable(SERVICE_URL)
        
        # Verify truncation
        current_count = int(arcpy.management.GetCount(SERVICE_URL)[0])
        if current_count != 0:
            log(f"❌ Truncation failed! Still has {current_count:,} records", "ERROR")
            return False
        
        log(f"✅ Current data truncated (0 records)")
        return True
        
    except Exception as e:
        log(f"❌ Truncation failed: {str(e)}", "ERROR")
        return False

def append_backup_data(backup_fc_path):
    """Append backup data to online layer"""
    log("\nRestoring backup data to online layer...")
    log("⏱️  This may take 5-10 minutes for 561K records...")
    
    start_time = datetime.now()
    
    try:
        # Use Append tool (not ExportFeatures) to restore to existing service
        arcpy.management.Append(
            backup_fc_path,
            SERVICE_URL,
            schema_type="NO_TEST",  # Assume schema matches
            field_mapping=None
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        log(f"✅ Restore completed in {duration:.1f} seconds")
        
        return True
        
    except Exception as e:
        log(f"❌ Restore failed: {str(e)}", "ERROR")
        log(arcpy.GetMessages(2), "ERROR")
        return False

def verify_restore_count(expected_count):
    """Verify restored record count matches backup"""
    log("\nVerifying restore integrity...")
    
    try:
        restored_count = int(arcpy.management.GetCount(SERVICE_URL)[0])
        log(f"   Restored count: {restored_count:,}")
        log(f"   Expected: {expected_count:,}")
        
        if restored_count != expected_count:
            log(f"⚠️  WARNING: Count mismatch! Expected {expected_count:,}, got {restored_count:,}", "WARNING")
            log("   Some records may be missing - review backup source", "WARNING")
            return False
        
        log(f"✅ Restore verified: {restored_count:,} records")
        return True
        
    except Exception as e:
        log(f"❌ Verification failed: {str(e)}", "ERROR")
        return False

def save_restore_record():
    """Save record of restore operation"""
    restore_record_file = os.path.join(BACKUP_FOLDER, "restore_record.txt")
    
    restore_record = f"""CAD Backfill Restore Record
==============================
Restore Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
User: {os.getenv('USERNAME')}
Machine: {os.getenv('COMPUTERNAME')}
Service: {SERVICE_URL}

Backup Source: {os.path.join(BACKUP_FOLDER, BACKUP_GDB_NAME, BACKUP_FC_NAME)}
Restored Count: {EXPECTED_BACKUP_COUNT:,}

Reason: Emergency rollback from failed truncate or backfill operation

Status: Dashboard restored to pre-backfill state
Next Steps: Investigate failure cause before retrying backfill
"""
    
    with open(restore_record_file, "w") as f:
        f.write(restore_record)
    
    log(f"✅ Restore record saved: {restore_record_file}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main restore execution"""
    log_separator()
    log("CAD BACKFILL - EMERGENCY RESTORE FROM BACKUP")
    log_separator()
    
    log(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"User: {os.getenv('USERNAME')}")
    log(f"Machine: {os.getenv('COMPUTERNAME')}\n")
    
    log("⚠️⚠️⚠️  ROLLBACK OPERATION  ⚠️⚠️⚠️")
    log("=" * 80)
    log("This script will:")
    log("   1. TRUNCATE all current data in the online layer")
    log("   2. RESTORE the pre-backfill backup (561,740 records)")
    log("   3. DISCARD any partial backfill progress")
    log("=" * 80)
    log("\nUse this script ONLY if:")
    log("   - Truncate succeeded but backfill failed partway")
    log("   - You need to revert to the pre-backfill state")
    log("   - Dashboard shows incorrect or incomplete data")
    log("=" * 80)
    
    # Confirmation
    print("\n" + "="*80)
    print("CONFIRMATION REQUIRED")
    print("="*80)
    confirm = input("\nType 'ROLLBACK' to proceed with restore: ")
    if confirm != "ROLLBACK":
        log("❌ Restore cancelled by user")
        sys.exit(0)
    
    # Step 1: Validate backup
    log("\nSTEP 1: Validating backup availability...")
    backup_fc_path = validate_backup_exists()
    if not backup_fc_path:
        log("\n❌ ABORT: No backup available for restore", "ERROR")
        sys.exit(1)
    
    # Step 2: Check online status
    log("\nSTEP 2: Checking current online status...")
    current_count = check_online_status()
    if current_count is None:
        log("\n❌ ABORT: Cannot connect to online service", "ERROR")
        sys.exit(1)
    
    if current_count > 0:
        log(f"\n⚠️  Current online layer has {current_count:,} records")
        log("   These will be DELETED during restore")
        confirm2 = input(f"\nProceed with deletion of {current_count:,} records? (yes/no): ")
        if confirm2.lower() != "yes":
            log("❌ Restore cancelled by user")
            sys.exit(0)
    
    # Step 3: Truncate current data
    log("\nSTEP 3: Truncating current data...")
    if not truncate_current_data():
        log("\n❌ ABORT: Failed to truncate current data", "ERROR")
        sys.exit(1)
    
    # Step 4: Restore backup
    log("\nSTEP 4: Restoring backup data...")
    if not append_backup_data(backup_fc_path):
        log("\n❌ CRITICAL: Restore failed! Online layer may be empty!", "ERROR")
        log("   Contact support immediately", "ERROR")
        sys.exit(1)
    
    # Step 5: Verify count
    log("\nSTEP 5: Verifying restore integrity...")
    if not verify_restore_count(EXPECTED_BACKUP_COUNT):
        log("\n⚠️  WARNING: Restore count verification failed", "WARNING")
        log("   Review online layer manually", "WARNING")
    
    # Step 6: Save record
    log("\nSTEP 6: Saving restore record...")
    save_restore_record()
    
    # Success!
    log_separator()
    log("✅ RESTORE COMPLETED")
    log_separator()
    log(f"\nOnline layer: {SERVICE_URL}")
    log(f"Current count: {EXPECTED_BACKUP_COUNT:,} records (restored from backup)")
    log(f"\n⚠️  Dashboard has been rolled back to pre-backfill state")
    log(f"\nNext steps:")
    log(f"   1. Investigate why backfill failed")
    log(f"   2. Fix any issues identified")
    log(f"   3. Re-run backfill when ready")
    log_separator()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\n\n❌ Restore cancelled by user (Ctrl+C)", "ERROR")
        log("   Online layer may be in inconsistent state - check manually", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"\n\n❌ Unexpected error: {str(e)}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        sys.exit(1)
