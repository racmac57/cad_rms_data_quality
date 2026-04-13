# ONE-TIME BACKFILL - Clean Historical Data (2019-2026)

**Date:** 2026-02-05  
**Time Available:** 1 hour 25 minutes  
**Goal:** Load clean polished ESRI dataset into dashboard before tonight's automated run  
**Status:** READY TO EXECUTE

---

## What This Does

**One-time backfill of historical data (2019 to 2026-02-03):**
- ✅ Loads 565,870 clean, normalized records
- ✅ Fixes Phone/911 issue in ALL historical data
- ✅ Provides best quality historical data through 2026-02-03
- ✅ Tonight's automated run (12:30 AM) will update the last 7 days with fresh data

**The 7-Day Overlap:**
Your desktop file `ESRI_CADExport.xlsx` contains the last 7 days (01/28 - 02/04). When tonight's task runs, it will:
- Overwrite 01/28 - 02/04 with fresh data from FileMaker ✅ This is fine!
- Add 02/05 (today's new records) ✅

So you get:
- **Pre-01/28:** Clean historical data from backfill (Phone/911 fixed)
- **01/28 onward:** Fresh data from nightly updates

---

## Prerequisites (5 minutes)

### 1. Verify Clean Dataset Location

The clean polished ESRI file from yesterday/this morning should be at:

**Option A: From CSV export (if you have it)**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\consolidation\output\CFSTable_2019_2026_FULL_20260203_231437.csv
```

**Option B: From baseline (if generated)**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx
```

**Check which you have:**
```powershell
# Check CSV
Test-Path "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\consolidation\output\CFSTable_2019_2026_FULL_20260203_231437.csv"

# Check Excel baseline
Test-Path "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx"
```

**If neither exists:** Check `C:\HPD ESRI\03_Data\CAD\Backfill\` on the server (you may have already copied it there)

---

## Step-by-Step Execution (Total: 60-70 minutes)

### **Step 1: Copy Clean Data to Server** (10 minutes - LOCAL MACHINE)

```powershell
# Open PowerShell on LOCAL machine
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\arcgis"

# If you have the Excel baseline:
.\Copy-PolishedToServer.ps1

# If script doesn't exist or you prefer manual copy:
# Via RDP: Copy the file to server at C:\HPD ESRI\03_Data\CAD\Backfill\
```

**What this does:**
- Copies your clean dataset to the server
- Destination: `C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx`

**Verify:**
```powershell
# On server (via RDP)
Get-Item "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" | Select Name, Length, LastWriteTime

# Should show today's date and ~70-80 MB size
```

---

### **Step 2: Connect to Server** (2 minutes)

```
1. Open Remote Desktop Connection
2. Connect to: HPD2022LAWSOFT
3. Log in with your credentials
4. Open PowerShell (Run as Administrator)
```

---

### **Step 3: Pre-Flight Checks** (5 minutes - ON SERVER)

```powershell
cd "C:\HPD ESRI\04_Scripts"

# Run readiness check
.\Test-PublishReadiness.ps1
```

**Expected output:**
```
✅ Lock file: Not present
✅ Scheduled tasks: Not running
✅ Geoprocessing: Not active
✅ Geodatabase: Available
✅ Excel validation: Sheet1 exists
✅ Disk space: Sufficient

[READY] System is ready for backfill publish
```

**If any checks fail:**
- **Lock file exists:** Wait 5 minutes or check if process is stuck
- **Scheduled task running:** Wait for it to finish (shouldn't be running during day)
- **Geoprocessing active:** Close ArcGIS Pro if open
- **Excel sheet wrong:** Your file might have different sheet name - check it

---

### **Step 4: Dry Run Test** (5 minutes - ON SERVER)

```powershell
cd "C:\HPD ESRI\04_Scripts"

# Test run (no actual publish)
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" `
    -DryRun
```

**Expected output:**
```
[DRY RUN MODE - Testing only, no changes made]

[1] Loading configuration... [OK]
[2] Verifying files... [OK]
[3] Pre-flight checks... [OK]
[4] Would swap: backfill → staging
[5] Would run: Publish Call Data tool
[6] Would restore: default → staging
[7] Would cleanup: lock file

[SUCCESS] Dry run completed - ready for actual run
```

**If errors appear:** Stop here and troubleshoot. Don't proceed to actual run.

---

### **Step 5: Actual Backfill Publish** (40-60 minutes - ON SERVER)

**⚠️ IMPORTANT:** This will take 40-60 minutes. Make sure you can stay connected.

```powershell
cd "C:\HPD ESRI\04_Scripts"

# ACTUAL RUN
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
```

**What happens:**
```
[LIVE MODE]

[1] Loading configuration... [OK]
[2] Verifying files... [OK]
[3] Pre-flight checks... [OK]
[4] Creating lock file... [OK]
[5] Swapping backfill to staging...
    - Hash verification... [OK]
    - Atomic swap... [OK]
[6] Running Publish Call Data tool...
    - This takes 40-60 minutes
    - Importing 565,870 records
    - Publishing to ArcGIS Online
    - [Progress messages will appear]
[7] Tool completed... [OK]
[8] Restoring default export...
    - Atomic swap... [OK]
[9] Cleanup... [OK]

[SUCCESS] Backfill publish completed
```

**Monitor progress:**
- Watch for "Tool execution completed!" message
- Check for any error messages
- If connection drops, reconnect and check lock file

**If it fails mid-way:**
- Script will auto-restore staging file
- Lock file will be removed
- Safe to try again

---

### **Step 6: Verify Dashboard** (5 minutes)

**A. Check ArcGIS Online Feature Service**

```
1. Open browser
2. Go to ArcGIS Online
3. Navigate to: Content → CallsForService
4. Click "Data" tab
5. Verify:
   ✅ Last Modified: Today's date
   ✅ Record count: ~565,870 (or close to it)
```

**B. Check Dashboard**

```
1. Open your CAD dashboard URL
2. Verify:
   ✅ Date range shows: 2019 to 2026
   ✅ "Call Source" filter does NOT show "Phone/911" combined
   ✅ Shows separate "Phone" and "9-1-1" options
   ✅ Historical data (pre-2023) is visible
```

**C. Spot Check Historical Data**

```
Dashboard filters:
- Date range: 2019-01-01 to 2019-12-31
- Should show records
- Call Source: Should have Phone and 9-1-1 separated (not combined)
```

---

## Troubleshooting

### Issue: "Backfill file not found"

```powershell
# Verify file exists
Test-Path "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"

# If False, copy it manually via RDP
# Or use Copy-PolishedToServer.ps1 from local machine
```

### Issue: "Lock file exists"

```powershell
# Check lock file content
Get-Content "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\_LOCK.txt"

# Check if process is running
$lock = Get-Content "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\_LOCK.txt" | ConvertFrom-Json
Get-Process -Id $lock.process_id -ErrorAction SilentlyContinue

# If no process, remove stale lock
Remove-Item "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\_LOCK.txt" -Force
```

### Issue: "Tool fails with error"

```powershell
# Check log file
$latestLog = Get-ChildItem "C:\Temp\arcgis_scheduled_tasks" | Sort LastWriteTime -Descending | Select -First 1
Get-Content $latestLog.FullName -Tail 50
```

**Common errors:**
- **Sheet name wrong:** Your Excel file might not have "Sheet1" - check and rename if needed
- **File too large:** Try splitting into smaller date ranges (not recommended unless necessary)
- **Network timeout:** Run during off-peak hours (early morning 2-6 AM)

### Issue: "Upload takes longer than expected"

**This is normal for large datasets:**
- 565,870 records can take 40-90 minutes to upload
- Network speed affects upload time
- If >90 minutes, check if still progressing or hung

**If hung (no progress for 15+ minutes):**
```powershell
# Find the ArcGIS Pro Python process
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# If stuck, you may need to kill it and retry
# But let the script's error handling try first
```

---

## After Backfill Completes

### **Tonight's Automated Run (12:30 AM)**

The scheduled task will run automatically and:
1. Export last 7 days from FileMaker (01/28 - 02/05)
2. Copy to staging
3. **Publish to dashboard** (if you added Action 3 per QUICK_START_DAILY_PUBLISH.md)

**Result:** 
- Historical data (2019 to 01/27): ✅ Clean from backfill (Phone/911 fixed)
- Recent data (01/28 to 02/05): ✅ Fresh from tonight's export

**The overlap is GOOD:**
- Ensures continuity
- Fresh data overwrites older backfill data for recent dates
- No gaps

---

## Timeline Breakdown

| Step | Time | Description |
|------|------|-------------|
| Prerequisites | 5 min | Verify files exist |
| Step 1: Copy to server | 10 min | Transfer clean dataset |
| Step 2: Connect to RDP | 2 min | Remote desktop connection |
| Step 3: Pre-flight checks | 5 min | Verify system ready |
| Step 4: Dry run | 5 min | Test without publishing |
| Step 5: Actual publish | 40-60 min | ⏱️ LONGEST STEP |
| Step 6: Verify | 5 min | Check dashboard |
| **TOTAL** | **72-92 min** | **Fits in 1hr 25min** ✅ |

**Critical path:** Step 5 (actual publish) is the bottleneck. Plan to start this step when you can remain connected for 60 minutes.

---

## Success Criteria

✅ **Backfill completed** - Script shows "SUCCESS" message  
✅ **Dashboard updated** - Shows 2019-2026 date range  
✅ **Phone/911 fixed** - Separated into Phone and 9-1-1 in filters  
✅ **Historical data visible** - Can filter to 2019 and see records  
✅ **Ready for tonight** - Staging file restored, lock file removed

---

## What Happens Tonight (Automatic)

**12:05 AM:**
- FileMaker Schedule 8 exports last 7 days

**12:30 AM:**
- Task `LawSoftESRICADExport` runs:
  - Copies FileMaker export to staging
  - Runs batch file (copies to other locations)
  - **If you added Action 3:** Publishes to dashboard

**Result:**
- Dashboard shows 2019-2026 data
- Last 7 days are fresh from FileMaker
- Everything before that is your clean backfill data

---

## Quick Command Reference

```powershell
# LOCAL MACHINE: Copy to server
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\arcgis"
.\Copy-PolishedToServer.ps1

# SERVER: Pre-flight checks
cd "C:\HPD ESRI\04_Scripts"
.\Test-PublishReadiness.ps1

# SERVER: Dry run
.\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" -DryRun

# SERVER: Actual run
.\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"

# SERVER: Check lock file (if needed)
Get-Content "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\_LOCK.txt"

# SERVER: Check latest log
Get-ChildItem "C:\Temp\arcgis_scheduled_tasks" | Sort LastWriteTime -Descending | Select -First 1 | Get-Content -Tail 50
```

---

## Important Notes

1. **This is a ONE-TIME backfill** - Not recurring automation
2. **Tonight's task handles daily updates** - Make sure Action 3 is added (see QUICK_START_DAILY_PUBLISH.md)
3. **7-day overlap is intentional** - Ensures continuity, fresh data for recent dates
4. **Stay connected during Step 5** - 40-60 minute upload, don't disconnect RDP
5. **Script has safety features** - Auto-restore on error, lock file prevents collisions

---

## Next Steps (After Backfill)

**TODAY (After backfill completes):**
1. ✅ Verify dashboard shows historical data
2. ✅ Add Action 3 to scheduled task (if not done yet) - See QUICK_START_DAILY_PUBLISH.md

**TONIGHT (12:30 AM):**
- Scheduled task runs automatically
- Dashboard updates with today's data

**TOMORROW MORNING:**
- Verify dashboard updated overnight
- Check scheduled task ran successfully

---

**Created:** 2026-02-05  
**Time Required:** 1 hour 25 minutes  
**Status:** Ready to execute  
**Type:** One-time manual backfill
