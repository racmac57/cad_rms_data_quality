# ArcGIS Pro Scheduled Task Verification Guide

**Date Created:** 2026-02-04  
**Issue:** Phone/911 Combined Values in Dashboard  
**Scheduled Task:** Daily CAD data publication  
**Server:** HPD2022LAWSOFT (RDP)

---

## Quick Context

**The Problem:**
The CallsForService feature layer at https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data is showing "Phone/911" as a combined value instead of separate "Phone" and "9-1-1" values.

**Root Cause (Already Fixed):**
An Arcade expression in the ArcGIS Pro Model Builder tool was combining these values:
```arcade
iif($feature.How_Reported=='9-1-1'||$feature.How_Reported=='Phone','Phone/911',$feature.How_Reported)
```

**Fix Applied:**
The expression was changed to just pass through the value:
```arcade
$feature.How_Reported
```

**The Issue:**
The scheduled task needs to run with the FIXED model for the dashboard to update. If the dashboard still shows "Phone/911", either:
1. The scheduled task hasn't run yet
2. The scheduled task failed
3. The scheduled task ran with the OLD (unfixed) model

---

## Scheduled Task Details

### Task Name
`LawSoftESRICADExport`

### Schedule
- **Frequency:** Daily
- **Time:** 12:30 AM (00:30)
- **Trigger:** After FileMaker export completes (12:05 AM)

### What It Does
1. FileMaker exports fresh CAD data to: `C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx`
2. Task copies file to staging: `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx`
3. Runs ArcGIS Pro Model: `TransformCallData_tbx1`
4. Model publishes to feature layer: CallsForService (https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2)

### Server Location
`\\HPD2022LAWSOFT` (connect via RDP)

---

## How to Check If Task Ran Successfully

### Step 1: Check Task Scheduler (Remote Desktop)

**Connect to Server:**
```
Server: HPD2022LAWSOFT
Method: Remote Desktop Connection (RDP)
Credentials: [Your domain admin credentials]
```

**Open Task Scheduler:**
1. Press `Windows + R`
2. Type: `taskschd.msc`
3. Press Enter

**Find the Task:**
1. Navigate to: Task Scheduler Library
2. Find: `LawSoftESRICADExport`
3. Check:
   - **Last Run Time:** Should show today's date at 12:30 AM
   - **Last Run Result:** Should show "0x0" (success) or "0x1" (failure)
   - **Status:** Should show "Ready" (not "Running")

**Interpret Results:**

| Last Run Result | Meaning | Action |
|-----------------|---------|--------|
| `0x0` | Success | Check dashboard to verify data updated |
| `0x1` | General failure | Check task history for details |
| `0x41301` | Task not run yet | Wait for scheduled time or run manually |
| Task still "Running" | Hung or taking long | Check ArcGIS Pro processes |

---

### Step 2: Check Task History

**View History:**
1. Right-click `LawSoftESRICADExport` task
2. Select "View History"
3. Look for entries from today

**What to Look For:**
- **Task Started** (Event ID 100) - Shows task began execution
- **Task Completed** (Event ID 102) - Shows task finished successfully
- **Task Failed** (Event ID 103) - Shows task encountered error
- **Action Started** (Event ID 200) - Shows specific action (script/program) started
- **Action Completed** (Event ID 201) - Shows action finished

**Example Good Run:**
```
12:30:00 AM - Task Started (100)
12:30:05 AM - Action Started: powershell.exe (200)
12:35:42 AM - Action Completed: powershell.exe (201)
12:35:43 AM - Task Completed (102) - Exit Code: 0
```

**Example Failed Run:**
```
12:30:00 AM - Task Started (100)
12:30:05 AM - Action Started: powershell.exe (200)
12:32:18 AM - Task Failed (103) - Error Code: 0x1
```

---

### Step 3: Check ArcGIS Pro Model Logs

**Location:** `C:\HPD ESRI\04_Scripts\Logs\`

**Files to Check:**
- `TransformCallData_YYYYMMDD.log` - Model execution log
- `TaskScheduler_YYYYMMDD.log` - Task scheduler wrapper log
- `ErrorLog_YYYYMMDD.txt` - Any errors encountered

**Open Latest Log:**
```powershell
# Via PowerShell on RDP
cd "C:\HPD ESRI\04_Scripts\Logs"
Get-ChildItem | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 50
```

**What to Look For:**

**Success Indicators:**
```
INFO: Model started at 2026-02-04 00:30:15
INFO: Reading staging file: _STAGING\ESRI_CADExport.xlsx
INFO: Processing 1,247 records
INFO: Calculating fields...
INFO: Publishing to feature service...
INFO: Published successfully at 2026-02-04 00:35:42
INFO: Model completed - 0 errors, 0 warnings
```

**Failure Indicators:**
```
ERROR: Failed to read staging file
ERROR: Field calculation failed
ERROR: Token expired - authentication failed
ERROR: Feature service publish failed
WARNING: Model took longer than expected (>10 minutes)
```

---

### Step 4: Check Staging File Timestamp

**File:** `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx`

**Check Modified Date:**
```powershell
# Via PowerShell on RDP
Get-Item "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx" | Select-Object Name, LastWriteTime, Length
```

**Expected:**
- **LastWriteTime:** Today's date at ~12:30 AM
- **Length:** ~5-10 MB (depends on daily record count)

**If timestamp is old (yesterday or earlier):**
- Task didn't run or file copy failed
- Check Task Scheduler status

---

### Step 5: Verify Dashboard Data Updated

**Check Feature Layer:**
1. Open browser
2. Go to: https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data
3. Click "Data" tab
4. Check:
   - **Record count:** Should include today's date records
   - **Last updated:** Should show today's date/time
   - **HowReported values:** Should see separate "Phone" and "9-1-1" (NOT "Phone/911")

**Query to Test:**
```
Filter: callsource = 'Phone/911'
Expected Result: 0 records (if fix is working)
```

**If still showing "Phone/911":**
- The scheduled task ran with the OLD (unfixed) model
- Need to verify the model fix was saved correctly

---

## Common Issues & Troubleshooting

### Issue 1: Task Ran, But Dashboard Still Shows "Phone/911"

**Root Cause:** Model still has old Arcade expression

**How to Fix:**
1. Connect to RDP server
2. Open ArcGIS Pro
3. Open project: `C:\HPD ESRI\02_Projects\CallDataPublishing.aprx`
4. Open Toolboxes → Find "Publish Call Data" tool
5. Right-click → Edit
6. Find "Calculate Field" tool (Calculate callsource)
7. Check expression - should be: `$feature.How_Reported`
8. If it shows the OLD expression (combining Phone and 9-1-1), change it
9. Save the model
10. Manually run the tool to test
11. Wait for next scheduled run (12:30 AM tomorrow)

---

### Issue 2: Task Failed with "Token Expired"

**Root Cause:** ArcGIS Online authentication token expired

**How to Fix:**
1. Connect to RDP server
2. Open ArcGIS Pro
3. Sign in to ArcGIS Online (will refresh token)
4. Test publish manually
5. Task should work on next scheduled run

---

### Issue 3: Task Status Shows "Running" for Hours

**Root Cause:** ArcGIS Pro process hung or crashed

**How to Fix:**
```powershell
# Check if ArcGISPro.exe is running
Get-Process ArcGISPro -ErrorAction SilentlyContinue

# If hung, kill process
Stop-Process -Name ArcGISPro -Force

# Check task scheduler
# The task should auto-complete after process killed
```

**Then:**
1. Run task manually to verify it works
2. Check logs for what caused the hang

---

### Issue 4: Staging File Not Updated

**Root Cause:** FileMaker export failed or task copy failed

**How to Check:**
```powershell
# Check source file (FileMaker export)
Get-Item "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx" | Select-Object LastWriteTime

# Check staging file
Get-Item "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx" | Select-Object LastWriteTime
```

**Expected:**
- Both files should have today's date at ~12:05 AM (FileMaker) and ~12:30 AM (staging)

**If source file is old:**
- FileMaker export task failed
- Check FileMaker Server scheduled scripts

**If staging file is old:**
- Copy task failed
- Check task scheduler error details

---

## Manual Run Instructions

If you need to run the task manually (don't wait for scheduled time):

### Option A: Run Via Task Scheduler
1. Open Task Scheduler (taskschd.msc)
2. Find `LawSoftESRICADExport`
3. Right-click → "Run"
4. Monitor status (should complete in 5-10 minutes)
5. Check logs and dashboard

### Option B: Run Model Directly in ArcGIS Pro
1. Open ArcGIS Pro on RDP server
2. Open project: `C:\HPD ESRI\02_Projects\CallDataPublishing.aprx`
3. Open Toolboxes → Find "Publish Call Data" tool
4. Right-click → "Open"
5. Verify input: `_STAGING\ESRI_CADExport.xlsx`
6. Click "Run"
7. Monitor progress (5-10 minutes)
8. Check messages pane for completion status

### Option C: Run PowerShell Script Directly
```powershell
# Connect to RDP
# Open PowerShell as Administrator

cd "C:\HPD ESRI\04_Scripts"

# Run the publish script
.\Publish-DailyCADData.ps1

# Check output for success/failure
```

---

## Expected Timeline

**Normal Daily Run:**
- 12:05 AM - FileMaker exports CAD data
- 12:30 AM - Task scheduler triggers
- 12:30 AM - File copied to staging
- 12:30-12:40 AM - ArcGIS Pro model runs
- 12:40 AM - Feature service updated
- 12:40 AM - Dashboard shows new data

**Total Duration:** 10-15 minutes from scheduled trigger

---

## Verification Checklist

After checking the scheduled task, verify:

- [ ] Task Scheduler shows "Last Run: Today 12:30 AM"
- [ ] Task Scheduler shows "Last Result: 0x0" (success)
- [ ] Staging file timestamp is today at ~12:30 AM
- [ ] Log files show successful completion
- [ ] Dashboard record count increased
- [ ] Dashboard "Last Updated" shows today
- [ ] Dashboard shows NO "Phone/911" values (should be separate)
- [ ] HowReported domain has 11 distinct values (not 10)

**If ALL checks pass:** ✅ Task ran successfully, fix is deployed

**If ANY check fails:** ⚠️ Investigate using troubleshooting section above

---

## For the Orchestrator

**Context from Previous Conversation:**
- The Phone/911 issue was identified and fixed in ArcGIS Pro Model Builder
- The Arcade expression was changed to pass through values instead of combining them
- The fix needs to propagate to the dashboard via the scheduled task

**Today's Situation:**
- Scheduled task ran this morning (or should have)
- Dashboard still shows "Phone/911" combined values
- Need to verify if task ran successfully and if fix was applied

**Your Action:**
1. Follow the steps above to check task status on RDP server
2. Verify the model fix is saved (check Arcade expression)
3. If task ran but dashboard still wrong, model likely reverted or wasn't saved
4. If task didn't run, investigate task scheduler errors
5. Run manually if needed to get fix deployed immediately

**Priority:** HIGH - This affects dashboard data quality and user trust

---

**Reference:**
- Dashboard URL: https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data
- Server: HPD2022LAWSOFT (RDP)
- Task: LawSoftESRICADExport (12:30 AM daily)
- Model: TransformCallData_tbx1
- Expected Fix: HowReported shows separate "Phone" and "9-1-1" values

---

**Status:** Awaiting Verification  
**Created:** 2026-02-04  
**Author:** R. A. Carucci (with AI Orchestrator assistance)
