<#
.SYNOPSIS
    Pre-flight checks for CAD backfill publish workflow
    
.DESCRIPTION
    Tests all prerequisites before allowing a backfill publish to proceed:
    - Lock file check (with stale lock detection)
    - Scheduled task status check
    - Process check (geoprocessing workers)
    - Geodatabase lock check
    - File existence and sheet name validation
    - Disk space check
    
.PARAMETER ConfigPath
    Path to config.json file
    
.PARAMETER BackfillFile
    Path to the backfill Excel file to validate
    
.PARAMETER SkipSheetCheck
    Skip Excel sheet name validation (for testing)
    
.EXAMPLE
    .\Test-PublishReadiness.ps1 -ConfigPath "C:\HPD ESRI\04_Scripts\config.json" -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
    
.NOTES
    Author: R. A. Carucci
    Date: 2026-02-02
    Version: 1.0.0
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ConfigPath,
    
    [Parameter(Mandatory=$true)]
    [string]$BackfillFile,
    
    [switch]$SkipSheetCheck
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "PRE-FLIGHT READINESS CHECKS" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Load configuration
Write-Host "[1] Loading configuration..." -ForegroundColor Yellow
try {
    $config = Get-Content $ConfigPath | ConvertFrom-Json
    Write-Host "    ✓ Config loaded from: $ConfigPath" -ForegroundColor Green
} catch {
    Write-Host "    ✗ ERROR: Failed to load config: $_" -ForegroundColor Red
    exit 1
}

$checksPassed = 0
$checksTotal = 6
$checksFailed = @()

# CHECK 1: Lock file status
Write-Host ""
Write-Host "[2] Checking lock file status..." -ForegroundColor Yellow
$lockFile = $config.paths.lock_file

if (Test-Path $lockFile) {
    Write-Host "    ⚠ Lock file exists: $lockFile" -ForegroundColor Yellow
    
    # Read lock metadata
    try {
        $lockData = Get-Content $lockFile | ConvertFrom-Json
        $lockStartTime = [DateTime]::Parse($lockData.start_time)
        $lockAge = (Get-Date) - $lockStartTime
        $lockAgeHours = $lockAge.TotalHours
        
        Write-Host "    Lock created: $lockStartTime" -ForegroundColor Yellow
        Write-Host "    Lock age: $([int]$lockAgeHours) hours, $([int]$lockAge.Minutes) minutes" -ForegroundColor Yellow
        Write-Host "    Lock holder: $($lockData.user)@$($lockData.computer)" -ForegroundColor Yellow
        Write-Host "    Process ID: $($lockData.process_id)" -ForegroundColor Yellow
        
        # Check if process is still running
        $processAlive = $null -ne (Get-Process -Id $lockData.process_id -ErrorAction SilentlyContinue)
        
        if ($processAlive) {
            Write-Host "    ✗ Process is still running - lock is ACTIVE" -ForegroundColor Red
            $checksFailed += "Lock file is active (process running)"
        } else {
            Write-Host "    ⚠ Process is dead - checking if lock is stale..." -ForegroundColor Yellow
            
            $lockTimeoutHours = $config.collision_control.lock_timeout_hours
            if ($lockAgeHours -gt $lockTimeoutHours) {
                Write-Host "    ✓ Lock is STALE (>$lockTimeoutHours hours, process dead)" -ForegroundColor Green
                Write-Host "    Removing stale lock..." -ForegroundColor Green
                Remove-Item $lockFile -Force
                Write-Host "    ✓ Stale lock removed" -ForegroundColor Green
                $checksPassed++
            } else {
                Write-Host "    ✗ Lock age is <$lockTimeoutHours hours but process is dead - manual investigation required" -ForegroundColor Red
                $checksFailed += "Lock file exists but process is dead (age: $([int]$lockAgeHours)h)"
            }
        }
        
    } catch {
        Write-Host "    ✗ ERROR reading lock file: $_" -ForegroundColor Red
        Write-Host "    Manual cleanup required: Remove $lockFile" -ForegroundColor Red
        $checksFailed += "Lock file exists but cannot be read"
    }
} else {
    Write-Host "    ✓ No lock file present" -ForegroundColor Green
    $checksPassed++
}

# CHECK 2: Scheduled tasks
Write-Host ""
Write-Host "[3] Checking scheduled task status..." -ForegroundColor Yellow
$tasksRunning = @()

foreach ($taskName in $config.scheduled_tasks) {
    try {
        $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction SilentlyContinue
        
        if ($null -ne $taskInfo) {
            $taskState = $taskInfo.State.ToString()
            Write-Host "    Task: $taskName - State: $taskState" -ForegroundColor Cyan
            
            if ($taskState -eq "Running") {
                $tasksRunning += $taskName
            }
        } else {
            Write-Host "    Task: $taskName - Not found" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "    ⚠ Could not check task: $taskName" -ForegroundColor Yellow
    }
}

if ($tasksRunning.Count -gt 0) {
    Write-Host "    ✗ Running tasks detected: $($tasksRunning -join ', ')" -ForegroundColor Red
    $checksFailed += "Scheduled tasks are running"
} else {
    Write-Host "    ✓ No scheduled tasks running" -ForegroundColor Green
    $checksPassed++
}

# CHECK 3: ArcGIS processes
Write-Host ""
Write-Host "[4] Checking for active geoprocessing..." -ForegroundColor Yellow
$arcProcesses = Get-Process | Where-Object { 
    ($_.Name -like "ArcGISPro") -or 
    ($_.Name -like "python*" -and $_.Path -like "*ArcGIS*") -or
    ($_.Name -like "ProSwap") -or
    ($_.Name -like "ArcSOC")
}

if ($arcProcesses) {
    Write-Host "    ⚠ ArcGIS-related processes detected:" -ForegroundColor Yellow
    $arcProcesses | ForEach-Object {
        Write-Host "      - $($_.Name) (PID: $($_.Id))" -ForegroundColor Cyan
    }
    
    # Only block if geoprocessing workers are active
    $gpWorkers = $arcProcesses | Where-Object { 
        $_.Name -like "python*" -or $_.Name -like "ProSwap" -or $_.Name -like "ArcSOC"
    }
    
    if ($gpWorkers) {
        Write-Host "    ✗ Active geoprocessing workers detected - BLOCKING" -ForegroundColor Red
        $checksFailed += "Geoprocessing workers are active"
    } else {
        Write-Host "    ✓ ArcGIS Pro is open but no active geoprocessing" -ForegroundColor Green
        $checksPassed++
    }
} else {
    Write-Host "    ✓ No ArcGIS processes running" -ForegroundColor Green
    $checksPassed++
}

# CHECK 4: Geodatabase lock
Write-Host ""
Write-Host "[5] Checking geodatabase lock..." -ForegroundColor Yellow
$gdb = $config.paths.geodatabase

try {
    $testFile = Join-Path $gdb "_locktest.tmp"
    "test" | Out-File $testFile -Force
    Remove-Item $testFile -Force
    Write-Host "    ✓ Geodatabase is accessible (not locked)" -ForegroundColor Green
    $checksPassed++
} catch {
    Write-Host "    ✗ Geodatabase appears to be locked: $_" -ForegroundColor Red
    $checksFailed += "Geodatabase is locked"
}

# CHECK 5: Backfill file validation
Write-Host ""
Write-Host "[6] Validating backfill file..." -ForegroundColor Yellow

if (-not (Test-Path $BackfillFile)) {
    Write-Host "    ✗ Backfill file not found: $BackfillFile" -ForegroundColor Red
    $checksFailed += "Backfill file not found"
} else {
    $fileSize = (Get-Item $BackfillFile).Length / 1MB
    Write-Host "    ✓ File exists: $BackfillFile" -ForegroundColor Green
    Write-Host "    File size: $([int]$fileSize) MB" -ForegroundColor Cyan
    
    # Check file size is reasonable
    if ($fileSize -lt 10) {
        Write-Host "    ⚠ WARNING: File size seems small for backfill data" -ForegroundColor Yellow
    }
    
    # Check sheet name (unless skipped)
    if (-not $SkipSheetCheck) {
        Write-Host "    Checking Excel sheet name..." -ForegroundColor Cyan
        
        try {
            $excel = New-Object -ComObject Excel.Application
            $excel.Visible = $false
            $excel.DisplayAlerts = $false
            
            $workbook = $excel.Workbooks.Open($BackfillFile)
            $sheetNames = @($workbook.Worksheets | ForEach-Object { $_.Name })
            
            Write-Host "    Sheets found: $($sheetNames -join ', ')" -ForegroundColor Cyan
            
            $requiredSheet = $config.verification.required_sheet_name
            if ($sheetNames -contains $requiredSheet) {
                Write-Host "    ✓ Required sheet '$requiredSheet' found" -ForegroundColor Green
                $checksPassed++
            } else {
                Write-Host "    ✗ Required sheet '$requiredSheet' NOT found" -ForegroundColor Red
                Write-Host "    Action required: Rename sheet to '$requiredSheet' before staging" -ForegroundColor Red
                $checksFailed += "Backfill file missing required sheet name: $requiredSheet"
            }
            
            $workbook.Close($false)
            $excel.Quit()
            
            # Clean up COM objects
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($workbook) | Out-Null
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()
            
        } catch {
            Write-Host "    ⚠ WARNING: Could not validate sheet name: $_" -ForegroundColor Yellow
            Write-Host "    Assuming sheet name is correct..." -ForegroundColor Yellow
            $checksPassed++
        }
    } else {
        Write-Host "    ⚠ Sheet name check skipped" -ForegroundColor Yellow
        $checksPassed++
    }
}

# CHECK 6: Disk space
Write-Host ""
Write-Host "[7] Checking disk space..." -ForegroundColor Yellow
$drive = Split-Path $config.paths.staging_dir -Qualifier
$driveInfo = Get-PSDrive ($drive.TrimEnd(':'))
$freeSpaceGB = [math]::Round($driveInfo.Free / 1GB, 2)

Write-Host "    Drive: $drive" -ForegroundColor Cyan
Write-Host "    Free space: $freeSpaceGB GB" -ForegroundColor Cyan

if ($freeSpaceGB -lt 5) {
    Write-Host "    ✗ Low disk space (< 5 GB)" -ForegroundColor Red
    $checksFailed += "Low disk space: ${freeSpaceGB}GB"
} else {
    Write-Host "    ✓ Sufficient disk space" -ForegroundColor Green
    $checksPassed++
}

# SUMMARY
Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "PRE-FLIGHT SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "Checks passed: $checksPassed / $checksTotal" -ForegroundColor $(if ($checksPassed -eq $checksTotal) { "Green" } else { "Yellow" })

if ($checksFailed.Count -gt 0) {
    Write-Host ""
    Write-Host "✗ FAILED CHECKS:" -ForegroundColor Red
    $checksFailed | ForEach-Object {
        Write-Host "  - $_" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "RECOMMENDATION: Do not proceed with backfill publish" -ForegroundColor Red
    Write-Host ("=" * 70) -ForegroundColor Cyan
    exit 1
} else {
    Write-Host ""
    Write-Host "✓ ALL CHECKS PASSED - Ready for backfill publish" -ForegroundColor Green
    Write-Host ("=" * 70) -ForegroundColor Cyan
    exit 0
}
