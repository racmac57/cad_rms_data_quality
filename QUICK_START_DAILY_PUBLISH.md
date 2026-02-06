# Quick Start: Enable Daily Dashboard Publishing

**Goal:** Add automatic dashboard publishing to nightly scheduled task  
**Time:** 15 minutes  
**Risk:** LOW - Easy rollback, small datasets, tested tool  
**Benefit:** Dashboards update automatically every night

---

## Current Problem

**What's happening now:**
```
12:05 AM - FileMaker exports CAD data ✅
12:30 AM - Scheduled task copies files ✅
          - But does NOT publish to dashboard ❌
          
Result: Dashboards show old data
```

**What needs to happen:**
```
12:05 AM - FileMaker exports CAD data ✅
12:30 AM - Scheduled task copies files ✅
12:31 AM - Scheduled task publishes to dashboard ✅ (NEW)

Result: Dashboards update automatically
```

---

## Step 1: Verify Prerequisites (5 minutes)

### A. Check that staging file exists and is current

```powershell
# Connect to HPD2022LAWSOFT via RDP

# Check staging file
Get-Item "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx" | Select Name, LastWriteTime, Length

# Should show today's date
# If not, run this to update it:
Copy-Item "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx" `
          "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx" -Force
```

### B. Verify Python runner script exists

```powershell
Test-Path "C:\HPD ESRI\04_Scripts\run_publish_call_data.py"
# Should return: True

# If False, copy it from docs/arcgis/ in the repo
```

### C. Test the publish script manually (RECOMMENDED)

```powershell
cd "C:\HPD ESRI\04_Scripts"

# Test run (should take 5-30 minutes depending on data size)
C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat "run_publish_call_data.py"

# Watch for:
# ✅ "Tool execution completed!"
# ✅ "SUCCESS: Publish Call Data completed successfully"
# ❌ Any error messages (fix before scheduling)
```

---

## Step 2: Add Action to Scheduled Task (5 minutes)

### A. Open Task Scheduler

```
1. Press Win+R
2. Type: taskschd.msc
3. Press Enter
4. Navigate to: Task Scheduler Library
5. Find task: LawSoftESRICADExport
6. Right-click → Properties
```

### B. Add New Action

```
1. Click "Actions" tab
2. Click "New..." button
3. Fill in:

   Action: Start a program
   
   Program/script:
   C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat
   
   Add arguments:
   "C:\HPD ESRI\04_Scripts\run_publish_call_data.py"
   
   Start in:
   C:\HPD ESRI\04_Scripts

4. Click "OK"
5. Click "OK" again to save task
```

### C. Verify Action Order

The task should now have these actions IN THIS ORDER:

```
Action 1: Copy to staging (PowerShell)
Action 2: Run LawSoftESRICadExport.bat
Action 3: Run publish tool (NEW - propy.bat)
```

---

## Step 3: Test the Updated Task (5 minutes)

### Option A: Test Now (RECOMMENDED)

```powershell
# This will run all 3 actions immediately
Start-ScheduledTask -TaskName "LawSoftESRICADExport"

# Monitor task status
Get-ScheduledTask -TaskName "LawSoftESRICADExport" | Select TaskName, State, LastRunTime, LastTaskResult

# Check log file (created by run_publish_call_data.py)
Get-ChildItem "C:\Temp\arcgis_scheduled_tasks" | Sort LastWriteTime -Descending | Select -First 1
```

### Option B: Test Tonight (Let it run at 12:30 AM)

```powershell
# Just let it run automatically tonight
# Check results tomorrow morning

# Tomorrow: Check log
Get-ChildItem "C:\Temp\arcgis_scheduled_tasks" | Sort LastWriteTime -Descending | Select -First 1 | Get-Content
```

---

## Step 4: Verify Dashboard Updated

### Check ArcGIS Online

1. Open dashboard URL
2. Check "Last Updated" timestamp
3. Verify today's records are present
4. Test key filters (Call Source, Disposition, etc.)

### Quick Verification Query

```
Dashboard should show:
- Last updated: [Today's date]
- Records with today's date: [Some number > 0]
- No "Phone/911" combined values (should be separate Phone and 9-1-1)
```

---

## Troubleshooting

### Issue: Task fails with "Cannot find propy.bat"

**Fix:**
```powershell
# Use full path
C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat
```

### Issue: Task fails with "Cannot find run_publish_call_data.py"

**Fix:**
```powershell
# Check file exists
Test-Path "C:\HPD ESRI\04_Scripts\run_publish_call_data.py"

# If missing, copy from repo:
Copy-Item "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\arcgis\run_publish_call_data.py" `
          "C:\HPD ESRI\04_Scripts\" -Force
```

### Issue: Task runs but dashboard doesn't update

**Check:**
```powershell
# 1. Check if upload completed
Get-Content "C:\Temp\arcgis_scheduled_tasks\publish_call_data_*.log" -Tail 20

# Should see: "SUCCESS: Publish Call Data completed successfully"

# 2. Check if feature service received data
# Log into ArcGIS Online
# Go to: Content → CallsForService → Data tab
# Verify "Last Modified" is today
```

### Issue: Upload takes too long (>1 hour)

**This is expected for large datasets**

If this is a problem:
- Consider weekly backfill instead of nightly (see NIGHTLY_AUTOMATION_ASSESSMENT.md)
- Or accept longer nightly run time
- Or split into smaller incremental updates

---

## Monitoring

### Daily Check (First 3 Days)

```powershell
# Check task ran successfully
Get-ScheduledTask -TaskName "LawSoftESRICADExport" | 
  Select TaskName, State, LastRunTime, LastTaskResult

# LastTaskResult should be: 0 (success)
# If not 0, check logs

# Check log file
Get-ChildItem "C:\Temp\arcgis_scheduled_tasks" | 
  Sort LastWriteTime -Descending | 
  Select -First 1 | 
  Get-Content -Tail 50
```

### Weekly Check (After Initial Testing)

- Dashboard shows current data
- No error emails/alerts
- Task running within acceptable time (<1 hour)
- Quality scores remain stable (≥95)

---

## Rollback Plan

### If Something Goes Wrong

**Option 1: Remove Action 3**
```
1. Open Task Scheduler
2. Find: LawSoftESRICADExport
3. Properties → Actions tab
4. Select Action 3 (propy.bat)
5. Click "Remove"
6. Click "OK"

Result: Task goes back to just copying files
```

**Option 2: Disable Entire Task**
```powershell
Disable-ScheduledTask -TaskName "LawSoftESRICADExport"

# Re-enable later when fixed
Enable-ScheduledTask -TaskName "LawSoftESRICADExport"
```

**Option 3: Run Manually Until Fixed**
```powershell
# Disable scheduled task
Disable-ScheduledTask -TaskName "LawSoftESRICADExport"

# Run manually when needed
cd "C:\HPD ESRI\04_Scripts"
C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat "run_publish_call_data.py"
```

---

## Success Criteria

✅ **Task runs successfully** (LastTaskResult = 0)  
✅ **Dashboard updates nightly** (Last Modified = today)  
✅ **No error logs** (check C:\Temp\arcgis_scheduled_tasks\)  
✅ **Upload completes in reasonable time** (<1 hour preferred)  
✅ **Quality remains high** (≥95 validation score)

---

## Next Steps (After This Works)

Once daily publishing is stable:

1. **Generate clean baseline** (run validation first)
2. **Test collision detection** (manual backfill while task running)
3. **Add weekly backfill task** (for historical data refresh)
4. **Set up monitoring/alerts** (automated checks)

See `NIGHTLY_AUTOMATION_ASSESSMENT.md` for full roadmap.

---

## Summary

**What we're doing:**
Adding a 3rd action to the existing scheduled task to publish data to ArcGIS Online

**Why it's safe:**
- ✅ Low risk (small datasets, tested tool)
- ✅ Easy rollback (just remove the action)
- ✅ Doesn't change existing file copy logic
- ✅ Can test manually before scheduling

**Expected result:**
Dashboards update automatically every night at ~12:31 AM

**Time to implement:** 15 minutes  
**Time to verify:** 24 hours (wait for first automated run)

---

**Created:** 2026-02-05  
**Status:** Ready to implement  
**Risk Level:** LOW
