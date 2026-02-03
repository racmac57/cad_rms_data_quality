<#
.SYNOPSIS
    Main orchestrator for CAD backfill publish workflow
    
.DESCRIPTION
    Automated end-to-end backfill publish workflow:
    1. Pre-flight checks (lock, tasks, processes, geodatabase)
    2. Create lock file with metadata
    3. Swap backfill data into staging (atomic swap with hash verification)
    4. Run Publish Call Data tool via Python runner
    5. Restore default export to staging (atomic swap)
    6. Remove lock file and cleanup
    
.PARAMETER BackfillFile
    Path to the polished CAD file on the server to publish
    
.PARAMETER ConfigPath
    Path to config.json (default: C:\HPD ESRI\04_Scripts\config.json)
    
.PARAMETER DryRun
    Test mode - shows what would happen without executing
    
.PARAMETER SkipPreFlightChecks
    Force run - bypasses pre-flight checks (use with caution)
    
.PARAMETER NoRestore
    Leave staging as backfill after publish (for testing/debugging)
    
.EXAMPLE
    .\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
    
.EXAMPLE
    .\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" -DryRun
    
.NOTES
    Author: R. A. Carucci
    Date: 2026-02-02
    Version: 1.0.0
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$BackfillFile,
    
    [string]$ConfigPath = "C:\HPD ESRI\04_Scripts\config.json",
    
    [switch]$DryRun,
    [switch]$SkipPreFlightChecks,
    [switch]$NoRestore
)

$ErrorActionPreference = "Stop"
$startTime = Get-Date

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "CAD BACKFILL PUBLISH ORCHESTRATOR" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "Start time: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
Write-Host "Backfill file: $BackfillFile" -ForegroundColor Cyan
Write-Host "Config: $ConfigPath" -ForegroundColor Cyan
Write-Host "Mode: $(if ($DryRun) { 'DRY RUN (testing)' } else { 'LIVE' })" -ForegroundColor $(if ($DryRun) { 'Yellow' } else { 'Green' })
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Load configuration
Write-Host "[1] Loading configuration..." -ForegroundColor Yellow
try {
    $config = Get-Content $ConfigPath | ConvertFrom-Json
    Write-Host "    [OK] Config loaded" -ForegroundColor Green
}
catch {
    Write-Host "    [ERROR] Failed to load config: $_" -ForegroundColor Red
    exit 1
}

$stagingDir = $config.paths.staging_dir
$stagingFile = $config.paths.staging_file
$defaultExport = $config.paths.default_export
$lockFile = $config.paths.lock_file
$runnerScript = Join-Path $config.paths.scripts_dir "run_publish_call_data.py"
$propyPath = $config.paths.propy_python

# Verify files exist
Write-Host "[2] Verifying files..." -ForegroundColor Yellow

if (-not (Test-Path $BackfillFile)) {
    Write-Host "    [ERROR] Backfill file not found: $BackfillFile" -ForegroundColor Red
    exit 2
}

if (-not (Test-Path $defaultExport)) {
    Write-Host "    [ERROR] Default export not found: $defaultExport" -ForegroundColor Red
    exit 2
}

if (-not (Test-Path $runnerScript)) {
    Write-Host "    [ERROR] Python runner script not found: $runnerScript" -ForegroundColor Red
    exit 2
}

Write-Host "    [OK] All required files exist" -ForegroundColor Green

# Pre-flight checks
if (-not $SkipPreFlightChecks) {
    Write-Host ""
    Write-Host "[3] Running pre-flight checks..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "    [DRY RUN] Would run: Test-PublishReadiness.ps1" -ForegroundColor Cyan
    }
    else {
        $preflightScript = Join-Path $config.paths.scripts_dir "Test-PublishReadiness.ps1"
        
        if (Test-Path $preflightScript) {
            & $preflightScript -ConfigPath $ConfigPath -BackfillFile $BackfillFile
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "    [ERROR] Pre-flight checks FAILED. Aborting." -ForegroundColor Red
                exit 3
            }
            Write-Host "    [OK] Pre-flight checks passed" -ForegroundColor Green
        }
        else {
            Write-Host "    ⚠ Pre-flight script not found, skipping checks" -ForegroundColor Yellow
        }
    }
}
else {
    Write-Host ""
    Write-Host "[3] Pre-flight checks SKIPPED (forced run)" -ForegroundColor Yellow
}

# Create lock file with metadata
Write-Host ""
Write-Host "[4] Creating lock file..." -ForegroundColor Yellow

$lockData = @{
    start_time    = (Get-Date).ToString('o')
    user          = $env:USERNAME
    computer      = $env:COMPUTERNAME
    backfill_file = $BackfillFile
    process_id    = $PID
    mode          = $(if ($DryRun) { "DRY_RUN" } else { "LIVE" })
} | ConvertTo-Json

if ($DryRun) {
    Write-Host "    [DRY RUN] Would create lock file: $lockFile" -ForegroundColor Cyan
}
else {
    try {
        $lockData | Out-File $lockFile -Force
        Write-Host "    [OK] Lock file created" -ForegroundColor Green
    }
    catch {
        Write-Host "    [ERROR] Failed to create lock file: $_" -ForegroundColor Red
        exit 3
    }
}

try {
    # STEP 5: Swap IN backfill data (atomic swap with hash verification)
    Write-Host ""
    Write-Host "[5] Swapping backfill data into staging..." -ForegroundColor Yellow
    
    $tempFile = Join-Path $stagingDir "ESRI_CADExport.xlsx.tmp"
    
    if ($DryRun) {
        Write-Host "    [DRY RUN] Would compute source file hash..." -ForegroundColor Cyan
        Write-Host "    [DRY RUN] Would copy: $BackfillFile -> $tempFile" -ForegroundColor Cyan
        Write-Host "    [DRY RUN] Would verify integrity (size + hash)" -ForegroundColor Cyan
        Write-Host "    [DRY RUN] Would rename: $tempFile -> $stagingFile" -ForegroundColor Cyan
    }
    else {
        Write-Host "    Computing source file hash..." -ForegroundColor Cyan
        $backfillHash = (Get-FileHash $BackfillFile -Algorithm SHA256).Hash
        Write-Host "    Source hash: $backfillHash" -ForegroundColor Cyan
        
        Write-Host "    Copying backfill to staging temp..." -ForegroundColor Cyan
        Copy-Item $BackfillFile $tempFile -Force
        
        Write-Host "    Verifying file integrity..." -ForegroundColor Cyan
        $backfillSize = (Get-Item $BackfillFile).Length
        $tempSize = (Get-Item $tempFile).Length
        
        if ($backfillSize -ne $tempSize) {
            Write-Host "    [ERROR] File size mismatch after copy" -ForegroundColor Red
            Write-Host "      Source: $backfillSize bytes" -ForegroundColor Red
            Write-Host "      Temp: $tempSize bytes" -ForegroundColor Red
            throw "File size mismatch after copy"
        }
        
        $tempHash = (Get-FileHash $tempFile -Algorithm SHA256).Hash
        if ($backfillHash -ne $tempHash) {
            Write-Host "    [ERROR] File hash mismatch after copy - file may be corrupted" -ForegroundColor Red
            throw "File hash mismatch after copy"
        }
        
        Write-Host "    [OK] Integrity verified (size + hash match)" -ForegroundColor Green
        
        Write-Host "    Performing atomic swap..." -ForegroundColor Cyan
        Move-Item $tempFile $stagingFile -Force
        Write-Host "    [OK] Backfill data staged successfully" -ForegroundColor Green
    }
    
    # STEP 6: Run ArcGIS Pro publish tool via Python runner
    Write-Host ""
    Write-Host "[6] Running Publish Call Data tool..." -ForegroundColor Yellow
    Write-Host "    This may take several minutes..." -ForegroundColor Cyan
    
    if ($DryRun) {
        Write-Host "    [DRY RUN] Would run: $propyPath $runnerScript $ConfigPath" -ForegroundColor Cyan
    }
    else {
        Write-Host "    Command: $propyPath $runnerScript $ConfigPath" -ForegroundColor Cyan
        Write-Host ""
        
        & $propyPath $runnerScript $ConfigPath
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "    [ERROR] Publish Call Data tool failed with exit code $LASTEXITCODE" -ForegroundColor Red
            throw "Publish tool failed"
        }
        
        Write-Host ""
        Write-Host "    [OK] Publish Call Data completed successfully" -ForegroundColor Green
    }
    
    # STEP 7: Restore default export to staging (unless NoRestore)
    if (-not $NoRestore) {
        Write-Host ""
        Write-Host "[7] Restoring default export to staging..." -ForegroundColor Yellow
        
        if ($DryRun) {
            Write-Host "    [DRY RUN] Would copy: $defaultExport -> $tempFile" -ForegroundColor Cyan
            Write-Host "    [DRY RUN] Would verify size match" -ForegroundColor Cyan
            Write-Host "    [DRY RUN] Would rename: $tempFile -> $stagingFile" -ForegroundColor Cyan
        }
        else {
            Write-Host "    Copying default export to temp..." -ForegroundColor Cyan
            Copy-Item $defaultExport $tempFile -Force
            
            Write-Host "    Verifying size match..." -ForegroundColor Cyan
            $defaultSize = (Get-Item $defaultExport).Length
            $tempSize = (Get-Item $tempFile).Length
            
            if ($defaultSize -ne $tempSize) {
                Write-Host "    [ERROR] File size mismatch during restore" -ForegroundColor Red
                Write-Host "      Source: $defaultSize bytes" -ForegroundColor Red
                Write-Host "      Temp: $tempSize bytes" -ForegroundColor Red
                throw "File size mismatch during restore"
            }
            
            Write-Host "    Performing atomic swap..." -ForegroundColor Cyan
            Move-Item $tempFile $stagingFile -Force
            Write-Host "    [OK] Default export restored to staging" -ForegroundColor Green
        }
    }
    else {
        Write-Host ""
        Write-Host "[7] Restore skipped (NoRestore flag)" -ForegroundColor Yellow
        Write-Host "    WARNING: Staging file is still backfill data" -ForegroundColor Yellow
    }
    
    # SUCCESS SUMMARY
    $endTime = Get-Date
    $duration = $endTime - $startTime

    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Green
    Write-Host "[SUCCESS] WORKFLOW COMPLETED SUCCESSFULLY" -ForegroundColor Green
    Write-Host ("=" * 70) -ForegroundColor Green
    Write-Host "End time: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
    Write-Host "Duration: $($duration.ToString('mm\:ss'))" -ForegroundColor Cyan
    Write-Host ""

    if ($DryRun) {
        Write-Host "This was a DRY RUN - no changes were made" -ForegroundColor Yellow
    }
    else {
        Write-Host "Dashboard has been updated with backfill data" -ForegroundColor Green
        if (-not $NoRestore) {
            Write-Host "Staging has been restored to default export" -ForegroundColor Green
        }
        else {
            Write-Host "WARNING: Staging still contains backfill data (NoRestore flag)" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Verify dashboard shows expected date range: 2019-01-01 through 2026-02-01" -ForegroundColor Cyan
    Write-Host "2. Check record counts match expected values" -ForegroundColor Cyan
    Write-Host "3. Run Test-DashboardData.ps1 for detailed verification" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Green
    
}
catch {
    Write-Host ""
    Write-Host "[ERROR] Workflow failed: $_" -ForegroundColor Red
    Write-Host ""
    
    # Try to restore default export on error (best effort)
    if (-not $NoRestore -and -not $DryRun) {
        Write-Host "Attempting emergency restore of default export..." -ForegroundColor Yellow
        try {
            Copy-Item $defaultExport $stagingFile -Force
            Write-Host "[OK] Emergency restore completed" -ForegroundColor Green
        }
        catch {
            Write-Host "[ERROR] Emergency restore failed: $_" -ForegroundColor Red
            Write-Host "MANUAL ACTION REQUIRED: Copy $defaultExport to $stagingFile" -ForegroundColor Red
        }
    }
    
    exit 4
    
}
finally {
    # STEP 8: Remove lock file (always runs)
    Write-Host ""
    Write-Host "[8] Cleaning up..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "    [DRY RUN] Would remove lock file: $lockFile" -ForegroundColor Cyan
    }
    else {
        if (Test-Path $lockFile) {
            Remove-Item $lockFile -Force
            Write-Host "    [OK] Lock file removed" -ForegroundColor Green
        }
    }
}

exit 0
