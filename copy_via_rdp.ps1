# ================================================================
# ALTERNATIVE: Copy CAD Dataset via RDP Session
# ================================================================
# Use this if network copy fails due to permissions
# Date: 2026-01-31
# ================================================================

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "ALTERNATIVE COPY METHOD - VIA RDP SESSION" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$sourceFile = "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final\CAD_ESRI_POLISHED_20260131_004142.xlsx"
$serverIP = "10.0.0.157"
$serverName = "HPD2022LAWSOFT"

Write-Host "INSTRUCTIONS FOR MANUAL COPY:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Step 1: Connect to Remote Server" -ForegroundColor White
Write-Host "  - Open Remote Desktop Connection (mstsc.exe)" -ForegroundColor Gray
Write-Host "  - Server: $serverName or $serverIP" -ForegroundColor Cyan
Write-Host "  - Connect using your administrator credentials" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 2: Access Source File on Local Machine" -ForegroundColor White
Write-Host "  Option A - Via OneDrive (if synced):" -ForegroundColor Gray
Write-Host "    C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final\" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Option B - Via Network Share (map this on server):" -ForegroundColor Gray
Write-Host "    \\YOUR-MACHINE-NAME\c$\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final\" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Option C - Copy to USB drive or shared folder first" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 3: Copy File to Server (while in RDP session)" -ForegroundColor White
Write-Host "  Destination Option 1:" -ForegroundColor Gray
Write-Host "    C:\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Destination Option 2:" -ForegroundColor Gray
Write-Host "    C:\HPD ESRI\03_Data\CAD\CAD_Consolidated_2019_2026.xlsx" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 4: Verify Copy" -ForegroundColor White
Write-Host "  - Check file size: Should be ~70-74 MB" -ForegroundColor Gray
Write-Host "  - Right-click file > Properties" -ForegroundColor Gray
Write-Host "  - Verify timestamp is recent" -ForegroundColor Gray
Write-Host ""

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "POWERSHELL COMMANDS TO RUN ON SERVER (in RDP session)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "# Verify destination folder exists" -ForegroundColor Gray
Write-Host 'Test-Path "C:\ESRIExport\LawEnforcementDataManagement_New"' -ForegroundColor Cyan
Write-Host ""

Write-Host "# List current files in destination" -ForegroundColor Gray
Write-Host 'Get-ChildItem "C:\ESRIExport\LawEnforcementDataManagement_New\*.xlsx" | Select-Object Name, Length, LastWriteTime' -ForegroundColor Cyan
Write-Host ""

Write-Host "# After copying, verify new file" -ForegroundColor Gray
Write-Host 'Get-Item "C:\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx" | ' -ForegroundColor Cyan
Write-Host '    Select-Object Name, @{N="Size (MB)";E={[math]::Round($_.Length/1MB,2)}}, LastWriteTime' -ForegroundColor Cyan
Write-Host ""

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we can copy via admin share
Write-Host "Attempting copy via admin share (C$)..." -ForegroundColor Yellow
$adminSharePath = "\\$serverName\c$\ESRIExport\LawEnforcementDataManagement_New"

if (Test-Path $adminSharePath) {
    Write-Host "  OK Admin share is accessible: $adminSharePath" -ForegroundColor Green
    Write-Host ""
    
    $destFile = "$adminSharePath\CAD_Consolidated_2019_2026.xlsx"
    
    Write-Host "  Attempting to copy file..." -ForegroundColor Yellow
    try {
        Copy-Item -Path $sourceFile -Destination $destFile -Force -ErrorAction Stop
        Write-Host "  SUCCESS File copied via admin share!" -ForegroundColor Green
        Write-Host "    Destination: $destFile" -ForegroundColor Gray
        
        if (Test-Path $destFile) {
            $destInfo = Get-Item $destFile
            Write-Host "    Size: $([math]::Round($destInfo.Length / 1MB, 2)) MB" -ForegroundColor Gray
            Write-Host "    Copied: $($destInfo.LastWriteTime)" -ForegroundColor Gray
        }
        Write-Host ""
        Write-Host "  File successfully copied to server!" -ForegroundColor Green
        Write-Host "  You can now use it in ArcGIS Pro" -ForegroundColor Green
        Write-Host ""
    }
    catch {
        Write-Host "  ERROR Failed to copy via admin share: $_" -ForegroundColor Red
        Write-Host "  Please use manual copy method via RDP (see instructions above)" -ForegroundColor Yellow
        Write-Host ""
    }
}
else {
    Write-Host "  WARNING Admin share not accessible: $adminSharePath" -ForegroundColor Yellow
    Write-Host "  Please use manual copy method via RDP (see instructions above)" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "DATASET INFORMATION" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Source File:" -ForegroundColor White
Write-Host "  $sourceFile" -ForegroundColor Gray
Write-Host ""
Write-Host "Dataset Details:" -ForegroundColor White
Write-Host "  Records: 716,420" -ForegroundColor Gray
Write-Host "  Unique Cases: 553,624" -ForegroundColor Gray
Write-Host "  Date Range: 2019-01-01 to 2026-01-16" -ForegroundColor Gray
Write-Host "  Size: ~70-74 MB" -ForegroundColor Gray
Write-Host "  Schema: 20 ESRI columns" -ForegroundColor Gray
Write-Host "  Quality: EXCELLENT (99.9%+ completeness)" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
