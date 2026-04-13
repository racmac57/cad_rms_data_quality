# RDP Deployment Verification Checklist
**Date:** 2026-02-15
**Deployment:** Deploy-ToRDP-Simple.ps1 (ScriptsDeploy_20260215_222258)

---

## ✅ What Was Deployed

### Scripts Deployed (33 files → `C:\HPD ESRI\04_Scripts\`)
- All Python scripts from `scripts/` directory
- All PowerShell scripts from `scripts/` directory
- Includes: complete_backfill_simplified.py, publish_with_xy_coordinates.py, backup_current_layer.py, etc.

### Documentation Deployed (3 files → `C:\HPD ESRI\`)
- SUMMARY.md
- README.md
- CHANGELOG.md

### Backup Created
- Location: `\\HPD2022LAWSOFT\C$\HPD ESRI\00_Backups\ScriptsDeploy_20260215_222258\`
- Contains: Previous versions of all deployed files

---

## 🔍 5-Minute Verification Checklist

### 1. Confirm Scripts Are Actually Updated

```powershell
# On RDP server, run:
Get-ChildItem "C:\HPD ESRI\04_Scripts" | Sort LastWriteTime -Descending | Select -First 10 Name,LastWriteTime,Length
```

**Expected:**
- Timestamps should be: **2026-02-15 22:22:58 - 22:22:59**
- Top files should include: complete_backfill_simplified.py, publish_with_xy_coordinates.py, etc.

**Red Flag:**
- If timestamps are old (before 2026-02-15), deployment didn't work
- If key scripts missing, check backup folder

---

### 2. Confirm Task Scheduler Entrypoint

```powershell
# Check what the scheduled task is calling:
$task = Get-ScheduledTask -TaskName "LawSoftESRICADExport"
$task.Actions[0].Execute
$task.Actions[0].Arguments
```

**Expected:**
- Execute: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`
- Arguments should reference: `C:\HPD ESRI\04_Scripts\Invoke-CADBackfillPublish.ps1`

**Red Flag:**
- If it calls `C:\HPD ESRI\Publish Call Data.py` (root-level), update task to call PS1 orchestrator
- If it calls old paths, scheduled task won't use new scripts

---

### 3. Confirm Output Directory Exists and Is Writable

```powershell
# Check _out directory exists:
Test-Path "C:\HPD ESRI\04_Scripts\_out"

# Try to write a test file:
"test" | Out-File "C:\HPD ESRI\04_Scripts\_out\_test.txt"
Remove-Item "C:\HPD ESRI\04_Scripts\_out\_test.txt"
```

**Expected:**
- Returns `True`
- Test file writes successfully

**Red Flag:**
- If directory missing, create it: `New-Item -Path "C:\HPD ESRI\04_Scripts\_out" -ItemType Directory`
- If write fails, check permissions

---

### 4. Confirm Staging Heartbeat Path Exists

```powershell
# Check staging directory structure:
Test-Path "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING"

# Create heartbeat file if missing:
if (-not (Test-Path "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\heartbeat.txt")) {
    "Initial heartbeat" | Out-File "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\heartbeat.txt"
}
```

**Expected:**
- Staging directory exists
- Heartbeat file can be created/updated

**Red Flag:**
- If directory missing, watchdog monitoring will fail
- Create directory: `New-Item -Path "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING" -ItemType Directory`

---

### 5. Confirm Runtime Scripts Still Include Dependencies

```powershell
# Check key orchestrator exists:
Test-Path "C:\HPD ESRI\04_Scripts\Invoke-CADBackfillPublish.ps1"

# Check Python runner exists:
Test-Path "C:\HPD ESRI\04_Scripts\run_publish_call_data.py"

# Check config exists:
Test-Path "C:\HPD ESRI\04_Scripts\config.json"
```

**Expected:**
- All return `True`

**Red Flag:**
- If any missing, restore from backup or redeploy

---

## ⚠️ Yellow Flags (Known but Acceptable)

### 1. Cached Credentials Deploy
- **Status:** Working reliably for current Windows session
- **Limitation:** Fragile if:
  - Run under different Windows account
  - Password changes
  - Admin share behaves differently
- **Mitigation:** Keep fallback `-Credential` mode for future (not urgent)

### 2. Docs Moved to /docs in Git
- **Status:** Totally fine - runtime doesn't expect docs in specific location
- **Verification:** Confirm nothing on RDP expects docs at root (already checked - all clear)

---

## 🚀 Next Steps (Fastest Path to Geometry Fix)

### Recommended Order: Prompt B First, Then Prompt A

**Why B before A:**
- Prompt B creates the "fail-safe gate" (monitor + job failure)
- Testing Prompt A patches safely requires the gate to be in place
- Can't accidentally re-break geometry during testing

### Prompt B Implementation (Monitor + Gating)

**File to Create:** `C:\HPD ESRI\04_Scripts\monitor_dashboard_health.py`

**Where to Insert Monitor Call:** In `Invoke-CADBackfillPublish.ps1`, after line 518:

```powershell
# Current code (line 509-519):
& $propyPath $runnerScript $ConfigPath

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "    [ERROR] Publish Call Data tool failed with exit code $LASTEXITCODE" -ForegroundColor Red
    throw "Publish tool failed"
}

Write-Host ""
Write-Host "    [OK] Publish Call Data completed successfully" -ForegroundColor Green

# INSERT HERE: Post-publish validation
Write-Host ""
Write-Host "[6.5] Running post-publish validation..." -ForegroundColor Yellow

$monitorScript = Join-Path $scriptsDir "monitor_dashboard_health.py"
Write-Host "    Command: $propyPath $monitorScript" -ForegroundColor Cyan

& $propyPath $monitorScript

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "    [ERROR] Post-publish validation failed (exit code $LASTEXITCODE)" -ForegroundColor Red
    Write-Host "    Dashboard may have geometry or schema issues" -ForegroundColor Red
    throw "Post-publish validation failed"
}

Write-Host ""
Write-Host "    [OK] Dashboard health check passed" -ForegroundColor Green
```

**Monitor Script Requirements (from original spec):**
- Use ArcGIS API for Python (GIS('pro'))
- Return: record count, WKID, % null geometry (sample 1000 features)
- Exit non-zero if:
  - Geometry % < 99%
  - WKID ≠ 3857

**Staged Mode:** Same insertion point exists around line 310-325 in the watchdog monitoring section (after successful batch)

---

## 📊 Deployment Log Location

**Local Log:**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\deploy_logs\Deploy_20260215_222258.log
```

**Backup Location (on RDP):**
```
\\HPD2022LAWSOFT\C$\HPD ESRI\00_Backups\ScriptsDeploy_20260215_222258\
```

---

## 🔧 Quick Fixes for Common Issues

### Issue: "Scripts didn't update"
```powershell
# Check if network path is still accessible:
Test-Path "\\HPD2022LAWSOFT\C$\HPD ESRI\04_Scripts"

# If false, reconnect via File Explorer:
# 1. Open: \\HPD2022LAWSOFT\C$
# 2. Re-run: .\Deploy-ToRDP-Simple.ps1
```

### Issue: "Scheduled task not calling new scripts"
```powershell
# Update task action to call PS1 orchestrator:
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"C:\HPD ESRI\04_Scripts\Invoke-CADBackfillPublish.ps1`" -BackfillFile `"C:\HPD ESRI\03_Data\CAD\Default\ESRI_CADExport.xlsx`""

Set-ScheduledTask -TaskName "LawSoftESRICADExport" -Action $action
```

### Issue: "Heartbeat monitoring fails"
```powershell
# Create staging directory and heartbeat:
New-Item -Path "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING" -ItemType Directory -Force
"Initial heartbeat $(Get-Date)" | Out-File "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\heartbeat.txt"
```

---

## ✅ Deployment Success Indicators

- [x] 33 scripts deployed with correct timestamps
- [x] 3 documentation files deployed
- [x] Backup created successfully
- [x] Local Git committed
- [x] Deployment log saved
- [ ] RDP verification completed (run checklist above)
- [ ] Scheduled task validated (if applicable)
- [ ] Staging directories confirmed
- [ ] Monitor script created (Prompt B)
- [ ] Patches applied (Prompt A)

---

## 📝 Notes

**Deployment Method:** Leverages Windows cached credentials (File Explorer auth)

**Safety:** Automatic backup before deployment ensures rollback capability

**Repeatability:** Script can be run multiple times safely (backup + overwrite)

**Next Deploy:** Run `.\Deploy-ToRDP-Simple.ps1` from local repo root after implementing Prompt B monitor

