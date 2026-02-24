# 🕒 2026-02-15-19-50-30 (EST)
# Hackensack_PD_ETL/File_Cleanup_Reorg.ps1
# Author: R. A. Carucci
# Purpose: Consolidate yearly CAD exports and remove redundant Geocode instances.

# --- CONFIGURATION ---
$basePath = "C:\Users\carucci_r\OneDrive - City of Hackensack"
$yearlyCadPath = Join-Path $basePath "05_EXPORTS\_CAD\yearly"
$masterGeocodePath = Join-Path $basePath "09_Reference\GeographicData\NJ_Geocode"
$logFile = Join-Path $basePath "05_EXPORTS\_CAD\cleanup_log_$(Get-Date -Format 'yyyyMMdd').txt"

Function Write-Log {
    Param([string]$Message)
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$stamp : $Message" | Out-File -FilePath $logFile -Append
}

Write-Host "Starting Law Enforcement Data Environment Optimization..." -ForegroundColor Cyan

# --- TASK 1: REORGANIZE YEARLY CAD EXPORTS ---
# Move 2019_CAD_ALL.xlsx from \yearly\2019\ to \yearly\
Write-Host "Step 1: Flattening Yearly CAD Directory Structure..." -ForegroundColor Yellow

$subFolders = Get-ChildItem -Path $yearlyCadPath -Directory
foreach ($folder in $subFolders) {
    $yearFiles = Get-ChildItem -Path $folder.FullName -Filter "*.xlsx"
    foreach ($file in $yearFiles) {
        $destPath = Join-Path $yearlyCadPath $file.Name
        if (-not (Test-Path $destPath)) {
            Write-Log "Moving $($file.Name) to root yearly folder."
            Move-Item -Path $file.FullName -Destination $destPath -Force
        }
        else {
            Write-Log "SKIP: $($file.Name) already exists in root yearly folder."
        }
    }
    # Optional: Remove empty subfolder if move was successful
    if ((Get-ChildItem -Path $folder.FullName).Count -eq 0) {
        Remove-Item -Path $folder.FullName -Force
        Write-Log "Removed empty directory: $($folder.Name)"
    }
}

# --- TASK 2: GEOCODE CLEANUP ---
# Verify master exists, then find and remove clones
Write-Host "Step 2: NJ_Geocode Verification and Redundancy Cleanup..." -ForegroundColor Yellow

if (Test-Path $masterGeocodePath) {
    $masterVersion = (Get-Item $masterGeocodePath).LastWriteTime
    Write-Log "Verified Master NJ_Geocode exists. Last Modified: $masterVersion"
    
    # Search for other instances of 'NJ_Geocode' on the local machine (excluding the master path)
    # Note: Scanning the whole C: drive may require Admin perms and take time.
    $potentialClones = Get-ChildItem -Path "C:\Users\carucci_r\" -Filter "NJ_Geocode" -Recurse -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullName -notlike "*$masterGeocodePath*" }

    foreach ($clone in $potentialClones) {
        Write-Log "Found redundant instance: $($clone.FullName). Removing..."
        # Uncomment the line below to enable actual deletion
        # Remove-Item -Path $clone.FullName -Recurse -Force 
        Write-Host "DELETED (Simulated): $($clone.FullName)" -ForegroundColor Gray
    }
}
else {
    Write-Host "CRITICAL ERROR: Master Geocode not found at $masterGeocodePath. Cleanup aborted." -ForegroundColor Red
    Write-Log "ERROR: Master Geocode missing. Cleanup cancelled to prevent data loss."
}

Write-Host "Optimization Complete. Check log: $logFile" -ForegroundColor Green