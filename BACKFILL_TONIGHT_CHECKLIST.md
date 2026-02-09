# ArcGIS Pro Backfill - Quick Start Checklist

**Date:** 2026-02-08  
**Purpose:** Complete one-time setup and run backfill before 12:30 AM scheduled tasks  
**Estimated Time:** ~45 minutes total  
**Safe Window:** 8 PM - 11 PM (complete well before 12:30 AM scheduled tasks)

---

## ⚡ PREP BEFORE LEAVING HOME (Do This Now!)

### 1. Copy Required Files

**Location:** `C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\arcgis\`

**Files to copy (to USB or email to yourself):**
- ✅ `config.json`
- ✅ `run_publish_call_data.py`
- ✅ `Test-PublishReadiness.ps1`
- ✅ `Invoke-CADBackfillPublish.ps1`

### 2. Note Source File Location

**Baseline file (724,794 records):**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx
```

---

## 🏢 AT THE OFFICE - COMPLETE WORKFLOW

### PHASE 1: Connect to Server (2 min)

1. Open **Remote Desktop Connection** on your work PC
2. **Computer:** `10.0.0.157` or `HPD2022LAWSOFT`
3. **User:** Your admin credentials (e.g., `administrator`)
4. Click **Connect**
5. Enter admin password when prompted

**✅ Checkpoint:** You're logged into the server desktop

---

### PHASE 2: One-Time Setup (15 min)

#### Step 1: Create Directory Structure (2 min)

On the server, open **PowerShell as Administrator**:

```powershell
# Create directory structure
New-Item -ItemType Directory -Path "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING" -Force
New-Item -ItemType Directory -Path "C:\HPD ESRI\04_Scripts" -Force
New-Item -ItemType Directory -Path "C:\HPD ESRI\05_Reports" -Force
```

**Expected output:** Three "Directory" confirmations

---

#### Step 2: Copy Scripts to Server (3 min)

1. Retrieve the 4 files from USB drive or email
2. Open File Explorer on server
3. Navigate to `C:\HPD ESRI\04_Scripts\`
4. Paste all 4 files
5. Verify all 4 files are present

**Files should be:**
- `config.json`
- `run_publish_call_data.py`
- `Test-PublishReadiness.ps1`
- `Invoke-CADBackfillPublish.ps1`

---

#### Step 3: Initialize Staging File (2 min)

In PowerShell on server:

```powershell
Copy-Item "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx" `
    "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx"
```

**✅ Checkpoint:** No errors, file copied successfully

---

#### Step 4: Copy Baseline File to Server (5 min)

**Option A - If OneDrive synced on server:**
```powershell
# Create backfill directory if needed
New-Item -ItemType Directory -Path "C:\HPD ESRI\03_Data\CAD\Backfill" -Force

# Copy from OneDrive on server
Copy-Item "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx" `
    "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx"
```

**Option B - If OneDrive not synced:**
- Access your work PC from the server
- Copy the file manually via network share or USB
- Place in `C:\HPD ESRI\03_Data\CAD\Backfill\`

**✅ Checkpoint:** File ~75 MB copied to backfill folder

---

#### Step 5: Verify Setup (3 min)

Run these verification commands:

```powershell
# Check directories exist
Test-Path "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING"
Test-Path "C:\HPD ESRI\04_Scripts"
Test-Path "C:\HPD ESRI\05_Reports"

# Check files exist
Test-Path "C:\HPD ESRI\04_Scripts\config.json"
Test-Path "C:\HPD ESRI\04_Scripts\run_publish_call_data.py"
Test-Path "C:\HPD ESRI\04_Scripts\Test-PublishReadiness.ps1"
Test-Path "C:\HPD ESRI\04_Scripts\Invoke-CADBackfillPublish.ps1"
Test-Path "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx"
Test-Path "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx"

# Check file size
Get-Item "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx" | 
    Select-Object Name, @{N='Size (MB)';E={[math]::Round($_.Length/1MB,2)}}
```

**✅ Checkpoint:** All commands return `True`, file size ~71-75 MB

---

### PHASE 3: Run Pre-Flight Checks (5 min)

```powershell
cd "C:\HPD ESRI\04_Scripts"

# Run pre-flight checks
.\Test-PublishReadiness.ps1
```

**Expected output:**
- ✅ Lock file check: PASS (no lock file)
- ✅ Scheduled task check: PASS (not running)
- ✅ ArcGIS process check: PASS (no geoprocessing workers)
- ✅ Geodatabase lock: PASS (writable)
- ✅ Excel sheet check: PASS (Sheet1 exists)
- ✅ Disk space: PASS (>5 GB free)

**If any checks FAIL:**
- Lock file exists: Check if stale, remove if process is dead
- Scheduled task running: Wait for it to complete
- ArcGIS Pro open: Close ArcGIS Pro
- Geodatabase locked: Close any ArcGIS connections

---

### PHASE 4: Run Backfill - DRY RUN (5 min)

Test the backfill process without making actual changes:

```powershell
# Test run (no actual changes)
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx" `
    -DryRun
```

**What to check in output:**
- ✅ No errors
- ✅ Shows it would create lock file
- ✅ Shows it would swap files (backfill → staging)
- ✅ Shows it would call ArcGIS Pro tool
- ✅ Shows it would restore default export
- ✅ Shows it would remove lock file
- ✅ "DRY RUN" appears in output

**✅ Checkpoint:** Dry run completes without errors

---

### PHASE 5: Run ACTUAL Backfill (30 min)

**IMPORTANT:** Monitor the output during this phase!

```powershell
# Real run - this will update the dashboard
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx"
```

**Watch for these steps:**
1. **Lock file created** → Collision protection active
2. **Backup created** → Safety copy of current staging file
3. **File swap started** → Copying backfill to staging (SHA256 verified)
4. **ArcGIS Pro tool starting** → Calling `arcpy.TransformCallData_tbx1()`
5. **Geoprocessing messages** → Watch for progress/errors
6. **Tool completed** → Check exit code
7. **Restore default export** → Staging file restored to default
8. **Lock file removed** → Process complete

**Expected duration:** ~15-30 minutes for the tool to run

**Monitor for:**
- ✅ No errors in PowerShell output
- ✅ Geoprocessing messages appear (shows tool is running)
- ✅ **Exit code: 0** (success)
- ✅ Lock file removed at end

**If it takes longer than 1 hour:**
- Check `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\_LOCK.txt` - is process still alive?
- Check ArcGIS Pro geoprocessing messages for errors
- May need to kill process and troubleshoot

**✅ Checkpoint:** Process completes with exit code 0, no errors

---

### PHASE 6: Verify Dashboard (5 min)

1. Open dashboard in web browser
2. Check the following:

**Data Range:**
- ✅ **Minimum date:** 2019-01-01
- ✅ **Maximum date:** 2026-01-30

**Record Count:**
- ✅ **Expected:** ~724,794 records
- ✅ Verify in dashboard statistics or query

**Visualizations:**
- ✅ Maps display correctly
- ✅ Charts show data from 2019-2026
- ✅ Filters work properly
- ✅ No missing data warnings

**✅ Checkpoint:** Dashboard shows 7 years of data (2019-2026), ~724K records

---

## ⏱️ TIMELINE FOR TONIGHT

| Time | Activity | Duration |
|------|----------|----------|
| 8:00 PM | Arrive, log in to work PC | 5 min |
| 8:05 PM | RDP to server | 2 min |
| 8:07 PM | Create directories (Phase 2, Step 1) | 2 min |
| 8:09 PM | Copy scripts (Phase 2, Step 2) | 3 min |
| 8:12 PM | Initialize staging (Phase 2, Step 3) | 2 min |
| 8:14 PM | Copy baseline file (Phase 2, Step 4) | 5 min |
| 8:19 PM | Verify setup (Phase 2, Step 5) | 3 min |
| 8:22 PM | Pre-flight checks (Phase 3) | 5 min |
| 8:27 PM | Dry run (Phase 4) | 5 min |
| 8:32 PM | **ACTUAL BACKFILL (Phase 5)** | **30 min** |
| 9:02 PM | Verify dashboard (Phase 6) | 5 min |
| **9:07 PM** | **DONE! ✅** | **Total: ~67 min** |

**Scheduled tasks start:** 12:30 AM  
**Your buffer time:** ~3 hours 23 minutes  
**Safe margin:** ✅ Plenty of time!

---

## 🚨 TROUBLESHOOTING

### Issue: Pre-Flight Checks Fail

**Lock file exists:**
```powershell
# Check lock file
Get-Content "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\_LOCK.txt"

# If stale (>2 hours old with dead process), remove:
Remove-Item "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\_LOCK.txt" -Force
```

**Scheduled task running:**
- Wait for it to complete (usually 5-10 minutes)
- Or come back in 15 minutes and try again

**ArcGIS Pro open:**
- Close ArcGIS Pro
- Check Task Manager for `ArcGISPro.exe` processes
- Kill if necessary

**Geodatabase locked:**
- Close all ArcGIS connections
- Restart ArcGIS Pro if needed

---

### Issue: Backfill Takes Longer Than 30 Minutes

**Check progress:**
```powershell
# Check lock file - is process still alive?
Get-Content "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\_LOCK.txt"

# Check for ArcGIS Pro processes
Get-Process | Where-Object {$_.ProcessName -like "*ArcGIS*"}
```

**If stuck (>1 hour):**
1. Check geoprocessing messages in output
2. Look for errors in: `C:\HPD ESRI\05_Reports\`
3. If hung, kill process:
   ```powershell
   # Get PID from lock file, then:
   Stop-Process -Id <PID> -Force
   ```
4. Run emergency restore (if available)
5. Investigate error before retrying

---

### Issue: Dashboard Doesn't Update

**Verify tool ran successfully:**
- Check exit code was 0
- Review geoprocessing messages
- Check if feature class was updated

**Force refresh:**
1. Restart ArcGIS Server service (if applicable)
2. Clear browser cache
3. Re-publish service if needed

**Verify data source:**
```powershell
# Check if staging file was updated
Get-Item "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx" | 
    Select-Object Name, Length, LastWriteTime
```

---

### Issue: Record Count Mismatch

**Expected:** 724,794 records

**If different:**
1. Check date range filter in dashboard
2. Verify complete file was copied (check file size ~75 MB)
3. Check for import errors in ArcGIS Pro
4. Verify baseline file is correct:
   ```powershell
   Get-Item "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx" | 
       Select-Object Name, @{N='Size (MB)';E={[math]::Round($_.Length/1MB,2)}}, LastWriteTime
   ```

---

## 📝 QUICK REFERENCE - KEY PATHS

### Server Locations

**Scripts:**
```
C:\HPD ESRI\04_Scripts\
├── config.json
├── run_publish_call_data.py
├── Test-PublishReadiness.ps1
└── Invoke-CADBackfillPublish.ps1
```

**Data:**
```
C:\HPD ESRI\03_Data\CAD\Backfill\
├── _STAGING\
│   ├── ESRI_CADExport.xlsx (Model reads this file)
│   └── _LOCK.txt (Created during backfill)
└── CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx (Source file, 724,794 records)
```

**Reports:**
```
C:\HPD ESRI\05_Reports\ (Created by backfill process)
```

### Local Machine Locations

**Project Root:**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\
```

**Source Files:**
```
docs\arcgis\ (4 scripts to copy)
13_PROCESSED_DATA\ESRI_Polished\base\ (Baseline file)
```

**Documentation:**
```
docs\arcgis\README_Backfill_Process.md (Complete guide)
BACKFILL_TONIGHT_CHECKLIST.md (This file)
```

---

## ✅ SUCCESS CRITERIA

### Pre-Flight
- [x] All directories created
- [x] All 4 scripts copied to `C:\HPD ESRI\04_Scripts\`
- [x] Staging file initialized
- [x] Baseline file copied to server (~75 MB)
- [x] All verification checks pass (`Test-Path` returns True)

### Execution
- [x] Pre-flight checks pass (all green)
- [x] Dry run completes without errors
- [x] Actual backfill completes (exit code 0)
- [x] No errors in PowerShell output
- [x] Lock file created and removed properly
- [x] Geoprocessing messages show success

### Verification
- [x] Dashboard shows date range: 2019-01-01 to 2026-01-30
- [x] Record count: ~724,794
- [x] Visualizations display correctly
- [x] All charts/maps show 2019-2026 data
- [x] Process completed before 10 PM
- [x] Well before 12:30 AM scheduled tasks

---

## 📞 EMERGENCY CONTACTS & RESOURCES

**If you need help:**
- Complete documentation: `docs\arcgis\README_Backfill_Process.md`
- Configuration: `docs\arcgis\config.json`
- Logs location: `C:\HPD ESRI\05_Reports\` (on server)

**For tomorrow (if needed):**
- This checklist only needs to be done ONCE (one-time setup)
- Future backfills just run Phase 5 (the orchestrator script)
- Estimated time for future backfills: ~30 minutes

---

## 🎯 FINAL CHECKLIST BEFORE YOU START

**Before leaving home:**
- [ ] 4 script files copied to USB or emailed
- [ ] Baseline file location noted
- [ ] This checklist accessible (printed or on phone)

**At the office:**
- [ ] Logged into work PC
- [ ] On office network (no VPN needed when in office)
- [ ] Have admin credentials ready
- [ ] Time check: Starting between 8-9 PM ✓

**You're ready to go!** 🚀

---

**Document Created:** 2026-02-08  
**Version:** 1.0  
**Status:** Ready for tonight's backfill  
**Expected completion:** ~9:00-9:30 PM  
**Safe margin before scheduled tasks:** ✅ 3+ hours
