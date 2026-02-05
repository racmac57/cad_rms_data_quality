################################################################################
# Schedule ArcGIS Pro "Publish Call Data" Tool for 3 AM
# Creates a Windows Scheduled Task to run during off-peak hours
################################################################################

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$TaskName = "ArcGIS_Publish_Call_Data_3AM",
    
    [Parameter(Mandatory = $false)]
    [string]$Time = "03:00:00",
    
    [Parameter(Mandatory = $false)]
    [switch]$RunOnce,  # If set, runs once tomorrow. Otherwise, runs daily.
    
    [Parameter(Mandatory = $false)]
    [switch]$RemoveTask  # If set, removes existing task
)

$ErrorActionPreference = "Stop"

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "Schedule ArcGIS Pro Publish Call Data Tool" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "`n[ERROR] This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Remove existing task if requested
if ($RemoveTask) {
    Write-Host "`n[INFO] Removing existing task: $TaskName" -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "[SUCCESS] Task removed" -ForegroundColor Green
    }
    catch {
        Write-Host "[INFO] Task did not exist or could not be removed" -ForegroundColor Yellow
    }
    exit 0
}

# Paths
$pythonScript = "C:\Temp\scheduled_tasks\scheduled_publish_call_data.py"
$proPyExe = "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"
$logDir = "C:\Temp\arcgis_scheduled_tasks"

# Verify files exist
Write-Host "`n[VERIFY] Checking required files..." -ForegroundColor Cyan

if (-not (Test-Path $pythonScript)) {
    Write-Host "[ERROR] Python script not found: $pythonScript" -ForegroundColor Red
    exit 1
}
Write-Host "  Python script: $pythonScript" -ForegroundColor Green

if (-not (Test-Path $proPyExe)) {
    Write-Host "[ERROR] ArcGIS Pro Python not found: $proPyExe" -ForegroundColor Red
    exit 1
}
Write-Host "  ArcGIS Pro Python: $proPyExe" -ForegroundColor Green

# Create log directory if needed
if (-not (Test-Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    Write-Host "  Created log directory: $logDir" -ForegroundColor Green
}

# Calculate trigger date/time
$tomorrow = (Get-Date).AddDays(1).Date
$triggerTime = [datetime]::Parse("$($tomorrow.ToString('yyyy-MM-dd')) $Time")

Write-Host "`n[INFO] Task Configuration:" -ForegroundColor Cyan
Write-Host "  Task Name: $TaskName" -ForegroundColor White
Write-Host "  Schedule: $($triggerTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
if ($RunOnce) {
    Write-Host "  Frequency: One-time only" -ForegroundColor White
}
else {
    Write-Host "  Frequency: Daily at $Time" -ForegroundColor White
}
Write-Host "  Python Script: $pythonScript" -ForegroundColor White
Write-Host "  Log Directory: $logDir" -ForegroundColor White

# Confirm
Write-Host "`n[CONFIRM] Create this scheduled task? (Y/N): " -ForegroundColor Yellow -NoNewline
$confirm = Read-Host
if ($confirm -ne 'Y' -and $confirm -ne 'y') {
    Write-Host "[CANCELLED] Task not created" -ForegroundColor Yellow
    exit 0
}

# Create the scheduled task
Write-Host "`n[CREATE] Creating scheduled task..." -ForegroundColor Cyan

try {
    # Task action: Run propy.bat with the Python script
    $action = New-ScheduledTaskAction `
        -Execute $proPyExe `
        -Argument "`"$pythonScript`"" `
        -WorkingDirectory (Split-Path $pythonScript)
    
    # Task trigger: Daily at specified time
    if ($RunOnce) {
        $trigger = New-ScheduledTaskTrigger -Once -At $triggerTime
    }
    else {
        $trigger = New-ScheduledTaskTrigger -Daily -At $triggerTime
    }
    
    # Task settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
        -RestartCount 1 `
        -RestartInterval (New-TimeSpan -Minutes 10)
    
    # Task principal (run as current user)
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Highest
    
    # Register the task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Publishes CAD call data to ArcGIS Online feature service during off-peak hours (3 AM). Uploads 565,870 records from local geodatabase." `
        -Force | Out-Null
    
    Write-Host "[SUCCESS] Scheduled task created!" -ForegroundColor Green
    
    # Display task info
    $task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "`n[INFO] Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $($task.TaskName)" -ForegroundColor White
    Write-Host "  State: $($task.State)" -ForegroundColor White
    Write-Host "  Next Run: $($task.Triggers[0].StartBoundary)" -ForegroundColor White
    
    Write-Host "`n[NEXT STEPS]" -ForegroundColor Cyan
    Write-Host "1. Task is scheduled and ready" -ForegroundColor White
    Write-Host "2. It will run automatically at $($triggerTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
    Write-Host "3. Check logs in: $logDir" -ForegroundColor White
    Write-Host "4. Monitor task: Task Scheduler > Task Scheduler Library > $TaskName" -ForegroundColor White
    
    Write-Host "`n[OPTIONAL] Test the task now:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    
    Write-Host "`n[OPTIONAL] Remove the task:" -ForegroundColor Yellow
    Write-Host "  .\Schedule-PublishCallData.ps1 -RemoveTask" -ForegroundColor White
    
}
catch {
    Write-Host "`n[ERROR] Failed to create scheduled task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "Scheduled Task Created Successfully!" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green
Write-Host "`n"
