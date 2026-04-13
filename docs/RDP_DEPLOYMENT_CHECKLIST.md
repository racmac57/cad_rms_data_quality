# RDP DEPLOYMENT CHECKLIST
## Deploy CAD Baseline to ArcGIS Pro - 2026-02-03

**You are here:** Logged into HPD2022LAWSOFT as administrator.HPD  
**Goal:** Deploy 754,409 records to ArcGIS Pro dashboard  
**Time:** ~15-20 minutes

---

## ✅ STEP 1: Copy Baseline File (30 seconds)

Run this command in PowerShell on the server:

```powershell
Copy-Item "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx" -Destination "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" -Force
```

Then verify:
```powershell
Get-Item "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" | Select-Object Name, @{Name='SizeMB';Expression={[math]::Round($_.Length/1MB,1)}}, LastWriteTime
```

**Expected output:**
- Name: CAD_Consolidated_2019_2026.xlsx
- Size: **76.1 MB** (not 70.6 MB!)
- Date: **TODAY** (2026-02-03)

If you see the old file (70.6 MB, 1/31), the copy failed - check OneDrive sync status.

---

## ✅ STEP 2: Run Dry Run Test (2-3 minutes)

```powershell
cd "C:\HPD ESRI\04_Scripts"

.\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" -DryRun
```

**What this does:**
- ✅ Checks all prerequisites (lock files, tasks, processes)
- ✅ Validates file can be read
- ✅ Shows what WOULD happen
- ❌ Does NOT change anything

**Expected output:**
- [OK] All pre-flight checks passed
- [DRY RUN] Would swap staging file
- [DRY RUN] Would run publish tool
- [DRY RUN] Would restore staging file

**If it fails:**
- Read the error message
- Common issues: Lock file exists, scheduled task running, ArcGIS Pro open

---

## ✅ STEP 3: Run Actual Backfill (10-15 minutes)

**Only proceed if Step 2 passed!**

```powershell
.\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
```

**What this does:**
1. Backs up current staging file
2. Swaps in your 754,409-record baseline
3. Runs ArcGIS Pro publish tool
4. Restores original staging file
5. Cleans up lock file

**Watch for:**
- Progress messages every 30 seconds
- "Publish tool completed successfully"
- "Emergency restore NOT needed"

**If something goes wrong:**
- Script will automatically restore the staging file
- Check output for error details
- Lock file will be cleaned up automatically

---

## ✅ STEP 4: Verify Dashboard (5 minutes)

1. Open dashboard in web browser
2. Check these key metrics:
   - **Date range**: Should show 2019-01-01 to 2026-02-03
   - **Record count**: Should be ~754,409
   - **January 2026**: Should have data for ALL of January (not just Jan 10+)
   - **February 2026**: Should show Feb 1-3 data

---

## 🚨 If You See Errors

### Error: "Lock file exists"
```powershell
# Check lock file
Get-Content "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\_LOCK.txt"

# If process is dead, remove manually
Remove-Item "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\_LOCK.txt" -Force
```

### Error: "Scheduled task is running"
Wait for the nightly task to finish (usually runs after midnight, takes ~5 minutes).

### Error: "ArcGIS geoprocessing workers active"
Close ArcGIS Pro completely and try again.

### Error: "Sheet name is not Sheet1"
Open the Excel file and rename the sheet to "Sheet1".

---

## 📊 What You're Deploying

- **Records**: 754,409
- **Date Range**: 2019-01-01 to 2026-02-03
- **Unique Cases**: 560,031
- **Includes**: All supplements and unit records
- **Quality**: 100% validated (10/10 tests passed)
- **Jan 1-9 Gap**: ✅ FILLED (3,101 records)

---

## ⏱️ Timeline

- Step 1 (Copy): 30 seconds
- Step 2 (Dry Run): 2-3 minutes
- Step 3 (Actual): 10-15 minutes
- Step 4 (Verify): 5 minutes
- **Total**: 15-20 minutes

---

## 🎯 Success Criteria

You'll know it worked when:
- ✅ No error messages in PowerShell
- ✅ "Publish tool completed successfully" appears
- ✅ Dashboard shows data through Feb 2026
- ✅ Record count is ~754K
- ✅ January 1-9 data is visible

---

**Ready? Start with STEP 1 above!**

Last updated: 2026-02-03
