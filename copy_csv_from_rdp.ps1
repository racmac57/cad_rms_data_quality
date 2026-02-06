################################################################################
# Copy CFSTable CSV from RDP Server to Local Machine
# Purpose: Transfer large CSV export from RDP temp directory to local consolidation output
# Author: Auto-generated for Phone/911 fix session
# Date: 2026-02-04
################################################################################

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$RDPServerName = "HPD-ESRI-01",  # Update this with your RDP server name/IP
    
    [Parameter(Mandatory = $false)]
    [string]$SourcePath = "C:\Temp\CFSTable_2019_2026_FULL_20260203_231437.csv",
    
    [Parameter(Mandatory = $false)]
    [string]$DestinationPath = "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\consolidation\output\CFSTable_2019_2026_FULL_20260203_231437.csv",
    
    [Parameter(Mandatory = $false)]
    [switch]$UseUNCPath,
    
    [Parameter(Mandatory = $false)]
    [switch]$VerifyAfterCopy = $true
)

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "Copy CSV from RDP Server to Local Machine" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan

# Ensure destination directory exists
$destDir = Split-Path -Parent $DestinationPath
if (-not (Test-Path $destDir)) {
    Write-Host "`n[INFO] Creating destination directory..." -ForegroundColor Yellow
    New-Item -Path $destDir -ItemType Directory -Force | Out-Null
    Write-Host "  Created: $destDir" -ForegroundColor Green
}

Write-Host "`n[INFO] Copy Configuration:" -ForegroundColor White
Write-Host "  Source (RDP): $SourcePath" -ForegroundColor White
Write-Host "  Destination:  $DestinationPath" -ForegroundColor White

# Method 1: Try UNC Path if server name is provided and UseUNCPath is set
if ($UseUNCPath -and $RDPServerName) {
    Write-Host "`n[METHOD] Using UNC Path..." -ForegroundColor Cyan
    
    # Convert to UNC path
    $uncPath = "\\$RDPServerName\$($SourcePath -replace ':', '$')"
    Write-Host "  UNC Path: $uncPath" -ForegroundColor White
    
    if (Test-Path $uncPath) {
        Write-Host "`n[COPY] Starting robocopy..." -ForegroundColor Yellow
        
        $sourceDir = Split-Path -Parent $uncPath
        $fileName = Split-Path -Leaf $uncPath
        
        robocopy $sourceDir $destDir $fileName /Z /R:3 /W:5 /NFL /NDL /NP
        
        if ($LASTEXITCODE -le 7) {
            Write-Host "`n[SUCCESS] File copied via UNC path!" -ForegroundColor Green
            $copySuccess = $true
        }
        else {
            Write-Host "`n[ERROR] Robocopy failed with exit code: $LASTEXITCODE" -ForegroundColor Red
            $copySuccess = $false
        }
    }
    else {
        Write-Host "`n[WARNING] UNC path not accessible: $uncPath" -ForegroundColor Yellow
        Write-Host "  Falling back to manual instructions..." -ForegroundColor Yellow
        $copySuccess = $false
    }
}
# Method 2: Try RDP drive redirection (if C: is mapped as \\tsclient\C in RDP)
else {
    Write-Host "`n[METHOD] Attempting RDP drive redirection..." -ForegroundColor Cyan
    
    # Check if this is being run FROM the RDP session
    $isRDP = $env:SESSIONNAME -like "RDP*"
    
    if ($isRDP) {
        Write-Host "  Detected: Running FROM RDP session" -ForegroundColor Yellow
        
        # Try to access local machine via \\tsclient\C
        $localPath = "\\tsclient\C\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\consolidation\output"
        
        if (Test-Path $localPath) {
            Write-Host "  Found local machine path via \\tsclient\C" -ForegroundColor Green
            
            $fullDestPath = Join-Path $localPath (Split-Path -Leaf $SourcePath)
            
            Write-Host "`n[COPY] Starting copy..." -ForegroundColor Yellow
            Copy-Item -Path $SourcePath -Destination $fullDestPath -Force -Verbose
            
            if ($?) {
                Write-Host "`n[SUCCESS] File copied via tsclient redirection!" -ForegroundColor Green
                $copySuccess = $true
                $DestinationPath = $fullDestPath
            }
            else {
                Write-Host "`n[ERROR] Copy failed" -ForegroundColor Red
                $copySuccess = $false
            }
        }
        else {
            Write-Host "  \\tsclient\C not accessible from RDP session" -ForegroundColor Yellow
            $copySuccess = $false
        }
    }
    # Running from local machine
    else {
        Write-Host "  Detected: Running from LOCAL machine" -ForegroundColor Yellow
        Write-Host "  Cannot access RDP server's C:\Temp directly" -ForegroundColor Red
        $copySuccess = $false
    }
}

# Method 3: Manual instructions if automated methods fail
if (-not $copySuccess) {
    Write-Host "`n" + "="*80 -ForegroundColor Yellow
    Write-Host "MANUAL COPY REQUIRED" -ForegroundColor Yellow
    Write-Host "="*80 -ForegroundColor Yellow
    
    Write-Host "`n[INSTRUCTIONS] Please copy manually using one of these methods:" -ForegroundColor White
    
    Write-Host "`n1. Using RDP Session File Explorer:" -ForegroundColor Cyan
    Write-Host "   a. In your RDP session, open File Explorer" -ForegroundColor White
    Write-Host "   b. Navigate to: $SourcePath" -ForegroundColor White
    Write-Host "   c. Copy the file (Ctrl+C)" -ForegroundColor White
    Write-Host "   d. Navigate to your local machine (usually \\tsclient\C\...)" -ForegroundColor White
    Write-Host "   e. Paste to: $destDir" -ForegroundColor White
    
    Write-Host "`n2. Using Local Machine File Explorer:" -ForegroundColor Cyan
    Write-Host "   a. On your local machine, connect to RDP server via network share" -ForegroundColor White
    Write-Host "   b. Navigate to: \\$RDPServerName\C$\Temp (requires admin access)" -ForegroundColor White
    Write-Host "   c. Copy: CFSTable_2019_2026_FULL_20260203_231437.csv" -ForegroundColor White
    Write-Host "   d. Paste to: $destDir" -ForegroundColor White
    
    Write-Host "`n3. Using Shared Network Drive:" -ForegroundColor Cyan
    Write-Host "   If you have a shared network drive accessible from both:" -ForegroundColor White
    Write-Host "   a. From RDP: Copy $SourcePath to shared drive" -ForegroundColor White
    Write-Host "   b. From Local: Copy from shared drive to $destDir" -ForegroundColor White
    
    Write-Host "`n[INFO] Expected file size: ~168 MB (171,546 KB)" -ForegroundColor White
    Write-Host "`n" + "="*80 -ForegroundColor Yellow
    
    exit 1
}

# Verify copy if successful
if ($copySuccess -and $VerifyAfterCopy) {
    Write-Host "`n[VERIFY] Checking copied file..." -ForegroundColor Cyan
    
    if (Test-Path $DestinationPath) {
        $destFile = Get-Item $DestinationPath
        $destSizeKB = [math]::Round($destFile.Length / 1KB, 0)
        $destSizeMB = [math]::Round($destFile.Length / 1MB, 2)
        
        Write-Host "  File exists: $DestinationPath" -ForegroundColor Green
        Write-Host "  Size: $destSizeMB MB ($destSizeKB KB)" -ForegroundColor Green
        Write-Host "  Modified: $($destFile.LastWriteTime)" -ForegroundColor Green
        
        # Check if size matches expected (~171,546 KB)
        if ($destSizeKB -gt 170000 -and $destSizeKB -lt 173000) {
            Write-Host "`n[SUCCESS] File size matches expected range!" -ForegroundColor Green
        }
        else {
            Write-Host "`n[WARNING] File size unexpected. Expected ~171,546 KB, got $destSizeKB KB" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  [ERROR] File not found at destination!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "CSV Export Copy Complete!" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green
Write-Host "`n[NEXT STEPS]" -ForegroundColor Cyan
Write-Host "1. Verify file: $DestinationPath" -ForegroundColor White
Write-Host "2. Run validation scripts from NEXT_ACTIONS_PHONE911_FIX.md" -ForegroundColor White
Write-Host "3. Begin comprehensive data quality checks" -ForegroundColor White
Write-Host "`n"
