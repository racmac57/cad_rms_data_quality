# ================================================================
# Copy Consolidated CAD Dataset to Remote Server (v2.0 - Manifest-Based)
# ================================================================
# Purpose: Copy the latest consolidated CAD dataset to the remote server
#          for use with ArcGIS Pro dashboard
# Date: 2026-02-01
# Author: R. A. Carucci
# Version: 2.0.0 - Now reads from 13_PROCESSED_DATA/manifest.json
# ================================================================

param(
    [switch]$DryRun,
    [switch]$Verbose
)

# Configuration
$processedDataRoot = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA"
$manifestPath = Join-Path $processedDataRoot "manifest.json"
$serverIP = "10.0.0.157"
$serverName = "HPD2022LAWSOFT"
$destESRIShare = "\\$serverIP\esri"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "CAD CONSOLIDATED DATASET COPY TO REMOTE SERVER" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Version: 2.0.0 (Manifest-Based)" -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN MODE] No files will be copied" -ForegroundColor Yellow
    Write-Host ""
}

# ================================================================
# STEP 1: Read manifest.json to find latest polished file
# ================================================================
Write-Host "[Step 1] Reading manifest.json..." -ForegroundColor Yellow

if (-not (Test-Path $manifestPath)) {
    Write-Host "  ERROR: Manifest not found at: $manifestPath" -ForegroundColor Red
    Write-Host "  Please ensure 13_PROCESSED_DATA/manifest.json exists" -ForegroundColor Yellow
    exit 1
}

try {
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    Write-Host "  OK Manifest loaded successfully" -ForegroundColor Green
    Write-Host "    Schema version: $($manifest.schema_version)" -ForegroundColor Gray
    Write-Host "    Last updated: $($manifest.last_updated)" -ForegroundColor Gray
}
catch {
    Write-Host "  ERROR: Failed to parse manifest.json: $_" -ForegroundColor Red
    exit 1
}

# Extract latest file info from manifest
$latestInfo = $manifest.latest
$latestRelativePath = $latestInfo.path
$latestFullPath = $latestInfo.full_path
$expectedRecords = $latestInfo.record_count
$expectedCases = $latestInfo.unique_cases
$dateRangeStart = $latestInfo.date_range.start
$dateRangeEnd = $latestInfo.date_range.end
$runType = $latestInfo.run_type

Write-Host ""
Write-Host "  Latest file from manifest:" -ForegroundColor White
Write-Host "    Relative path: $latestRelativePath" -ForegroundColor Gray
Write-Host "    Full path: $latestFullPath" -ForegroundColor Gray
Write-Host "    Expected records: $($expectedRecords.ToString('N0'))" -ForegroundColor Gray
Write-Host "    Unique cases: $($expectedCases.ToString('N0'))" -ForegroundColor Gray
Write-Host "    Date range: $dateRangeStart to $dateRangeEnd" -ForegroundColor Gray
Write-Host "    Run type: $runType" -ForegroundColor Gray
Write-Host ""

# ================================================================
# STEP 2: Verify source file exists and get info
# ================================================================
Write-Host "[Step 2] Verifying source file..." -ForegroundColor Yellow

if (Test-Path $latestFullPath) {
    $sourceInfo = Get-Item $latestFullPath
    Write-Host "  OK Source file found" -ForegroundColor Green
    Write-Host "    Path: $latestFullPath" -ForegroundColor Gray
    Write-Host "    Size: $([math]::Round($sourceInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
    Write-Host "    Last Modified: $($sourceInfo.LastWriteTime)" -ForegroundColor Gray
    Write-Host ""
}
else {
    Write-Host "  ERROR: Source file not found: $latestFullPath" -ForegroundColor Red
    Write-Host "    Manifest points to a file that doesn't exist" -ForegroundColor Yellow
    Write-Host "    Please run consolidation to generate the file" -ForegroundColor Yellow
    exit 1
}

# ================================================================
# STEP 3: Check server connectivity
# ================================================================
Write-Host "[Step 3] Checking server connectivity..." -ForegroundColor Yellow

$pingResult = Test-Connection -ComputerName $serverIP -Count 2 -Quiet -ErrorAction SilentlyContinue
if ($pingResult) {
    Write-Host "  OK Server $serverName ($serverIP) is reachable" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "  ERROR: Server $serverName ($serverIP) is NOT reachable" -ForegroundColor Red
    Write-Host "    Please verify network connection or VPN" -ForegroundColor Yellow
    exit 1
}

# ================================================================
# STEP 4: Check ESRI share access
# ================================================================
Write-Host "[Step 4] Checking ESRI share access..." -ForegroundColor Yellow

if (Test-Path $destESRIShare) {
    Write-Host "  OK ESRI share is accessible: $destESRIShare" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "  ERROR: ESRI share is NOT accessible: $destESRIShare" -ForegroundColor Red
    Write-Host "    Please verify share permissions" -ForegroundColor Yellow
    exit 1
}

# ================================================================
# STEP 5: Copy file to ESRI share with friendly filename
# ================================================================
$destFileFriendly = Join-Path $destESRIShare "CAD_Consolidated_2019_2026.xlsx"
$destFileOriginal = Join-Path $destESRIShare (Split-Path $latestFullPath -Leaf)

Write-Host "[Step 5] Copying file to ESRI share (friendly filename)..." -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "  [DRY RUN] Would copy to: $destFileFriendly" -ForegroundColor Yellow
}
else {
    try {
        Copy-Item -Path $latestFullPath -Destination $destFileFriendly -Force -ErrorAction Stop
        Write-Host "  OK File copied successfully" -ForegroundColor Green
        Write-Host "    Destination: $destFileFriendly" -ForegroundColor Gray

        if (Test-Path $destFileFriendly) {
            $destInfo = Get-Item $destFileFriendly
            Write-Host "    Size: $([math]::Round($destInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
            Write-Host "    Copied: $($destInfo.LastWriteTime)" -ForegroundColor Gray
        }
        Write-Host ""
    }
    catch {
        Write-Host "  ERROR: Failed to copy file: $_" -ForegroundColor Red
        Write-Host ""
    }
}

# ================================================================
# STEP 6: Copy file with original filename (for ArcPy reference)
# ================================================================
Write-Host "[Step 6] Copying file to ESRI share (original filename)..." -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "  [DRY RUN] Would copy to: $destFileOriginal" -ForegroundColor Yellow
}
else {
    try {
        Copy-Item -Path $latestFullPath -Destination $destFileOriginal -Force -ErrorAction Stop
        Write-Host "  OK File copied successfully" -ForegroundColor Green
        Write-Host "    Destination: $destFileOriginal" -ForegroundColor Gray

        if (Test-Path $destFileOriginal) {
            $destInfo = Get-Item $destFileOriginal
            Write-Host "    Size: $([math]::Round($destInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
            Write-Host "    Copied: $($destInfo.LastWriteTime)" -ForegroundColor Gray
        }
        Write-Host ""
    }
    catch {
        Write-Host "  ERROR: Failed to copy file: $_" -ForegroundColor Red
        Write-Host ""
    }
}

# ================================================================
# STEP 7: Verify copy integrity (file size comparison)
# ================================================================
Write-Host "[Step 7] Verifying copy integrity..." -ForegroundColor Yellow

if (-not $DryRun) {
    $sourceSize = (Get-Item $latestFullPath).Length
    $destExists = Test-Path $destFileFriendly

    if ($destExists) {
        $destSize = (Get-Item $destFileFriendly).Length

        if ($sourceSize -eq $destSize) {
            Write-Host "  OK File sizes match: $([math]::Round($sourceSize / 1MB, 2)) MB" -ForegroundColor Green
        }
        else {
            Write-Host "  WARNING: File size mismatch!" -ForegroundColor Yellow
            Write-Host "    Source: $([math]::Round($sourceSize / 1MB, 2)) MB ($sourceSize bytes)" -ForegroundColor Gray
            Write-Host "    Dest:   $([math]::Round($destSize / 1MB, 2)) MB ($destSize bytes)" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  WARNING: Destination file not found for verification" -ForegroundColor Yellow
    }
    Write-Host ""
}
else {
    Write-Host "  [DRY RUN] Skipping verification" -ForegroundColor Yellow
    Write-Host ""
}

# ================================================================
# SUMMARY
# ================================================================
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "COPY OPERATION COMPLETE" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dataset Information (from manifest):" -ForegroundColor White
Write-Host "  Source: $latestRelativePath" -ForegroundColor Gray
Write-Host "  Records: $($expectedRecords.ToString('N0'))" -ForegroundColor Gray
Write-Host "  Unique Cases: $($expectedCases.ToString('N0'))" -ForegroundColor Gray
Write-Host "  Date Range: $dateRangeStart to $dateRangeEnd" -ForegroundColor Gray
Write-Host "  Run Type: $runType" -ForegroundColor Gray
Write-Host ""
Write-Host "Files Available On Server:" -ForegroundColor White
Write-Host "  Network Share: $destFileFriendly" -ForegroundColor Cyan
Write-Host "  Network Share: $destFileOriginal" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. Connect to server via Remote Desktop ($serverName)" -ForegroundColor Gray
Write-Host "  2. Run ArcPy import script:" -ForegroundColor Gray
Write-Host "     docs/arcgis/import_cad_polished_to_geodatabase.py" -ForegroundColor Cyan
Write-Host "  3. Or manually import via ArcGIS Pro" -ForegroundColor Gray
Write-Host "  4. Verify $($expectedRecords.ToString('N0')) records imported correctly" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation:" -ForegroundColor White
Write-Host "  docs/arcgis/README.md - ArcGIS import guide" -ForegroundColor Gray
Write-Host "  REMOTE_SERVER_GUIDE.md - Comprehensive server guide" -ForegroundColor Gray
Write-Host "  13_PROCESSED_DATA/manifest.json - Latest file registry" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
