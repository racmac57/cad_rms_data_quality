# ============================================================================
# Analyze-WatchdogHangs.ps1
# Parse backfill logs for heartbeat stalls and generate diagnostic report
# ============================================================================
#
# Purpose:
#   Scans backfill execution logs for heartbeat stalls (silent hangs),
#   identifies "last known good" timestamp before hang, calculates
#   heartbeat delta (time frozen), and validates cooling period effectiveness.
#
# Features:
#   - Scans log files for heartbeat stall events
#   - Calculates hang duration (time between last heartbeat and watchdog kill)
#   - Identifies which batches triggered hangs
#   - Generates diagnostic report for feature 564,916 investigation
#   - Validates cooling period effectiveness
#
# Usage:
#   .\Analyze-WatchdogHangs.ps1
#   .\Analyze-WatchdogHangs.ps1 -LogPath "C:\custom\backfill.log"
#   .\Analyze-WatchdogHangs.ps1 -Verbose
#
# Author: R. A. Carucci
# Created: 2026-02-06
# Version: 1.0.0
#
# ============================================================================

[CmdletBinding()]
param(
    [Parameter()]
    [string]$LogPath = "C:\HPD ESRI\05_Reports\backfill_execution.log",

    [Parameter()]
    [string]$OutputPath = "C:\HPD ESRI\05_Reports\watchdog_hang_analysis.txt"
)

$ErrorActionPreference = "Stop"

# ============================================================================
# FUNCTIONS
# ============================================================================

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Parse-LogFile {
    param([string]$LogPath)

    Write-Host "[1/4] Parsing log file: $LogPath"

    if (-not (Test-Path $LogPath)) {
        throw "Log file not found: $LogPath"
    }

    $logContent = Get-Content $LogPath -Raw

    # Extract events
    $events = @()
    $lines = $logContent -split "`n"

    foreach ($line in $lines) {
        # Match heartbeat updates
        if ($line -match "^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Heartbeat updated") {
            $events += [PSCustomObject]@{
                Timestamp = [DateTime]::Parse($matches[1])
                EventType = "HeartbeatUpdate"
                Message = $line
            }
        }

        # Match watchdog kills
        if ($line -match "^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*CRITICAL.*Heartbeat stalled") {
            $events += [PSCustomObject]@{
                Timestamp = [DateTime]::Parse($matches[1])
                EventType = "WatchdogKill"
                Message = $line
            }
        }

        # Match batch start
        if ($line -match "^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Processing batch (\d+)") {
            $events += [PSCustomObject]@{
                Timestamp = [DateTime]::Parse($matches[1])
                EventType = "BatchStart"
                BatchNumber = [int]$matches[2]
                Message = $line
            }
        }

        # Match batch completion
        if ($line -match "^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Batch (\d+) completed successfully") {
            $events += [PSCustomObject]@{
                Timestamp = [DateTime]::Parse($matches[1])
                EventType = "BatchComplete"
                BatchNumber = [int]$matches[2]
                Message = $line
            }
        }
    }

    Write-Host "      Found $($events.Count) relevant event(s)" -ForegroundColor Gray

    return $events | Sort-Object Timestamp
}

function Detect-Hangs {
    param([array]$Events)

    Write-Host ""
    Write-Host "[2/4] Detecting heartbeat stalls"

    $hangs = @()
    $lastHeartbeat = $null
    $currentBatch = $null

    foreach ($event in $Events) {
        switch ($event.EventType) {
            "BatchStart" {
                $currentBatch = $event.BatchNumber
            }

            "HeartbeatUpdate" {
                $lastHeartbeat = $event
            }

            "WatchdogKill" {
                if ($lastHeartbeat) {
                    $hangDuration = ($event.Timestamp - $lastHeartbeat.Timestamp).TotalSeconds

                    $hang = [PSCustomObject]@{
                        BatchNumber = $currentBatch
                        LastHeartbeat = $lastHeartbeat.Timestamp
                        WatchdogKill = $event.Timestamp
                        HangDurationSeconds = [math]::Round($hangDuration, 0)
                        HangDurationFormatted = "{0:D2}:{1:D2}" -f `
                            ([math]::Floor($hangDuration / 60)),
                            ([math]::Round($hangDuration % 60, 0))
                    }

                    $hangs += $hang
                }
            }
        }
    }

    Write-Host "      Detected $($hangs.Count) hang(s)" -ForegroundColor $(if ($hangs.Count -gt 0) { "Yellow" } else { "Green" })

    return $hangs
}

function Calculate-CoolingPeriodStats {
    param([array]$Events)

    Write-Host ""
    Write-Host "[3/4] Calculating cooling period statistics"

    $completions = $Events | Where-Object { $_.EventType -eq "BatchComplete" }

    if ($completions.Count -lt 2) {
        Write-Host "      [INFO] Not enough batch completions to calculate cooling periods" -ForegroundColor Gray
        return $null
    }

    $coolingPeriods = @()

    for ($i = 0; $i -lt $completions.Count - 1; $i++) {
        $current = $completions[$i]
        $next = $completions[$i + 1]

        $coolingSeconds = ($next.Timestamp - $current.Timestamp).TotalSeconds

        $coolingPeriods += [PSCustomObject]@{
            FromBatch = $current.BatchNumber
            ToBatch = $next.BatchNumber
            CoolingSeconds = [math]::Round($coolingSeconds, 0)
        }
    }

    $avgCooling = ($coolingPeriods | Measure-Object -Property CoolingSeconds -Average).Average
    $minCooling = ($coolingPeriods | Measure-Object -Property CoolingSeconds -Minimum).Minimum
    $maxCooling = ($coolingPeriods | Measure-Object -Property CoolingSeconds -Maximum).Maximum

    Write-Host "      Average cooling period: $([math]::Round($avgCooling, 0)) seconds" -ForegroundColor Gray
    Write-Host "      Min: $minCooling seconds | Max: $maxCooling seconds" -ForegroundColor Gray

    return [PSCustomObject]@{
        Periods = $coolingPeriods
        Average = $avgCooling
        Min = $minCooling
        Max = $maxCooling
    }
}

function Generate-DiagnosticReport {
    param(
        [array]$Events,
        [array]$Hangs,
        [object]$CoolingStats,
        [string]$OutputPath
    )

    Write-Host ""
    Write-Host "[4/4] Generating diagnostic report"

    # Build report
    $report = @()
    $report += "=" * 70
    $report += "WATCHDOG HANG ANALYSIS REPORT"
    $report += "=" * 70
    $report += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $report += "Log file: $LogPath"
    $report += ""
    $report += "SUMMARY:"
    $report += "  Total events parsed: $($Events.Count)"
    $report += "  Heartbeat stalls detected: $($Hangs.Count)"
    $report += ""

    if ($Hangs.Count -eq 0) {
        $report += "RESULT: NO HANGS DETECTED"
        $report += "  All batches completed without watchdog intervention."
        $report += "  The staged backfill strategy successfully eliminated the 564,916 hang."
        $report += ""
    } else {
        $report += "HANG DETAILS:"
        $report += ""

        foreach ($hang in $Hangs) {
            $report += "  Batch $($hang.BatchNumber):"
            $report += "    Last heartbeat: $($hang.LastHeartbeat.ToString('yyyy-MM-dd HH:mm:ss'))"
            $report += "    Watchdog kill: $($hang.WatchdogKill.ToString('yyyy-MM-dd HH:mm:ss'))"
            $report += "    Hang duration: $($hang.HangDurationFormatted) ($($hang.HangDurationSeconds) seconds)"
            $report += ""
        }

        # Average hang duration
        $avgHangDuration = ($Hangs | Measure-Object -Property HangDurationSeconds -Average).Average
        $report += "  Average hang duration: $([math]::Round($avgHangDuration, 0)) seconds"
        $report += ""
    }

    # Cooling period analysis
    if ($CoolingStats) {
        $report += "COOLING PERIOD ANALYSIS:"
        $report += "  Average cooling period: $([math]::Round($CoolingStats.Average, 0)) seconds"
        $report += "  Min: $($CoolingStats.Min) seconds"
        $report += "  Max: $($CoolingStats.Max) seconds"
        $report += ""

        if ($CoolingStats.Average -lt 60) {
            $report += "  [WARNING] Average cooling period below 60 seconds"
            $report += "            Consider increasing cooling period in config"
        } elseif ($CoolingStats.Average -gt 120) {
            $report += "  [INFO] Average cooling period above 120 seconds"
            $report += "         Adaptive cooling may have been triggered"
        } else {
            $report += "  [PASS] Cooling period within expected range (60-120 seconds)"
        }

        $report += ""
    }

    # Recommendations
    $report += "RECOMMENDATIONS:"
    $report += ""

    if ($Hangs.Count -eq 0) {
        $report += "  1. Current configuration is optimal"
        $report += "  2. No changes needed to watchdog or cooling settings"
        $report += "  3. Continue using staged backfill strategy for future runs"
    } else {
        $report += "  1. Review batches that triggered hangs for data anomalies"
        $report += "  2. Consider increasing cooling period to $([math]::Ceiling($CoolingStats.Max * 1.2)) seconds"
        $report += "  3. Investigate feature 564,916 specifically if pattern repeats"
        $report += "  4. Monitor network conditions during batch processing"
    }

    $report += ""
    $report += "=" * 70

    # Write report
    $reportText = $report -join "`n"
    Set-Content -Path $OutputPath -Value $reportText -Encoding UTF8

    # Print to console
    Write-Host ""
    $reportText -split "`n" | ForEach-Object {
        if ($_ -match "NO HANGS|PASS") {
            Write-Host $_ -ForegroundColor Green
        } elseif ($_ -match "WARNING") {
            Write-Host $_ -ForegroundColor Yellow
        } else {
            Write-Host $_
        }
    }

    Write-Host ""
    Write-Host "Report saved to: $OutputPath" -ForegroundColor Gray
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-Header "WATCHDOG HANG ANALYZER"
Write-Host "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

try {
    # Parse log file
    $events = Parse-LogFile -LogPath $LogPath

    if ($events.Count -eq 0) {
        Write-Host ""
        Write-Host "[WARNING] No relevant events found in log file" -ForegroundColor Yellow
        Write-Host "          Log may be empty or not from a staged backfill execution" -ForegroundColor Yellow
        exit 1
    }

    # Detect hangs
    $hangs = Detect-Hangs -Events $events

    # Calculate cooling period statistics
    $coolingStats = Calculate-CoolingPeriodStats -Events $events

    # Generate diagnostic report
    Generate-DiagnosticReport `
        -Events $events `
        -Hangs $hangs `
        -CoolingStats $coolingStats `
        -OutputPath $OutputPath

    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Green
    Write-Host "ANALYSIS COMPLETE" -ForegroundColor Green
    Write-Host ("=" * 70) -ForegroundColor Green

} catch {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Red
    Write-Host "ANALYSIS FAILED" -ForegroundColor Red
    Write-Host ("=" * 70) -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    exit 1
}
