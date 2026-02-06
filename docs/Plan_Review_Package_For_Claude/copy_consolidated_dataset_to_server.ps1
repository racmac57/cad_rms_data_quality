# ================================================================
# Copy Consolidated CAD Dataset to Remote Server
# ================================================================
# Purpose: Copy the consolidated CAD dataset (2019-2026) to the 
#          remote server for use with ArcGIS Pro dashboard
# Date: 2026-01-31
# Author: R. A. Carucci
# ================================================================

# Define source and destination paths
$sourceFile = "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final\CAD_ESRI_POLISHED_20260131_004142.xlsx"
$serverIP = "10.0.0.157"
$serverName = "HPD2022LAWSOFT"
$destESRIShare = "\\$serverIP\esri\CAD_Consolidated_2019_2026.xlsx"
$destESRIShareOriginal = "\\$serverIP\esri\CAD_ESRI_POLISHED_20260131_004142.xlsx"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "CAD CONSOLIDATED DATASET COPY TO REMOTE SERVER" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Verify source file exists
Write-Host "[Step 1] Verifying source file..." -ForegroundColor Yellow
if (Test-Path $sourceFile) {
    $sourceInfo = Get-Item $sourceFile
    Write-Host "  OK Source file found" -ForegroundColor Green
    Write-Host "    Path: $sourceFile" -ForegroundColor Gray
    Write-Host "    Size: $([math]::Round($sourceInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
    Write-Host "    Last Modified: $($sourceInfo.LastWriteTime)" -ForegroundColor Gray
    Write-Host ""
}
else {
    Write-Host "  ERROR Source file not found: $sourceFile" -ForegroundColor Red
    exit 1
}

# Check server connectivity
Write-Host "[Step 2] Checking server connectivity..." -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName $serverIP -Count 2 -Quiet
if ($pingResult) {
    Write-Host "  OK Server $serverName ($serverIP) is reachable" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "  ERROR Server $serverName ($serverIP) is NOT reachable" -ForegroundColor Red
    Write-Host "    Please verify network connection or VPN" -ForegroundColor Yellow
    exit 1
}

# Check ESRI share access
Write-Host "[Step 3] Checking ESRI share access..." -ForegroundColor Yellow
if (Test-Path "\\$serverIP\esri") {
    Write-Host "  OK ESRI share is accessible: \\$serverIP\esri" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "  ERROR ESRI share is NOT accessible: \\$serverIP\esri" -ForegroundColor Red
    Write-Host "    Please verify share permissions" -ForegroundColor Yellow
    Write-Host ""
}

# Copy file to ESRI share with original filename
Write-Host "[Step 4] Copying file to ESRI share (original filename)..." -ForegroundColor Yellow
try {
    Copy-Item -Path $sourceFile -Destination $destESRIShareOriginal -Force -ErrorAction Stop
    Write-Host "  OK File copied successfully" -ForegroundColor Green
    Write-Host "    Destination: $destESRIShareOriginal" -ForegroundColor Gray
    
    if (Test-Path $destESRIShareOriginal) {
        $destInfo = Get-Item $destESRIShareOriginal
        Write-Host "    Size: $([math]::Round($destInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
        Write-Host "    Copied: $($destInfo.LastWriteTime)" -ForegroundColor Gray
    }
    Write-Host ""
}
catch {
    Write-Host "  ERROR Failed to copy file: $_" -ForegroundColor Red
    Write-Host ""
}

# Copy file to ESRI share with friendly filename
Write-Host "[Step 5] Copying file to ESRI share (friendly filename)..." -ForegroundColor Yellow
try {
    Copy-Item -Path $sourceFile -Destination $destESRIShare -Force -ErrorAction Stop
    Write-Host "  OK File copied successfully" -ForegroundColor Green
    Write-Host "    Destination: $destESRIShare" -ForegroundColor Gray
    
    if (Test-Path $destESRIShare) {
        $destInfo = Get-Item $destESRIShare
        Write-Host "    Size: $([math]::Round($destInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
        Write-Host "    Copied: $($destInfo.LastWriteTime)" -ForegroundColor Gray
    }
    Write-Host ""
}
catch {
    Write-Host "  ERROR Failed to copy file: $_" -ForegroundColor Red
    Write-Host ""
}

# Summary
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "COPY OPERATION COMPLETE" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dataset Information:" -ForegroundColor White
Write-Host "  File: CAD_ESRI_POLISHED_20260131_004142.xlsx" -ForegroundColor Gray
Write-Host "  Records: 716,420" -ForegroundColor Gray
Write-Host "  Date Range: 2019-01-01 to 2026-01-16" -ForegroundColor Gray
Write-Host "  Unique Cases: 553,624" -ForegroundColor Gray
Write-Host "  Size: 73.9 MB" -ForegroundColor Gray
Write-Host ""
Write-Host "Files Available On Server:" -ForegroundColor White
Write-Host "  Network Share: \\$serverIP\esri\CAD_Consolidated_2019_2026.xlsx" -ForegroundColor Cyan
Write-Host "  Network Share: \\$serverIP\esri\CAD_ESRI_POLISHED_20260131_004142.xlsx" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. Connect to server via Remote Desktop (HPD2022LAWSOFT)" -ForegroundColor Gray
Write-Host "  2. Open ArcGIS Pro" -ForegroundColor Gray
Write-Host "  3. Import dataset from:" -ForegroundColor Gray
Write-Host "     \\$serverIP\esri\CAD_Consolidated_2019_2026.xlsx" -ForegroundColor Cyan
Write-Host "  4. Verify 716,420 records imported correctly" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation:" -ForegroundColor White
Write-Host "  REMOTE_SERVER_GUIDE.md - Comprehensive guide" -ForegroundColor Gray
Write-Host "  SERVER_QUICK_REFERENCE.txt - Quick reference card" -ForegroundColor Gray
Write-Host "  outputs/consolidation/CONSOLIDATION_RUN_2026_01_30_SUMMARY.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
