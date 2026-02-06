# ============================================================================
# Resume-CADBackfill.ps1
# Resume staged backfill from checkpoint after watchdog kill or manual stop
# ============================================================================
#
# Purpose:
#   Post-watchdog recovery with stale file cleanup, marker restoration,
#   and batch resumption logic. Automatically detects remaining batches
#   and resumes from last successful checkpoint.
#
# Features:
#   - Detects remaining batches in folder (not in Completed/)
#   - Watchdog Recovery: Removes stale heartbeat.txt, _LOCK.txt, staging files
#   - Validates is_first_batch.txt marker exists (prevents accidental overwrite)
#   - Recreates marker if missing mid-sequence (batch number detection)
#   - Safety prompt before execution
#
# Usage:
#   .\Resume-CADBackfill.ps1
#   .\Resume-CADBackfill.ps1 -Verbose
#   .\Resume-CADBackfill.ps1 -WhatIf
#
# Author: R. A. Carucci
# Created: 2026-02-06
# Version: 1.0.0
#
# ============================================================================

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter()]
    [string]$BatchFolder = "C:\HPD ESRI\03_Data\CAD\Backfill\Batches",

    [Parameter()]
    [string]$ConfigPath = "C:\HPD ESRI\04_Scripts\config.json"
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

function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "[$Message]" -ForegroundColor Yellow
}

function Test-MarkerFile {
    param([string]$MarkerPath)

    if (Test-Path $MarkerPath) {
        $markerContent = Get-Content $MarkerPath -Raw
        Write-Host "  [PASS] Marker file exists" -ForegroundColor Green
        Write-Host "         Content: $markerContent" -ForegroundColor Gray
        return $true
    } else {
        Write-Host "  [WARNING] Marker file missing: $MarkerPath" -ForegroundColor Yellow
        return $false
    }
}

function Remove-StaleFiles {
    <#
    .SYNOPSIS
    Watchdog Recovery: Remove stale files after process kill
    #>
    param(
        [string]$StagingDir
    )

    Write-Section "Watchdog Recovery: Removing Stale Files"

    $staleFiles = @(
        (Join-Path $StagingDir "heartbeat.txt"),
        (Join-Path $StagingDir "_LOCK.txt"),
        (Join-Path $StagingDir "ESRI_CADExport.xlsx")
    )

    $removedCount = 0

    foreach ($file in $staleFiles) {
        if (Test-Path $file) {
            if ($PSCmdlet.ShouldProcess($file, "Remove stale file")) {
                Remove-Item -Path $file -Force -ErrorAction SilentlyContinue
                Write-Host "  [CLEANUP] Removed: $(Split-Path $file -Leaf)" -ForegroundColor Green
                $removedCount++
            }
        }
    }

    if ($removedCount -eq 0) {
        Write-Host "  [INFO] No stale files found - environment is clean" -ForegroundColor Gray
    } else {
        Write-Host "  [INFO] Removed $removedCount stale file(s)" -ForegroundColor Green
    }
}

function Get-RemainingBatches {
    param(
        [string]$BatchFolder
    )

    $completedDir = Join-Path $BatchFolder "Completed"

    # Get all batch files in main folder
    $allBatches = Get-ChildItem -Path $BatchFolder -Filter "BATCH_*.xlsx" | Sort-Object Name

    # Get completed batches
    $completedBatches = @()
    if (Test-Path $completedDir) {
        $completedBatches = Get-ChildItem -Path $completedDir -Filter "BATCH_*.xlsx" | ForEach-Object { $_.Name }
    }

    # Filter remaining batches
    $remainingBatches = $allBatches | Where-Object { $_.Name -notin $completedBatches }

    return $remainingBatches
}

function Get-LastCompletedBatchNumber {
    param(
        [string]$BatchFolder
    )

    $completedDir = Join-Path $BatchFolder "Completed"

    if (-not (Test-Path $completedDir)) {
        return 0
    }

    $completedBatches = Get-ChildItem -Path $completedDir -Filter "BATCH_*.xlsx"

    if ($completedBatches.Count -eq 0) {
        return 0
    }

    # Extract batch numbers and return max
    $batchNumbers = $completedBatches | ForEach-Object {
        if ($_.Name -match "BATCH_(\d+)") {
            [int]$matches[1]
        }
    }

    return ($batchNumbers | Measure-Object -Maximum).Maximum
}

function Restore-MarkerFile {
    <#
    .SYNOPSIS
    Recreate is_first_batch.txt if missing mid-sequence
    #>
    param(
        [string]$MarkerPath,
        [int]$LastCompletedBatch
    )

    Write-Section "Marker File Restoration"

    if (Test-Path $MarkerPath) {
        Write-Host "  [PASS] Marker file exists - no restoration needed" -ForegroundColor Green
        return
    }

    if ($LastCompletedBatch -eq 0) {
        Write-Host "  [ERROR] No completed batches found - cannot determine state" -ForegroundColor Red
        Write-Host "          This appears to be a fresh start. Use Invoke-CADBackfillPublish.ps1 instead." -ForegroundColor Red
        throw "No completed batches found"
    }

    # Recreate marker
    Write-Host "  [WARNING] Marker file missing - recreating from completed batch info" -ForegroundColor Yellow

    $markerContent = @"
FIRST_BATCH_COMPLETE
Batch 01 completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Marker restored by Resume-CADBackfill.ps1
Last completed batch: $LastCompletedBatch
"@

    if ($PSCmdlet.ShouldProcess($MarkerPath, "Restore marker file")) {
        Set-Content -Path $MarkerPath -Value $markerContent -Force
        Write-Host "  [RESTORED] Marker file recreated at: $MarkerPath" -ForegroundColor Green
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-Header "CAD BACKFILL RESUME SCRIPT"
Write-Host "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

try {
    # Load configuration
    Write-Section "Loading Configuration"

    if (-not (Test-Path $ConfigPath)) {
        throw "Configuration file not found: $ConfigPath"
    }

    $config = Get-Content $ConfigPath | ConvertFrom-Json
    $stagingDir = $config.paths.staging_dir
    $markerPath = Join-Path $stagingDir "is_first_batch.txt"

    Write-Host "  Config: $ConfigPath" -ForegroundColor Gray
    Write-Host "  Batch Folder: $BatchFolder" -ForegroundColor Gray
    Write-Host "  Staging Dir: $stagingDir" -ForegroundColor Gray

    # Check batch folder exists
    if (-not (Test-Path $BatchFolder)) {
        throw "Batch folder not found: $BatchFolder"
    }

    # Step 1: Watchdog Recovery - Remove stale files
    Remove-StaleFiles -StagingDir $stagingDir

    # Step 2: Detect remaining batches
    Write-Section "Detecting Remaining Batches"

    $remainingBatches = Get-RemainingBatches -BatchFolder $BatchFolder
    $lastCompletedBatch = Get-LastCompletedBatchNumber -BatchFolder $BatchFolder

    Write-Host "  Last completed batch: $lastCompletedBatch" -ForegroundColor Gray
    Write-Host "  Remaining batches: $($remainingBatches.Count)" -ForegroundColor Gray

    if ($remainingBatches.Count -eq 0) {
        Write-Host ""
        Write-Host "  [INFO] No remaining batches found - backfill appears complete!" -ForegroundColor Green
        Write-Host "         Run Validate-CADBackfillCount.py to verify record count." -ForegroundColor Green
        exit 0
    }

    Write-Host ""
    Write-Host "  Batches to process:" -ForegroundColor Yellow
    foreach ($batch in $remainingBatches | Select-Object -First 5) {
        Write-Host "    - $($batch.Name)" -ForegroundColor Gray
    }
    if ($remainingBatches.Count -gt 5) {
        Write-Host "    ... and $($remainingBatches.Count - 5) more" -ForegroundColor Gray
    }

    # Step 3: Validate/Restore marker file
    Restore-MarkerFile -MarkerPath $markerPath -LastCompletedBatch $lastCompletedBatch

    # Step 4: Safety prompt
    Write-Section "Resume Confirmation"

    Write-Host "  You are about to resume the staged backfill from Batch $($lastCompletedBatch + 1)." -ForegroundColor Yellow
    Write-Host "  This will process $($remainingBatches.Count) remaining batch(es)." -ForegroundColor Yellow
    Write-Host ""

    if (-not $PSCmdlet.ShouldProcess("Resume backfill", "Confirm")) {
        if (-not $WhatIfPreference) {
            $response = Read-Host "  Type YES to resume backfill"

            if ($response -ne "YES") {
                Write-Host ""
                Write-Host "  [ABORT] Resume cancelled by user" -ForegroundColor Red
                exit 1
            }
        }
    }

    # Step 5: Call main orchestrator in staged mode
    Write-Section "Calling Main Orchestrator"

    $orchestratorPath = Join-Path (Split-Path $ConfigPath) "Invoke-CADBackfillPublish.ps1"

    if (-not (Test-Path $orchestratorPath)) {
        throw "Orchestrator script not found: $orchestratorPath"
    }

    Write-Host "  Orchestrator: $orchestratorPath" -ForegroundColor Gray
    Write-Host "  Mode: Staged (Resume)" -ForegroundColor Gray
    Write-Host ""

    if ($PSCmdlet.ShouldProcess("Invoke-CADBackfillPublish.ps1", "Execute")) {
        & $orchestratorPath -Staged -BatchFolder $BatchFolder -ResumeFromCheckpoint
    }

    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Green
    Write-Host "RESUME COMPLETE" -ForegroundColor Green
    Write-Host ("=" * 70) -ForegroundColor Green

} catch {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Red
    Write-Host "RESUME FAILED" -ForegroundColor Red
    Write-Host ("=" * 70) -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    exit 1
}
