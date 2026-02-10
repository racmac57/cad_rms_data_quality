# 🕒 2026-02-09-09-00-00
# CAD_Backfill_Option_C/truncate_online_layer.py
# Author: R. A. Carucci
# Purpose: Truncate CFStable online layer after backup verification - DESTRUCTIVE OPERATION

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

LOG_FILE = os.path.join(BACKUP_FOLDER, "truncate_log.txt")

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
# PRE-TRUNCATE VALIDATION
# ============================================================================

def validate_backup_exists():
    """Verify backup was created successfully"""
    log("Validating backup existence...")
    
    backup_gdb_path = os.path.join(BACKUP_FOLDER, BACKUP_GDB_NAME)
    backup_fc_path = os.path.join(backup_gdb_path, BACKUP_FC_NAME)
    
    if not arcpy.Exists(backup_fc_path):
        log(f"❌ ABORT: Backup not found at {backup_fc_path}", "ERROR")
        log("   Run backup_current_layer.py first!", "ERROR")
        return False
    
    log(f"✅ Backup exists: {backup_fc_path}")
    return backup_fc_path

def validate_backup_count(backup_fc_path):
    """Verify backup has expected record count"""
    log("Validating backup record count...")
    
    try:
        backup_count = int(arcpy.management.GetCount(backup_fc_path)[0])
        log(f"   Backup count: {backup_count:,}")
        log(f"   Expected: {EXPECTED_BACKUP_COUNT:,}")
        
        if backup_count != EXPECTED_BACKUP_COUNT:
            log(f"⚠️  WARNING: Count mismatch! Expected {EXPECTED_BACKUP_COUNT:,}, got {backup_count:,}", "WARNING")
            response = input("\nBackup count differs from expected. Continue anyway? (yes/no): ")
            if response.lower() != "yes":
                return False
        
        log(f"✅ Backup validated: {backup_count:,} records")
        return True
        
    except Exception as e:
        log(f"❌ Failed to validate backup: {str(e)}", "ERROR")
        return False

def check_backup_metadata():
    """Display backup metadata for user review"""
    metadata_file = os.path.join(BACKUP_FOLDER, "backup_metadata.txt")
    
    if os.path.exists(metadata_file):
        log("\n📋 Backup Metadata:")
        log("-" * 80)
        with open(metadata_file, "r") as f:
            metadata = f.read()
            print(metadata)
        log("-" * 80)
    else:
        log("⚠️  Backup metadata not found", "WARNING")

def test_service_connection():
    """Test connection to online service"""
    log("Testing connection to online service...")
    
    try:
        desc = arcpy.Describe(SERVICE_URL)
        current_count = int(arcpy.management.GetCount(SERVICE_URL)[0])
        log(f"✅ Connection successful")
        log(f"   Current online count: {current_count:,} records")
        return current_count
    except Exception as e:
        log(f"❌ Connection failed: {str(e)}", "ERROR")
        return None

def check_truncate_permissions():
    """Verify user has truncate permissions (admin or owner required)"""
    log("Checking truncate permissions...")
    
    try:
        # Attempt to describe the service
        desc = arcpy.Describe(SERVICE_URL)
        
        # Note: We can't directly check permissions via arcpy
        # User must be owner or admin of the layer
        log(f"✅ Service accessible")
        log(f"   Type: {desc.dataType}")
        log("⚠️  Note: You must be the layer owner or org admin to truncate", "WARNING")
        
        return True
    except Exception as e:
        log(f"❌ Permission check failed: {str(e)}", "ERROR")
        return False

# ============================================================================
# TRUNCATE OPERATION
# ============================================================================

def perform_truncate():
    """Execute truncate operation with final confirmation"""
    
    log("\n⚠️⚠️⚠️  FINAL SAFETY CHECK  ⚠️⚠️⚠️")
    log("=" * 80)
    log("You are about to PERMANENTLY DELETE all records from:")
    log(f"   {SERVICE_URL}")
    log("=" * 80)
    log("\nThis operation:")
    log("   ✅ CAN be recovered from backup")
    log("   ⚠️  CANNOT be undone without the backup")
    log("   ⚠️  Will affect all users viewing the dashboard")
    log("   ⏱️  Takes ~30 seconds to complete")
    log("=" * 80)
    
    # Triple confirmation
    print("\n" + "="*80)
    print("CONFIRMATION REQUIRED - Type exactly as shown (case-sensitive)")
    print("="*80)
    
    confirm1 = input("\n[1/3] Type 'TRUNCATE' to confirm: ")
    if confirm1 != "TRUNCATE":
        log("❌ Truncation cancelled (confirmation 1 failed)")
        return False
    
    confirm2 = input("[2/3] Type your username to confirm: ")
    expected_username = os.getenv('USERNAME')
    if confirm2 != expected_username:
        log(f"❌ Truncation cancelled (username mismatch: expected '{expected_username}')")
        return False
    
    confirm3 = input("[3/3] Type 'DELETE ALL RECORDS' to proceed: ")
    if confirm3 != "DELETE ALL RECORDS":
        log("❌ Truncation cancelled (confirmation 3 failed)")
        return False
    
    log("\n✅ All confirmations received. Proceeding with truncate...")
    log("⏱️  Truncating online layer (this may take 30-60 seconds)...")
    
    start_time = datetime.now()
    
    try:
        # Perform truncate
        arcpy.management.TruncateTable(SERVICE_URL)
        
        duration = (datetime.now() - start_time).total_seconds()
        log(f"✅ Truncate completed in {duration:.1f} seconds")
        
        return True
        
    except arcpy.ExecuteError:
        log(f"❌ Truncate failed (ArcPy error):", "ERROR")
        log(arcpy.GetMessages(2), "ERROR")
        return False
    except Exception as e:
        log(f"❌ Truncate failed: {str(e)}", "ERROR")
        return False

def verify_truncate_success():
    """Verify table is actually empty after truncate"""
    log("\nVerifying truncate success...")
    
    try:
        current_count = int(arcpy.management.GetCount(SERVICE_URL)[0])
        log(f"   Current online count: {current_count:,} records")
        
        if current_count != 0:
            log(f"❌ TRUNCATE FAILED! Table still has {current_count:,} records", "ERROR")
            log("   DO NOT PROCEED - Contact support", "ERROR")
            return False
        
        log(f"✅ Truncate verified: 0 records in online layer")
        return True
        
    except Exception as e:
        log(f"❌ Verification failed: {str(e)}", "ERROR")
        return False

def save_truncate_record():
    """Save record of truncate operation"""
    truncate_record_file = os.path.join(BACKUP_FOLDER, "truncate_record.txt")
    
    truncate_record = f"""CAD Backfill Truncate Record
===============================
Truncate Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
User: {os.getenv('USERNAME')}
Machine: {os.getenv('COMPUTERNAME')}
Service: {SERVICE_URL}
Pre-Truncate Count: {EXPECTED_BACKUP_COUNT:,} (backed up)
Post-Truncate Count: 0 (verified)

Backup Location: {os.path.join(BACKUP_FOLDER, BACKUP_GDB_NAME, BACKUP_FC_NAME)}

Next Step: Run staged backfill (Invoke-CADBackfillPublish.ps1)
Expected Final Count: 754,409 records (2019-01-01 to 2026-02-03)

Rollback Available: Yes (restore_from_backup.py)
"""
    
    with open(truncate_record_file, "w") as f:
        f.write(truncate_record)
    
    log(f"✅ Truncate record saved: {truncate_record_file}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main truncate execution"""
    log_separator()
    log("CAD BACKFILL - PHASE 2: TRUNCATE ONLINE LAYER")
    log_separator()
    
    log(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"User: {os.getenv('USERNAME')}")
    log(f"Machine: {os.getenv('COMPUTERNAME')}\n")
    
    # Pre-flight checks
    log("PRE-FLIGHT CHECKS")
    log("-" * 80)
    
    # Check 1: Backup exists
    log("\n[Check 1/5] Validating backup existence...")
    backup_fc_path = validate_backup_exists()
    if not backup_fc_path:
        log("\n❌ ABORT: No valid backup found", "ERROR")
        log("   Run backup_current_layer.py first!", "ERROR")
        sys.exit(1)
    
    # Check 2: Backup count
    log("\n[Check 2/5] Validating backup record count...")
    if not validate_backup_count(backup_fc_path):
        log("\n❌ ABORT: Backup validation failed", "ERROR")
        sys.exit(1)
    
    # Check 3: Display metadata
    log("\n[Check 3/5] Reviewing backup metadata...")
    check_backup_metadata()
    
    # Check 4: Service connection
    log("\n[Check 4/5] Testing online service connection...")
    current_count = test_service_connection()
    if current_count is None:
        log("\n❌ ABORT: Cannot connect to online service", "ERROR")
        sys.exit(1)
    
    # Check 5: Permissions
    log("\n[Check 5/5] Checking truncate permissions...")
    if not check_truncate_permissions():
        log("\n❌ ABORT: Permission check failed", "ERROR")
        sys.exit(1)
    
    log("\n✅ All pre-flight checks passed")
    
    # Perform truncate with confirmations
    log_separator()
    if not perform_truncate():
        log("\n❌ Truncate operation cancelled or failed", "ERROR")
        sys.exit(1)
    
    # Verify success
    if not verify_truncate_success():
        log("\n❌ CRITICAL: Truncate verification failed!", "ERROR")
        log("   DO NOT PROCEED WITH BACKFILL", "ERROR")
        log("   Run restore_from_backup.py if needed", "ERROR")
        sys.exit(1)
    
    # Save record
    save_truncate_record()
    
    # Success!
    log_separator()
    log("✅ TRUNCATE COMPLETED SUCCESSFULLY")
    log_separator()
    log(f"\nOnline layer: {SERVICE_URL}")
    log(f"Current count: 0 records (verified)")
    log(f"Backup available: {backup_fc_path} ({EXPECTED_BACKUP_COUNT:,} records)")
    log(f"\n🚀 READY FOR STAGED BACKFILL")
    log(f"\nNext step:")
    log(f"   cd C:\\HPD ESRI\\04_Scripts")
    log(f"   .\\Invoke-CADBackfillPublish.ps1 -Staged -BatchFolder \"C:\\HPD ESRI\\03_Data\\CAD\\Backfill\\Batches\"")
    log_separator()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\n\n❌ Truncate cancelled by user (Ctrl+C)", "ERROR")
        log("   Online layer may still contain data - check manually", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"\n\n❌ Unexpected error: {str(e)}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        sys.exit(1)
