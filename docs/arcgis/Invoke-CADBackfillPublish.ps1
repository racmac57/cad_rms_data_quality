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
    
.PARAMETER Staged
    Enable staged batch processing mode (processes multiple batches sequentially)
    
.PARAMETER BatchFolder
    Path to folder containing batch files (default: C:\HPD ESRI\03_Data\CAD\Backfill\Batches)
    
.PARAMETER CoolingSeconds
    Seconds to wait between batches (default: 60, adaptive extends to 120)
    
.PARAMETER MaxHangSeconds
    Watchdog timeout in seconds (default: 300 = 5 minutes)
    
.EXAMPLE
    .\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
    
.EXAMPLE
    .\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" -DryRun
    
.EXAMPLE
    .\Invoke-CADBackfillPublish.ps1 -Staged -BatchFolder "C:\HPD ESRI\03_Data\CAD\Backfill\Batches"
    
.EXAMPLE
    .\Invoke-CADBackfillPublish.ps1 -Staged -DryRun
    
.NOTES
    Author: R. A. Carucci
    Date: 2026-02-02
    Version: 2.0.0 (Staged Backfill with Watchdog)
    Updated: 2026-02-06 (Added staged batch processing)
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$BackfillFile,
    
    [string]$ConfigPath = "C:\HPD ESRI\04_Scripts\config.json",
    
    [switch]$DryRun,
    [switch]$SkipPreFlightChecks,
    [switch]$NoRestore,
    
    # Staged mode parameters
    [switch]$Staged,
    [string]$BatchFolder = "C:\HPD ESRI\03_Data\CAD\Backfill\Batches",
    [int]$CoolingSeconds = 60,
    [int]$MaxHangSeconds = 300
)

$ErrorActionPreference = "Stop"
$startTime = Get-Date

# Validate parameters
if (-not $Staged -and -not $BackfillFile) {
    Write-Host "ERROR: Either -BackfillFile or -Staged must be specified" -ForegroundColor Red
    Write-Host "Usage: .\Invoke-CADBackfillPublish.ps1 -BackfillFile <path>" -ForegroundColor Yellow
    Write-Host "   OR: .\Invoke-CADBackfillPublish.ps1 -Staged" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "CAD BACKFILL PUBLISH ORCHESTRATOR" -ForegroundColor Cyan
if ($Staged) {
    Write-Host "MODE: STAGED BATCH PROCESSING" -ForegroundColor Magenta
}
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "Start time: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
if ($Staged) {
    Write-Host "Batch folder: $BatchFolder" -ForegroundColor Cyan
    Write-Host "Cooling period: $CoolingSeconds seconds" -ForegroundColor Cyan
    Write-Host "Watchdog timeout: $MaxHangSeconds seconds" -ForegroundColor Cyan
} else {
    Write-Host "Backfill file: $BackfillFile" -ForegroundColor Cyan
}
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

if (-not $Staged) {
    # Single file mode validations
    if (-not (Test-Path $BackfillFile)) {
        Write-Host "    [ERROR] Backfill file not found: $BackfillFile" -ForegroundColor Red
        exit 2
    }
}
else {
    # Staged mode validations
    if (-not (Test-Path $BatchFolder)) {
        Write-Host "    [ERROR] Batch folder not found: $BatchFolder" -ForegroundColor Red
        exit 2
    }
    
    $batchFiles = Get-ChildItem -Path $BatchFolder -Filter "BATCH_*.xlsx" -ErrorAction SilentlyContinue
    if ($batchFiles.Count -eq 0) {
        Write-Host "    [ERROR] No batch files found in: $BatchFolder" -ForegroundColor Red
        Write-Host "    Expected: BATCH_*.xlsx files" -ForegroundColor Yellow
        exit 2
    }
    Write-Host "    [OK] Found $($batchFiles.Count) batch files" -ForegroundColor Green
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
            Write-Host "    WARNING: Pre-flight script not found, skipping checks" -ForegroundColor Yellow
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
    # ====================================================================
    # STAGED MODE: Process multiple batches sequentially with watchdog
    # ====================================================================
    if ($Staged) {
        Write-Host ""
        Write-Host ("=" * 70) -ForegroundColor Magenta
        Write-Host "STAGED BATCH PROCESSING MODE" -ForegroundColor Magenta
        Write-Host ("=" * 70) -ForegroundColor Magenta
        
        # Find all batch files (not in Completed/ folder)
        $batchFiles = Get-ChildItem -Path $BatchFolder -Filter "BATCH_*.xlsx" | Sort-Object Name
        $completedDir = Join-Path $BatchFolder "Completed"
        
        if (-not (Test-Path $completedDir)) {
            New-Item -ItemType Directory -Path $completedDir | Out-Null
            Write-Host "[INFO] Created Completed folder: $completedDir" -ForegroundColor Cyan
        }
        
        $totalBatches = $batchFiles.Count
        $currentBatch = 0
        $heartbeatFile = Join-Path $stagingDir "heartbeat.txt"
        
        Write-Host ""
        Write-Host "[INFO] Batches to process: $totalBatches" -ForegroundColor Cyan
        Write-Host "[INFO] Cooling period: $CoolingSeconds seconds" -ForegroundColor Cyan
        Write-Host "[INFO] Watchdog timeout: $MaxHangSeconds seconds" -ForegroundColor Cyan
        Write-Host ""
        
        # Disk space check (Gemini enhancement)
        $drive = (Get-Item $stagingDir).PSDrive
        $freeSpaceMB = [math]::Round((Get-PSDrive $drive.Name).Free / 1MB, 2)
        if ($freeSpaceMB -lt 500) {
            Write-Host "[ERROR] Insufficient disk space: ${freeSpaceMB}MB free (need 500MB)" -ForegroundColor Red
            throw "Insufficient disk space"
        }
        Write-Host "[OK] Disk space check passed: ${freeSpaceMB}MB free" -ForegroundColor Green
        
        foreach ($batchFile in $batchFiles) {
            $currentBatch++
            $batchNum = [regex]::Match($batchFile.Name, "BATCH_(\d+)").Groups[1].Value
            
            Write-Host ""
            Write-Host ("=" * 70) -ForegroundColor Yellow
            Write-Host "BATCH $batchNum OF $totalBatches" -ForegroundColor Yellow
            Write-Host ("=" * 70) -ForegroundColor Yellow
            Write-Host "File: $($batchFile.Name)" -ForegroundColor Yellow
            Write-Host "Size: $([math]::Round($batchFile.Length / 1MB, 2)) MB" -ForegroundColor Yellow
            Write-Host ("=" * 70) -ForegroundColor Yellow
            
            $batchTimer = [Diagnostics.Stopwatch]::StartNew()
            
            # Create batch number marker for Python runner
            $batchMarker = Join-Path $stagingDir "_current_batch.txt"
            if (-not $DryRun) {
                $batchNum | Out-File $batchMarker -Force
            }
            
            # Atomic swap to staging
            Write-Host "[1] Staging batch file..." -ForegroundColor Yellow
            $tempFile = Join-Path $stagingDir "ESRI_CADExport.xlsx.tmp"
            
            if ($DryRun) {
                Write-Host "    [DRY RUN] Would copy: $($batchFile.FullName) -> $tempFile" -ForegroundColor Cyan
                Write-Host "    [DRY RUN] Would move: $tempFile -> $stagingFile" -ForegroundColor Cyan
            }
            else {
                Copy-Item $batchFile.FullName $tempFile -Force
                Move-Item $tempFile $stagingFile -Force
                Write-Host "    [OK] Batch staged successfully" -ForegroundColor Green
            }
            
            # Run publish tool with watchdog monitoring
            Write-Host "[2] Executing ArcGIS Pro publish tool with watchdog..." -ForegroundColor Yellow
            
            if ($DryRun) {
                Write-Host "    [DRY RUN] Would start: $propyPath $runnerScript $ConfigPath" -ForegroundColor Cyan
                Write-Host "    [DRY RUN] Would monitor heartbeat file: $heartbeatFile" -ForegroundColor Cyan
            }
            else {
                Write-Host "    Starting Python process..." -ForegroundColor Cyan
                Write-Host "    Command: $propyPath $runnerScript $ConfigPath" -ForegroundColor Gray
                
                # Start Python process in background for monitoring
                $proc = Start-Process -FilePath $propyPath `
                                      -ArgumentList "`"$runnerScript`" `"$ConfigPath`"" `
                                      -PassThru `
                                      -NoNewWindow `
                                      -RedirectStandardOutput (Join-Path $stagingDir "batch_${batchNum}_stdout.log") `
                                      -RedirectStandardError (Join-Path $stagingDir "batch_${batchNum}_stderr.log")
                
                Write-Host "    Process started: PID $($proc.Id)" -ForegroundColor Cyan
                Write-Host "    Watchdog monitoring active..." -ForegroundColor Cyan
                
                $isHung = $false
                $lastHeartbeatCheck = Get-Date
                
                # Watchdog monitoring loop
                while (-not $proc.HasExited) {
                    Start-Sleep -Seconds 30
                    
                    # Check heartbeat file freshness
                    if (Test-Path $heartbeatFile) {
                        $lastUpdate = (Get-Item $heartbeatFile).LastWriteTime
                        $timeSinceHeartbeat = (Get-Date) - $lastUpdate
                        $secondsSinceHeartbeat = [math]::Round($timeSinceHeartbeat.TotalSeconds, 0)
                        
                        Write-Host "    [WATCHDOG] Heartbeat age: ${secondsSinceHeartbeat}s (threshold: ${MaxHangSeconds}s)" -ForegroundColor Gray
                        
                        if ($timeSinceHeartbeat.TotalSeconds -gt $MaxHangSeconds) {
                            Write-Host ""
                            Write-Host "    [CRITICAL] HEARTBEAT STALLED FOR BATCH $batchNum" -ForegroundColor Red
                            Write-Host "    Last heartbeat: $($lastUpdate.ToString('HH:mm:ss'))" -ForegroundColor Red
                            Write-Host "    Time frozen: ${secondsSinceHeartbeat} seconds" -ForegroundColor Red
                            Write-Host "    Terminating hung process..." -ForegroundColor Yellow
                            
                            Stop-Process -Id $proc.Id -Force
                            $isHung = $true
                            break
                        }
                    }
                    else {
                        Write-Host "    [WATCHDOG] Waiting for initial heartbeat..." -ForegroundColor Gray
                    }
                }
                
                # Wait for process to fully terminate
                if (-not $proc.HasExited) {
                    $proc.WaitForExit(5000)
                }
                
                # Check results
                if ($isHung) {
                    Write-Host ""
                    Write-Host "    [ERROR] Batch $batchNum was killed by watchdog (silent hang detected)" -ForegroundColor Red
                    Write-Host "    Batch file preserved for inspection: $($batchFile.FullName)" -ForegroundColor Yellow
                    Write-Host "    Review logs in: $stagingDir" -ForegroundColor Yellow
                    throw "Batch processing terminated by watchdog at batch $batchNum"
                }
                elseif ($proc.ExitCode -eq 0) {
                    $batchTimer.Stop()
                    $elapsed = $batchTimer.Elapsed.ToString("mm\:ss")
                    
                    Write-Host ""
                    Write-Host "    [OK] Batch $batchNum completed successfully in $elapsed" -ForegroundColor Green
                    
                    # Move to completed folder
                    $completedPath = Join-Path $completedDir $batchFile.Name
                    Move-Item $batchFile.FullName $completedPath -Force
                    Write-Host "    [OK] Moved to Completed folder" -ForegroundColor Green
                    
                    # Adaptive cooling period (Gemini enhancement)
                    if ($currentBatch -lt $totalBatches) {
                        # Check for network lag indicators in stdout log
                        $stdoutLog = Join-Path $stagingDir "batch_${batchNum}_stdout.log"
                        if (Test-Path $stdoutLog) {
                            $logContent = Get-Content $stdoutLog -Raw
                            if ($logContent -match "network|timeout|lag|throttl") {
                                Write-Host "    [ADAPTIVE] Network lag detected, extending cooling to ${CoolingSeconds}s + 60s" -ForegroundColor Yellow
                                $actualCooling = $CoolingSeconds + 60
                            }
                            else {
                                $actualCooling = $CoolingSeconds
                            }
                        }
                        else {
                            $actualCooling = $CoolingSeconds
                        }
                        
                        Write-Host "    [COOLING] Waiting $actualCooling seconds before next batch..." -ForegroundColor Cyan
                        Start-Sleep -Seconds $actualCooling
                    }
                }
                else {
                    Write-Host ""
                    Write-Host "    [ERROR] Batch $batchNum failed with exit code $($proc.ExitCode)" -ForegroundColor Red
                    Write-Host "    Batch file preserved for inspection: $($batchFile.FullName)" -ForegroundColor Yellow
                    throw "Batch processing failed at batch $batchNum with exit code $($proc.ExitCode)"
                }
            }
        }
        
        # All batches complete - cleanup markers
        Write-Host ""
        Write-Host ("=" * 70) -ForegroundColor Green
        Write-Host "ALL BATCHES COMPLETED SUCCESSFULLY" -ForegroundColor Green
        Write-Host ("=" * 70) -ForegroundColor Green
        Write-Host ""
        
        if (-not $DryRun) {
            # Remove marker files
            $markerFile = Join-Path $stagingDir "is_first_batch.txt"
            $batchMarkerFile = Join-Path $stagingDir "_current_batch.txt"
            
            if (Test-Path $markerFile) {
                Remove-Item $markerFile -Force
                Write-Host "[CLEANUP] Removed first batch marker" -ForegroundColor Green
            }
            
            if (Test-Path $batchMarkerFile) {
                Remove-Item $batchMarkerFile -Force
                Write-Host "[CLEANUP] Removed batch number marker" -ForegroundColor Green
            }
            
            if (Test-Path $heartbeatFile) {
                Remove-Item $heartbeatFile -Force
                Write-Host "[CLEANUP] Removed heartbeat file" -ForegroundColor Green
            }
            
            # Clean up batch logs
            Get-ChildItem -Path $stagingDir -Filter "batch_*_*.log" | Remove-Item -Force
            Write-Host "[CLEANUP] Removed batch logs" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "System ready for nightly automation" -ForegroundColor Green
        
        # SUCCESS SUMMARY
        $endTime = Get-Date
        $duration = $endTime - $startTime
        Write-Host ""
        Write-Host "End time: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
        Write-Host "Total duration: $($duration.ToString('hh\:mm\:ss'))" -ForegroundColor Cyan
        Write-Host "Average per batch: $([math]::Round($duration.TotalMinutes / $totalBatches, 1)) minutes" -ForegroundColor Cyan
        
        exit 0
    }
    
    # ====================================================================
    # SINGLE FILE MODE: Original backfill logic (legacy)
    # ====================================================================
    
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
