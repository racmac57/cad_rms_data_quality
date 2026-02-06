# ============================================================================
# Generate-BackfillReport.ps1
# Generate CSV audit log from completed batch files
# ============================================================================
#
# Purpose:
#   Generates CSV audit log of all completed batches with timestamps,
#   record counts, and duration. Provides verification summary for
#   post-execution analysis.
#
# Features:
#   - Reads from Completed/ folder
#   - Extracts record counts from batch filenames
#   - Calculates batch durations from file timestamps
#   - Generates CSV audit log
#   - Provides summary statistics
#
# Usage:
#   .\Generate-BackfillReport.ps1
#   .\Generate-BackfillReport.ps1 -BatchFolder "C:\custom\path"
#   .\Generate-BackfillReport.ps1 -OutputPath "C:\custom\report.csv"
#
# Author: R. A. Carucci
# Created: 2026-02-06
# Version: 1.0.0
#
# ============================================================================

[CmdletBinding()]
param(
    [Parameter()]
    [string]$BatchFolder = "C:\HPD ESRI\03_Data\CAD\Backfill\Batches",

    [Parameter()]
    [string]$OutputPath = "C:\HPD ESRI\05_Reports\backfill_audit_log.csv"
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

function Get-BatchRecordCount {
    <#
    .SYNOPSIS
    Extract record count from batch filename
    .EXAMPLE
    Get-BatchRecordCount "BATCH_01_records_0_50000.xlsx" returns 50000
    #>
    param([string]$Filename)

    if ($Filename -match "records_(\d+)_(\d+)") {
        $startIdx = [int]$matches[1]
        $endIdx = [int]$matches[2]
        return ($endIdx - $startIdx)
    }

    # Fallback: try to read Excel file
    return $null
}

function Get-BatchNumber {
    <#
    .SYNOPSIS
    Extract batch number from filename
    .EXAMPLE
    Get-BatchNumber "BATCH_01_records_0_50000.xlsx" returns 1
    #>
    param([string]$Filename)

    if ($Filename -match "BATCH_(\d+)") {
        return [int]$matches[1]
    }

    return $null
}

function Get-CompletedBatches {
    param([string]$CompletedDir)

    if (-not (Test-Path $CompletedDir)) {
        throw "Completed directory not found: $CompletedDir"
    }

    $batchFiles = Get-ChildItem -Path $CompletedDir -Filter "BATCH_*.xlsx" | Sort-Object Name

    if ($batchFiles.Count -eq 0) {
        Write-Host "  [WARNING] No completed batch files found in: $CompletedDir" -ForegroundColor Yellow
        return @()
    }

    $batches = @()

    foreach ($file in $batchFiles) {
        $batchNumber = Get-BatchNumber -Filename $file.Name
        $recordCount = Get-BatchRecordCount -Filename $file.Name

        $batch = [PSCustomObject]@{
            BatchNumber = $batchNumber
            Filename = $file.Name
            RecordCount = $recordCount
            CompletedTime = $file.LastWriteTime
            FileSizeMB = [math]::Round($file.Length / 1MB, 2)
        }

        $batches += $batch
    }

    return $batches
}

function Calculate-BatchDurations {
    param([array]$Batches)

    # Sort by batch number
    $sortedBatches = $Batches | Sort-Object BatchNumber

    for ($i = 0; $i -lt $sortedBatches.Count; $i++) {
        $currentBatch = $sortedBatches[$i]

        if ($i -eq 0) {
            # First batch - no previous batch to compare
            $currentBatch | Add-Member -MemberType NoteProperty -Name "DurationSeconds" -Value $null
            $currentBatch | Add-Member -MemberType NoteProperty -Name "DurationFormatted" -Value "N/A (First batch)"
        } else {
            # Calculate duration from previous batch
            $previousBatch = $sortedBatches[$i - 1]
            $duration = ($currentBatch.CompletedTime - $previousBatch.CompletedTime).TotalSeconds

            $currentBatch | Add-Member -MemberType NoteProperty -Name "DurationSeconds" -Value ([math]::Round($duration, 0))

            # Format duration
            $minutes = [math]::Floor($duration / 60)
            $seconds = [math]::Round($duration % 60, 0)
            $currentBatch | Add-Member -MemberType NoteProperty -Name "DurationFormatted" -Value ("{0:D2}:{1:D2}" -f $minutes, $seconds)
        }
    }

    return $sortedBatches
}

function Export-AuditLog {
    param(
        [array]$Batches,
        [string]$OutputPath
    )

    # Create output directory if needed
    $outputDir = Split-Path $OutputPath -Parent
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }

    # Export to CSV
    $Batches | Select-Object `
        BatchNumber,
        Filename,
        RecordCount,
        CompletedTime,
        DurationSeconds,
        DurationFormatted,
        FileSizeMB |
        Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8

    Write-Host "  [SUCCESS] Audit log exported to: $OutputPath" -ForegroundColor Green
}

function Show-Summary {
    param([array]$Batches)

    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "BACKFILL EXECUTION SUMMARY" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""

    $totalRecords = ($Batches | Measure-Object -Property RecordCount -Sum).Sum
    $totalBatches = $Batches.Count

    # Calculate total duration (first to last batch)
    $sortedBatches = $Batches | Sort-Object CompletedTime
    if ($sortedBatches.Count -gt 1) {
        $totalDuration = ($sortedBatches[-1].CompletedTime - $sortedBatches[0].CompletedTime).TotalMinutes
        $avgDuration = ($Batches | Where-Object { $_.DurationSeconds -ne $null } | Measure-Object -Property DurationSeconds -Average).Average
    } else {
        $totalDuration = 0
        $avgDuration = 0
    }

    Write-Host "Total batches completed: $totalBatches" -ForegroundColor Green
    Write-Host "Total records: $($totalRecords.ToString('N0'))" -ForegroundColor Green

    if ($totalDuration -gt 0) {
        Write-Host ("Total execution time: {0:N1} minutes" -f $totalDuration) -ForegroundColor Green
        Write-Host ("Average batch duration: {0:N0} seconds" -f $avgDuration) -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "First batch completed: $($sortedBatches[0].CompletedTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
    Write-Host "Last batch completed: $($sortedBatches[-1].CompletedTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray

    # Show batch table
    Write-Host ""
    Write-Host "Batch Details:" -ForegroundColor Yellow
    Write-Host ""

    $Batches | Sort-Object BatchNumber | ForEach-Object {
        Write-Host ("  Batch {0:D2}: {1,7:N0} records | Completed: {2} | Duration: {3}" -f `
            $_.BatchNumber,
            $_.RecordCount,
            $_.CompletedTime.ToString("yyyy-MM-dd HH:mm:ss"),
            $_.DurationFormatted
        ) -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-Header "BACKFILL AUDIT LOG GENERATOR"
Write-Host "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

try {
    # Check batch folder exists
    if (-not (Test-Path $BatchFolder)) {
        throw "Batch folder not found: $BatchFolder"
    }

    $completedDir = Join-Path $BatchFolder "Completed"

    Write-Host "[1/4] Reading completed batches from: $completedDir"
    $batches = Get-CompletedBatches -CompletedDir $completedDir

    if ($batches.Count -eq 0) {
        Write-Host ""
        Write-Host "No completed batches found - nothing to report" -ForegroundColor Yellow
        exit 0
    }

    Write-Host "      Found $($batches.Count) completed batch(es)" -ForegroundColor Gray

    Write-Host ""
    Write-Host "[2/4] Calculating batch durations"
    $batches = Calculate-BatchDurations -Batches $batches
    Write-Host "      Duration calculations complete" -ForegroundColor Gray

    Write-Host ""
    Write-Host "[3/4] Exporting audit log"
    Export-AuditLog -Batches $batches -OutputPath $OutputPath

    Write-Host ""
    Write-Host "[4/4] Generating summary"
    Show-Summary -Batches $batches

    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Green
    Write-Host "REPORT GENERATION COMPLETE" -ForegroundColor Green
    Write-Host ("=" * 70) -ForegroundColor Green
    Write-Host "Audit log: $OutputPath" -ForegroundColor Green
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Red
    Write-Host "REPORT GENERATION FAILED" -ForegroundColor Red
    Write-Host ("=" * 70) -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    exit 1
}
