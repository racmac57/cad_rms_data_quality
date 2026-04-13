<#
.SYNOPSIS
    Copy polished CAD data from local machine to server
    
.DESCRIPTION
    Robust file copy from local workstation to HPD ESRI server using robocopy.
    Reads latest polished file path from manifest.json.
    Supports SMB shares, admin shares, and retry logic.
    
.PARAMETER ManifestPath
    Path to manifest.json containing latest polished file info
    Default: C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\manifest.json
    
.PARAMETER Destination
    Destination path on server
    Default: \\HPD2022LAWSOFT\c$\HPD ESRI\03_Data\CAD\Backfill\
    
.PARAMETER DryRun
    Test mode - shows what would be copied without executing
    
.PARAMETER UseAdminShare
    Use admin share (c$) instead of SMB share (fallback option)
    
.EXAMPLE
    .\Copy-PolishedToServer.ps1
    
.EXAMPLE
    .\Copy-PolishedToServer.ps1 -DryRun
    
.EXAMPLE
    .\Copy-PolishedToServer.ps1 -Destination "\\HPD2022LAWSOFT\HPD_ESRI_Backfill\"
    
.NOTES
    Author: R. A. Carucci
    Date: 2026-02-02
    Version: 1.0.0
#>

param(
    [string]$ManifestPath = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\manifest.json",
    [string]$Destination = "\\HPD2022LAWSOFT\c$\HPD ESRI\03_Data\CAD\Backfill\",
    [switch]$DryRun,
    [switch]$UseAdminShare
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "COPY POLISHED CAD DATA TO SERVER" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Load manifest to get latest polished file
Write-Host "[1] Loading manifest..." -ForegroundColor Yellow

if (-not (Test-Path $ManifestPath)) {
    Write-Host "    ✗ ERROR: Manifest not found: $ManifestPath" -ForegroundColor Red
    exit 1
}

try {
    $manifest = Get-Content $ManifestPath | ConvertFrom-Json
    $sourceFile = $manifest.latest.full_path
    $recordCount = $manifest.latest.record_count
    $runType = $manifest.latest.run_type
    $timestamp = $manifest.latest.timestamp
    
    Write-Host "    ✓ Manifest loaded" -ForegroundColor Green
    Write-Host "    Latest file: $sourceFile" -ForegroundColor Cyan
    Write-Host "    Record count: $recordCount" -ForegroundColor Cyan
    Write-Host "    Run type: $runType" -ForegroundColor Cyan
    Write-Host "    Timestamp: $timestamp" -ForegroundColor Cyan
    
}
catch {
    Write-Host "    ✗ ERROR: Failed to parse manifest: $_" -ForegroundColor Red
    exit 1
}

# Verify source file exists
Write-Host ""
Write-Host "[2] Verifying source file..." -ForegroundColor Yellow

if (-not (Test-Path $sourceFile)) {
    Write-Host "    ✗ ERROR: Source file not found: $sourceFile" -ForegroundColor Red
    exit 2
}

$sourceSize = (Get-Item $sourceFile).Length / 1MB
Write-Host "    ✓ Source file exists" -ForegroundColor Green
Write-Host "    Size: $([int]$sourceSize) MB" -ForegroundColor Cyan

# Test destination accessibility
Write-Host ""
Write-Host "[3] Testing destination accessibility..." -ForegroundColor Yellow

if ($UseAdminShare) {
    Write-Host "    Using admin share (c$)" -ForegroundColor Yellow
}
else {
    Write-Host "    Attempting to use SMB share first..." -ForegroundColor Yellow
    # Try SMB share first (you'll need to update this path if IT creates a dedicated share)
    $smbShare = "\\HPD2022LAWSOFT\HPD_ESRI_Backfill\"
    
    if (Test-Path $smbShare -ErrorAction SilentlyContinue) {
        $Destination = $smbShare
        Write-Host "    ✓ SMB share accessible: $Destination" -ForegroundColor Green
    }
    else {
        Write-Host "    ⚠ SMB share not accessible, falling back to admin share" -ForegroundColor Yellow
        $Destination = "\\HPD2022LAWSOFT\c$\HPD ESRI\03_Data\CAD\Backfill\"
    }
}

# Test write access
try {
    $testFile = Join-Path $Destination "_writetest.tmp"
    "test" | Out-File $testFile -Force
    Remove-Item $testFile -Force
    Write-Host "    ✓ Destination is writable: $Destination" -ForegroundColor Green
}
catch {
    Write-Host "    ✗ ERROR: Cannot write to destination: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Verify you have permissions to the server share" -ForegroundColor Yellow
    Write-Host "2. Try running PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host "3. Check if server is accessible: Test-NetConnection HPD2022LAWSOFT" -ForegroundColor Yellow
    Write-Host "4. Ask IT to create a dedicated SMB share for better reliability" -ForegroundColor Yellow
    exit 3
}

# Prepare robocopy parameters
Write-Host ""
Write-Host "[4] Preparing file copy..." -ForegroundColor Yellow

$sourceDir = Split-Path $sourceFile -Parent
$sourceFileName = Split-Path $sourceFile -Leaf

# Robocopy parameters
# /R:3 = Retry 3 times on failed copies
# /W:5 = Wait 5 seconds between retries
# /NP = No progress (cleaner output)
# /NDL = No directory list
# /NFL = No file list (we'll add our own summary)
# /BYTES = Show sizes in bytes
# /TEE = Output to console and log file

$logFile = Join-Path ([System.IO.Path]::GetTempPath()) "robocopy_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

Write-Host "    Source: $sourceDir" -ForegroundColor Cyan
Write-Host "    File: $sourceFileName" -ForegroundColor Cyan
Write-Host "    Destination: $Destination" -ForegroundColor Cyan
Write-Host "    Log: $logFile" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host ""
    Write-Host "[DRY RUN] Would execute robocopy:" -ForegroundColor Yellow
    Write-Host "    robocopy ""$sourceDir"" ""$Destination"" ""$sourceFileName"" /R:3 /W:5 /NP /NDL /TEE /LOG:""$logFile""" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✓ Dry run completed - no files copied" -ForegroundColor Green
    exit 0
}

# Execute robocopy
Write-Host ""
Write-Host "[5] Copying file with robocopy..." -ForegroundColor Yellow
Write-Host "    This may take several minutes for large files..." -ForegroundColor Cyan
Write-Host ""

$robocopyArgs = @(
    """$sourceDir"""
    """$Destination"""
    """$sourceFileName"""
    "/R:3"
    "/W:5"
    "/NP"
    "/NDL"
    "/TEE"
    "/LOG:""$logFile"""
)

$robocopyCmd = "robocopy $($robocopyArgs -join ' ')"
Write-Host "    Command: $robocopyCmd" -ForegroundColor Cyan
Write-Host ""

# Run robocopy
$robocopyProcess = Start-Process -FilePath "robocopy.exe" -ArgumentList $robocopyArgs -NoNewWindow -Wait -PassThru

# Robocopy exit codes:
# 0 = No files copied (file already exists and is up-to-date)
# 1 = Files copied successfully
# 2 = Extra files or directories detected
# 4 = Mismatched files detected
# 8+ = Failure
$exitCode = $robocopyProcess.ExitCode

Write-Host ""
Write-Host "[6] Robocopy completed with exit code: $exitCode" -ForegroundColor Cyan

if ($exitCode -ge 8) {
    Write-Host "    ✗ ERROR: Robocopy failed" -ForegroundColor Red
    Write-Host "    Check log file: $logFile" -ForegroundColor Red
    exit 4
}
elseif ($exitCode -eq 0) {
    Write-Host "    ✓ No copy needed (file is already up-to-date on server)" -ForegroundColor Green
}
elseif ($exitCode -le 3) {
    Write-Host "    ✓ File copied successfully" -ForegroundColor Green
}
else {
    Write-Host "    ⚠ WARNING: Copy completed with warnings (code: $exitCode)" -ForegroundColor Yellow
}

# Verify copy
Write-Host ""
Write-Host "[7] Verifying file integrity..." -ForegroundColor Yellow

$destFile = Join-Path $Destination $sourceFileName

if (-not (Test-Path $destFile)) {
    Write-Host "    ✗ ERROR: Destination file not found after copy" -ForegroundColor Red
    exit 5
}

$destSize = (Get-Item $destFile).Length / 1MB
$sourceSize = (Get-Item $sourceFile).Length / 1MB

Write-Host "    Source size: $([int]$sourceSize) MB" -ForegroundColor Cyan
Write-Host "    Dest size: $([int]$destSize) MB" -ForegroundColor Cyan

if ([int]$sourceSize -eq [int]$destSize) {
    Write-Host "    ✓ File sizes match" -ForegroundColor Green
}
else {
    Write-Host "    ✗ ERROR: File size mismatch" -ForegroundColor Red
    exit 5
}

# Optional: Hash verification (commented out for speed, uncomment if needed)
# Write-Host "    Computing file hashes (this may take a while)..." -ForegroundColor Cyan
# $sourceHash = (Get-FileHash $sourceFile -Algorithm SHA256).Hash
# $destHash = (Get-FileHash $destFile -Algorithm SHA256).Hash
# if ($sourceHash -eq $destHash) {
#     Write-Host "    ✓ File hashes match" -ForegroundColor Green
# } else {
#     Write-Host "    ✗ ERROR: File hash mismatch" -ForegroundColor Red
#     exit 5
# }

# SUCCESS
Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host "✓ FILE COPIED SUCCESSFULLY" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host "Source: $sourceFile" -ForegroundColor Cyan
Write-Host "Destination: $destFile" -ForegroundColor Cyan
Write-Host "Size: $([int]$sourceSize) MB" -ForegroundColor Cyan
Write-Host "Record count: $recordCount" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Connect to server via RDP: mstsc /v:HPD2022LAWSOFT" -ForegroundColor Yellow
Write-Host "2. Run backfill publish orchestrator:" -ForegroundColor Yellow
Write-Host "   cd ""C:\HPD ESRI\04_Scripts""" -ForegroundColor Yellow
Write-Host "   .\Invoke-CADBackfillPublish.ps1 -BackfillFile ""$destFile""" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Green

exit 0
