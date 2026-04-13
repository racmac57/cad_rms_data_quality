---
name: pipeline-status
description: Generate PowerShell commands to check the nightly ESRI pipeline health on HPD2022LAWSOFT. Use for morning-after verification of Task Scheduler jobs, reading ArcGIS XML logs, and diagnosing failures.
disable-model-invocation: true
argument-hint: [call-data|crime-data|all]
allowed-tools: Read Grep
---

# Nightly Pipeline Health Check

Generate the PowerShell verification commands for the user to run on HPD2022LAWSOFT via RDP.

## Pipeline Definitions

| Pipeline | Task Name | Time | Input File | Status Field |
|----------|-----------|------|------------|--------------|
| Call Data | `Publish Call Data_2026_NEW` | 1:00 AM | `ESRI_CADExport.xlsx` | `LastTaskResult` |
| Crime Data | `Publish Crime Data_2026` | 1:30 AM | `ESRI_NIBRSExport.xlsx` | `LastTaskResult` |
| CAD Export | `LawSoftESRICADExport` | 12:30 AM | FileMaker trigger | `LastTaskResult` |
| NIBRS Export | `LawSoftESRINIBRSExport` | 1:00 AM | FileMaker trigger | `LastTaskResult` |

## Based on the argument `$ARGUMENTS`:

### If "all" or empty -- check everything:

```powershell
# === FULL PIPELINE STATUS ===

# Step 1 -- All task results
$tasks = @(
    "LawSoftESRICADExport",
    "LawSoftESRINIBRSExport",
    "Publish Call Data_2026_NEW",
    "Publish Crime Data_2026"
)
foreach ($t in $tasks) {
    try {
        $info = Get-ScheduledTaskInfo -TaskName $t
        Write-Host "$t => LastResult: $($info.LastTaskResult), LastRun: $($info.LastRunTime), NextRun: $($info.NextRunTime)"
    } catch {
        Write-Host "$t => NOT FOUND or access denied"
    }
}

# Step 2 -- Check input file freshness
$cadExport = "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx"
$nibrsExport = "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_NIBRSExport.xlsx"
Get-Item $cadExport | Select-Object Name, Length, LastWriteTime
Get-Item $nibrsExport | Select-Object Name, Length, LastWriteTime

# Step 3 -- Recent ArcGIS logs (Call Data pipeline)
Get-ChildItem "C:\Users\administrator.HPD\AppData\Local\ESRI\ArcGISPro\Geoprocessing\ScheduledTools\Logs" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, Length, LastWriteTime

# Step 4 -- Crime Data logs
Get-ChildItem "C:\ESRIExport\logs" -Filter "crime_data_*.txt" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, Length, LastWriteTime
```

### If "call-data" -- check Call Data pipeline only:

```powershell
# === CALL DATA PIPELINE STATUS ===

Get-ScheduledTaskInfo -TaskName "Publish Call Data_2026_NEW" |
    Select-Object LastRunTime, LastTaskResult, NextRunTime

# Check XML log
$logDir = "C:\Users\administrator.HPD\AppData\Local\ESRI\ArcGISPro\Geoprocessing\ScheduledTools\Logs"
$latest = Get-ChildItem $logDir | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host "Latest log: $($latest.Name) ($($latest.LastWriteTime))"

# Read the log (XML format)
if ($latest) {
    [xml]$log = Get-Content $latest.FullName
    Write-Host "Status: $($log.SelectSingleNode('//Result/@status').Value)"
    # status 4 = success, 5 = license/import failure
}
```

### If "crime-data" -- check Crime Data pipeline only:

```powershell
# === CRIME DATA PIPELINE STATUS ===

Get-ScheduledTaskInfo -TaskName "Publish Crime Data_2026" |
    Select-Object LastRunTime, LastTaskResult, NextRunTime

# Check log files
Get-ChildItem "C:\ESRIExport\logs" -Filter "crime_data_*.txt" |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1 |
    ForEach-Object { Write-Host "Latest log: $($_.Name)"; Get-Content $_.FullName -Tail 20 }
```

## Interpreting Results

Provide this diagnosis guide alongside the commands:

| LastTaskResult | Meaning | Action |
|----------------|---------|--------|
| `0` | Success | No action needed |
| `1` | Python script error | Read the log file for traceback |
| `2147942401` | Access denied | Task running as wrong user (should be `HPD\administrator`) |
| `2147943645` | Service unavailable | Check if AGOL is reachable, VPN connected |
| `2147946720` | Task killed (timeout) | Execution time limit hit -- check for GDB locks |

| XML Log Status | Meaning |
|----------------|---------|
| `4` | ArcPy model ran successfully |
| `5` | ArcPy import failed (no license -- wrong user context) |
| `0` + empty messages | Exception caught by `except: pass` in task.py |

### Common Failure Modes

1. **Password expired** for `HPD\administrator` -> update task credential with `schtasks /change`
2. **AGOL token expired** -> sign in to ArcGIS Pro interactively once on the server
3. **GDB locked** -> check for `.wr.lock` files:
   ```powershell
   Get-ChildItem "C:\ESRIExport\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb" -Filter "*.lock"
   Get-ChildItem "C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb" -Filter "*.lock"
   ```
4. **Input file is 0 bytes** -> FileMaker export failed; trigger manual export
5. **Input file stale** (>26 hours old) -> FileMaker Server may be down

## Instructions to Claude

1. Determine which pipeline(s) to check based on `$ARGUMENTS` (default: all).
2. Present the appropriate PowerShell commands for the user to run on the server.
3. Ask the user to paste back the output.
4. Interpret the results using the tables above and recommend next steps.
5. If a failure is detected, walk through the diagnosis tree step by step.
