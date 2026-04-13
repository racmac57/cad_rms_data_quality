# Run-BackfillOnRDP.ps1
# Purpose: Run truncate, then backfill, then health check on the RDP server.
# Usage: Run this script ON the RDP server (e.g. after logging in via Remote Desktop).
#
# Prerequisites:
#   - Staging file at C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx
#     with longitude/latitude or X_Coord/Y_Coord.
#   - Scripts deployed to C:\HPD ESRI\04_Scripts (Deploy-ToRDP-Simple.ps1).
#
# On RDP:
#   cd "C:\HPD ESRI\04_Scripts"
#   .\Run-BackfillOnRDP.ps1
#
# Step 1 will prompt for: TRUNCATE, <username>, DELETE ALL RECORDS.
# Step 2 and 3 run without prompts.
#
# Author: R. A. Carucci
# Date: 2026-02-16

$ErrorActionPreference = "Stop"
$ScriptDir = "C:\HPD ESRI\04_Scripts"
$Propy = "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"

foreach ($script in @("truncate_online_layer.py", "complete_backfill_simplified.py", "monitor_dashboard_health.py")) {
    $path = Join-Path $ScriptDir $script
    if (-not (Test-Path $path)) {
        Write-Error "Script not found: $path. Deploy scripts first (Deploy-ToRDP-Simple.ps1)."
    }
}
if (-not (Test-Path $Propy)) {
    Write-Error "Propy not found: $Propy. Run this script on the RDP server where ArcGIS Pro is installed."
}

Set-Location $ScriptDir

# Step 1: Truncate (interactive)
Write-Host "`n=== Step 1/3: Truncate online layer ===" -ForegroundColor Cyan
Write-Host "When prompted, type: TRUNCATE, then your username, then DELETE ALL RECORDS`n" -ForegroundColor Yellow
& $Propy (Join-Path $ScriptDir "truncate_online_layer.py")
if ($LASTEXITCODE -ne 0) {
    Write-Host "Truncate failed. Stopping." -ForegroundColor Red
    exit $LASTEXITCODE
}

# Step 2: Backfill
Write-Host "`n=== Step 2/3: Backfill (publish with geometry) ===" -ForegroundColor Cyan
& $Propy (Join-Path $ScriptDir "complete_backfill_simplified.py")
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backfill failed. Check staging file has longitude/latitude or X_Coord/Y_Coord." -ForegroundColor Red
    exit $LASTEXITCODE
}

# Step 3: Health check
Write-Host "`n=== Step 3/3: Dashboard health check ===" -ForegroundColor Cyan
& $Propy (Join-Path $ScriptDir "monitor_dashboard_health.py")
$monitorExit = $LASTEXITCODE
if ($monitorExit -eq 0) {
    Write-Host "`nAll steps completed. Dashboard should show data with points." -ForegroundColor Green
} else {
    Write-Host "`nHealth check reported an issue (exit code $monitorExit). Review report in 04_Scripts\_out\" -ForegroundColor Yellow
}
exit $monitorExit
