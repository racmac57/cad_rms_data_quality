---
name: esri-backfill
description: Generate a complete PowerShell backfill block for a monthly CAD file (backup -> stage -> run task -> wait -> restore -> verify) plus a post-run ArcPy gap-check block. Ready to paste on the RDP server.
disable-model-invocation: true
argument-hint: [source-xlsx] [month-label]
allowed-tools: Read Grep Glob
---

# ESRI Backfill -- Generate Monthly Backfill PowerShell

Produce a ready-to-paste PowerShell block that drives a monthly CAD backfill against
the `Publish Call Data_2026_NEW` scheduled task, plus a second ArcPy block for
post-run gap verification.

## Trigger

`/esri-backfill $ARGUMENTS` or "generate backfill script".

- `$0` -- source file path or filename (required)
- `$1` -- optional month label (e.g. "April 2026"); inferred from filename if omitted

Example invocations:
```
/esri-backfill 2026_04_CAD_FIXED.xlsx
/esri-backfill \\tsclient\C\Users\carucci_r\OneDrive - City of Hackensack\Desktop\2026_04_CAD_FIXED.xlsx "April 2026"
```

## Inputs to Gather

Ask the user (or infer from filename) before generating:

1. **Source file path** — one of:
   - Local desktop (use `\\tsclient\C\Users\carucci_r\OneDrive - City of Hackensack\Desktop\<file>`)
   - Already in `_STAGING` on the server
2. **Month label** — e.g. "April 2026" (for status messages; infer from filename like `2026_04_*`)

## Key Constants (hardcoded)

```
FileMaker live export : C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx
Scheduled task name   : Publish Call Data_2026_NEW
Staging folder        : C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\
tsclient desktop root : \\tsclient\C\Users\carucci_r\OneDrive - City of Hackensack\
```

## Output -- PowerShell Block (paste on the RDP)

Emit this as a fenced `powershell` code block, substituting `$0` and
`$1`:

```powershell
# === CAD Backfill: $1 ===
$Source    = "$0"
$LiveExport = "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx"
$BackupDir = "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING"
$Stamp     = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup    = Join-Path $BackupDir "ESRI_CADExport_LIVE_BACKUP_$Stamp.xlsx"
$TaskName  = "Publish Call Data_2026_NEW"

# Step 1: Backup live export
Write-Host "[1/6] Backing up live export -> $Backup" -ForegroundColor Cyan
Copy-Item -Path $LiveExport -Destination $Backup -Force

# Step 2: Stage the monthly file over the live export
Write-Host "[2/6] Staging $Source -> $LiveExport" -ForegroundColor Cyan
Copy-Item -Path $Source -Destination $LiveExport -Force

# Step 3: Kick off scheduled task
Write-Host "[3/6] Starting task: $TaskName" -ForegroundColor Cyan
Start-ScheduledTask -TaskName $TaskName

# Step 4: Poll until the task is idle
Write-Host "[4/6] Waiting for task to complete..." -ForegroundColor Cyan
do {
    Start-Sleep -Seconds 30
    $info  = Get-ScheduledTaskInfo -TaskName $TaskName
    $state = (Get-ScheduledTask -TaskName $TaskName).State
    Write-Host ("  {0}  state={1}  lastResult={2}" -f (Get-Date -Format HH:mm:ss), $state, $info.LastTaskResult)
} while ($state -eq "Running")

# Step 5: Report result
$result = (Get-ScheduledTaskInfo -TaskName $TaskName).LastTaskResult
if ($result -eq 0) {
    Write-Host "[5/6] Task completed successfully (LastTaskResult=0)" -ForegroundColor Green
} else {
    Write-Host "[5/6] Task returned non-zero: $result -- INVESTIGATE logs" -ForegroundColor Red
}

# Step 6: Restore the live export so nightly runs are not disturbed
Write-Host "[6/6] Restoring live export from backup" -ForegroundColor Cyan
Copy-Item -Path $Backup -Destination $LiveExport -Force

Write-Host "=== Done: $1 backfill finished at $(Get-Date -Format HH:mm:ss) ===" -ForegroundColor Yellow
```

## Output -- ArcPy Gap Check (paste in ArcGIS Pro Python window)

Also emit the gap check from the `esri-gap-check` skill, defaulting to a window that
covers the month that was just backfilled (plus a 7-day buffer on either side). If
the user just ran April 2026, default `FROM=2026-03-25`, `TO=2026-05-07`.

See `.claude/skills/esri-gap-check/SKILL.md` for the ArcPy block; produce it here
inline so the user has both steps in one response.

## Notes

- Always back up the live export first — the nightly task depends on it being present.
- Always restore it at the end, even on failure (the `Copy-Item` in step 6 is intentional
  after the `if/else` so it runs regardless of the result code).
- If the user provides a file still on their desktop, prefix with
  `\\tsclient\C\Users\carucci_r\OneDrive - City of Hackensack\` so RDP can see it.
- `LastTaskResult=0` means success. Non-zero requires checking the task log under
  `C:\Users\administrator.HPD\AppData\Local\ESRI\ArcGISPro\Geoprocessing\ScheduledTools\Logs\`.
