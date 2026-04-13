---
name: esri-pipeline-status
description: Generate a PowerShell block to check nightly ESRI publish-pipeline health on the RDP server -- last run time, LastTaskResult, and recent log status for the Call Data and Crime Data tasks.
disable-model-invocation: true
allowed-tools: Read
---

# ESRI Pipeline Status -- Nightly Publish Health Check

Emit a PowerShell block (paste on the RDP server) that reports the health of both
nightly ESRI publish pipelines without needing to open Task Scheduler.

## Trigger

`/esri-pipeline-status` or "check pipeline health".

## Key Constants

```
Log path    : C:\Users\administrator.HPD\AppData\Local\ESRI\ArcGISPro\Geoprocessing\ScheduledTools\Logs\
Task names  : "Publish Call Data_2026_NEW"  and  "Publish Crime Data_2026"
Status codes in logs:
  4 = success
  5 = license failure (wrong account / not signed in to AGOL)
  0 = unknown / incomplete run
```

`LastTaskResult` on the task itself: `0` means success, non-zero means the task
runner errored (distinct from the in-log `status` value).

## Output -- PowerShell Block (paste on the RDP)

```powershell
# === ESRI Nightly Pipeline Status ===
$LogRoot = "C:\Users\administrator.HPD\AppData\Local\ESRI\ArcGISPro\Geoprocessing\ScheduledTools\Logs"
$Tasks   = @("Publish Call Data_2026_NEW", "Publish Crime Data_2026")

$rows = foreach ($t in $Tasks) {
    $info = Get-ScheduledTaskInfo -TaskName $t -ErrorAction SilentlyContinue

    # Find the newest log file that mentions this task
    $log = Get-ChildItem -Path $LogRoot -Filter *.log -ErrorAction SilentlyContinue |
           Sort-Object LastWriteTime -Descending |
           Where-Object { (Get-Content $_.FullName -TotalCount 20 -ErrorAction SilentlyContinue) -match [regex]::Escape($t) } |
           Select-Object -First 1

    $logStatus = "n/a"
    $recordCount = "n/a"
    if ($log) {
        $content = Get-Content $log.FullName -ErrorAction SilentlyContinue
        $m = $content | Select-String -Pattern 'status["'']?\s*[:=]\s*(\d+)' | Select-Object -Last 1
        if ($m) { $logStatus = $m.Matches[0].Groups[1].Value }
        $rc = $content | Select-String -Pattern '(\d[\d,]{2,})\s+(records|features|rows)' | Select-Object -Last 1
        if ($rc) { $recordCount = $rc.Matches[0].Groups[1].Value }
    }

    [pscustomobject]@{
        Task           = $t
        LastRunTime    = if ($info) { $info.LastRunTime } else { "n/a" }
        LastTaskResult = if ($info) { $info.LastTaskResult } else { "n/a" }
        LogStatus      = $logStatus
        Records        = $recordCount
        LogFile        = if ($log) { $log.Name } else { "(none found)" }
    }
}

$rows | Format-Table -AutoSize

Write-Host ""
Write-Host "Interpretation:" -ForegroundColor Yellow
Write-Host "  LastTaskResult = 0  : task runner completed OK"
Write-Host "  LogStatus      = 4  : publish succeeded"
Write-Host "  LogStatus      = 5  : license failure (check AGOL sign-in on the task account)"
Write-Host "  LogStatus      = 0  : incomplete -- investigate the log file listed above"
```

## Notes

- The "Records" column is best-effort — it scrapes the newest number-followed-by
  "records/features/rows" from the log. Treat it as a sanity check, not authoritative.
- If the log search returns no file, the task likely hasn't run yet or its logs were
  rotated out. Confirm `LastRunTime` before alarming.
- A `LogStatus` of 5 is the most common failure mode and almost always means the
  scheduled-task user is not signed in to AGOL in ArcGIS Pro on that account.
- For a deeper dive into a specific run, open the log file named in the `LogFile`
  column under `$LogRoot`.
