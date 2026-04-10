# Handoff: Crime Data Pipeline — Create Scheduled Task

**Date:** 2026-04-10  
**Status:** Ready to implement. Complete ESRI pipeline verification first.  
**Prerequisite:** `HANDOFF_20260410_ESRI_Pipeline_Fixed.md` — confirm Call Data task is working  
**Server:** HPD2022LAWSOFT (10.0.0.157) — RDP as `HPD\administrator`

---

## Opening Prompt — Cursor

Paste this as your first message in a new Cursor chat:

```
Read C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\ai_handoff\HANDOFF_20260410_Crime_Data_Automation.md before responding.

Context: The Call Data nightly pipeline is now fixed (see HANDOFF_20260410_ESRI_Pipeline_Fixed.md). The Crime Data pipeline currently has NO scheduled task — it runs manually from ArcGIS Pro. I need to create a Task Scheduler job that runs the Crime Data publish pipeline nightly at 1:30 AM (after the NIBRS export at 1:00 AM). I'm connected to HPD2022LAWSOFT via RDP as HPD\administrator. Walk me through creating the wrapper script and the scheduled task.
```

## Opening Prompt — Claude Code

Run `claude` from the repo root, then paste:

```
I need to automate the Crime Data publish pipeline on HPD2022LAWSOFT (10.0.0.157). Read docs/ai_handoff/HANDOFF_20260410_Crime_Data_Automation.md for full context.

The Crime Data pipeline runs Model1 from the LawEnforcementDataManagement.atbx toolbox against the ESRI_NIBRSExport.xlsx FileMaker export. It currently runs manually only. I need to:
1. Write a Python wrapper script at C:\ESRIExport\Scripts\Publish_Crime_Data.py
2. Test it manually first (exit code 0 verification)
3. Create a Task Scheduler task to run it at 1:30 AM as HPD\administrator with RunLevel Highest

I will RDP and execute your commands. Start with the wrapper script content.
```

---

## Background

### What the Crime Data Pipeline Does (confirmed from manual run log, 2026-04-09 5:53 PM)

1. **Truncates** `CrimeUploadTable` and `TempLayer` in the HPD ESRI GDB
2. **Table Select** from `ESRI_NIBRSExport.xlsx` → filters to reportable incidents
3. **Calculates fields** (State, Location Type, Weapon Type)
4. **Adds Date Attributes** (day of week, hour, month, year)
5. **Joins** OffenseCodeLookup, WeaponCodeLookup, LocationCodeLookup
6. **Geocodes** via `NJ_Geocode.loc` (zero AGOL credits)
7. **Joins** police posts and beat polygons from AGOL
8. **Appends** to `CrimeUploadTable`
9. **UpdateFeaturesWithIncidentRecords** → AGOL Crimes feature service (UPSERT)
10. **Generate Incident Statistics** → AGOL CrimeStats feature service

**Last manual run results:** 100 records, 98 features updated to AGOL, 1 min 13 sec total

### GDB and Paths (Crime Data uses HPD ESRI, not ESRIExport)
```
Tool:    C:\ESRIExport\LawEnforcementDataManagement_New\LawEnforcementDataManagement.atbx\Model1
GDB:     C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb
Geocoder: C:\HPD ESRI\LawEnforcementDataManagement_New\NJ_Geocode.loc
Input:   C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_NIBRSExport.xlsx\Sheet1$
AGOL Crimes: https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/Crimes_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0
AGOL CrimeStats: https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CrimeStats_af933257473d49e2b4bd84f028a1c0b5/FeatureServer/0
```

---

## Implementation Plan

### Step 1 — Create the wrapper script on the server

Save to `C:\ESRIExport\Scripts\Publish_Crime_Data.py`:

```python
# Publish Crime Data — nightly automation wrapper
# Calls Model1 (Publish Crime Data) from LawEnforcementDataManagement.atbx
# Mirrors the structure of task.py used by the Call Data pipeline

import arcpy
import sys
import datetime
import os

LOG_DIR = r"C:\ESRIExport\logs"
INPUT_XLSX = r"C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_NIBRSExport.xlsx\Sheet1$"
ATBX = r"C:\ESRIExport\LawEnforcementDataManagement_New\LawEnforcementDataManagement.atbx"

os.makedirs(LOG_DIR, exist_ok=True)

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_path = os.path.join(LOG_DIR, f"crime_data_{timestamp}.txt")

def log(msg):
    print(msg)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

log(f"Crime Data Publish — Start: {datetime.datetime.now()}")
log(f"Input: {INPUT_XLSX}")

try:
    arcpy.env.overwriteOutput = True
    arcpy.ImportToolbox(ATBX)
    result = arcpy.Defaultatbx.Model1(INPUT_XLSX)
    log(f"Model1 completed. Status: {result.status}")
    log(f"Messages: {result.getMessage(0) if result.messageCount > 0 else 'none'}")
    log(f"Crime Data Publish — End: {datetime.datetime.now()}")
    sys.exit(0)
except Exception as e:
    log(f"ERROR: {e}")
    import traceback
    log(traceback.format_exc())
    log(f"Crime Data Publish — FAILED: {datetime.datetime.now()}")
    sys.exit(1)
```

### Step 2 — Test manually on the server

```powershell
$py = "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
$script = "C:\ESRIExport\Scripts\Publish_Crime_Data.py"
& $py $script 2>&1
Write-Host "Exit code: $LASTEXITCODE"
Get-ChildItem "C:\ESRIExport\logs" | Sort-Object LastWriteTime -Descending | Select-Object -First 3
```

Expected: exit code 0, log file written to `C:\ESRIExport\logs\crime_data_YYYYMMDD_HHMMSS.txt`

### Step 3 — Create the scheduled task

```powershell
# Create the Scripts directory if it doesn't exist
New-Item -ItemType Directory -Path "C:\ESRIExport\Scripts" -Force
New-Item -ItemType Directory -Path "C:\ESRIExport\logs" -Force

# Create the task
$action = New-ScheduledTaskAction `
    -Execute "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" `
    -Argument '"C:\ESRIExport\Scripts\Publish_Crime_Data.py"' `
    -WorkingDirectory "C:\ESRIExport\LawEnforcementDataManagement_New"

$trigger = New-ScheduledTaskTrigger -Daily -At "1:30AM"

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "Publish Crime Data_2026" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Nightly crime data publish from NIBRS export to AGOL Crimes feature service"

# Set account (schtasks is more reliable for user+runlevel)
$cred = Get-Credential -UserName "HPD\administrator" -Message "Task Scheduler password"
schtasks /change /tn "Publish Crime Data_2026" /ru "HPD\administrator" /rp $cred.GetNetworkCredential().Password /rl HIGHEST

# Verify
Get-ScheduledTask -TaskName "Publish Crime Data_2026" |
    Select-Object TaskName,
        @{n='User';e={$_.Principal.UserId}},
        @{n='RunLevel';e={$_.Principal.RunLevel}},
        @{n='Executable';e={$_.Actions[0].Execute}} |
    Format-List
```

### Step 4 — Trigger a test run

```powershell
Start-ScheduledTask -TaskName "Publish Crime Data_2026"
Start-Sleep -Seconds 90
Get-ScheduledTaskInfo -TaskName "Publish Crime Data_2026" | Select-Object LastRunTime, LastTaskResult
Get-ChildItem "C:\ESRIExport\logs" -Filter "crime_data_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

---

## Expected Nightly Schedule After Both Tasks Fixed

| Time | Task | Pipeline |
|------|------|----------|
| 12:30 AM | `LawSoftESRICADExport` | Copies CAD export from FileMaker |
| 1:00 AM | `LawSoftESRINIBRSExport` | Copies NIBRS export from FileMaker |
| 1:00 AM | `Publish Call Data_2026_NEW` | CAD → AGOL CallsForService (fixed 2026-04-09) |
| 1:30 AM | `Publish Crime Data_2026` | NIBRS → AGOL Crimes (**to be created**) |

---

## Also Pending (Separate Item)

**`2026_02_RMS.xlsx` is 0 bytes** — needs regeneration from LawSoft before April monthly validation runs. This is a separate issue from pipeline automation.

Check: `C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_NIBRSExport.xlsx` size — if 0 bytes, trigger a manual LawSoft export first.
