# Run-TruncateOnRDP.ps1
# Purpose: Run truncate_online_layer.py on the RDP server (HPD2022LAWSOFT).
# Usage: Run this script ON the RDP server (e.g. after logging in via Remote Desktop).
#
# On RDP:
#   cd "C:\HPD ESRI\04_Scripts"
#   .\Run-TruncateOnRDP.ps1
#
# When prompted by the Python script, type exactly:
#   TRUNCATE
#   <your Windows username>
#   DELETE ALL RECORDS
#
# Author: R. A. Carucci
# Date: 2026-02-16

$ErrorActionPreference = "Stop"
$Propy = "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"
$ScriptDir = "C:\HPD ESRI\04_Scripts"
$TruncateScript = Join-Path $ScriptDir "truncate_online_layer.py"

if (-not (Test-Path $Propy)) {
    Write-Error "Propy not found: $Propy. Run this script on the RDP server where ArcGIS Pro is installed."
}
if (-not (Test-Path $TruncateScript)) {
    Write-Error "Truncate script not found: $TruncateScript. Deploy scripts first (Deploy-ToRDP-Simple.ps1)."
}

Set-Location $ScriptDir
Write-Host "Running truncate_online_layer.py (you will be prompted for 3 confirmations)..." -ForegroundColor Cyan
& $Propy $TruncateScript
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Host "Truncate script exited with code $exitCode" -ForegroundColor Red
    exit $exitCode
}
Write-Host "Truncate completed. Online layer should now have 0 records." -ForegroundColor Green
