# 🕒 2026-02-16-17-05-00 (EST)
# cad_rms_data_quality/Convert-ExcelToCSV.ps1
# Author: R. A. Carucci
# Purpose: Convert ESRI_CADExport.xlsx to CSV for RDP deployment

$sourcePath = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx"
$outputPath = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Export.csv"
$logPath = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\Conversion_Log.txt"

# Clear old log
if (Test-Path $logPath) { Remove-Item $logPath }

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
    Add-Content -Path $logPath -Value $Message
}

Write-Log "==========================================================" "Cyan"
Write-Log "EXCEL TO CSV CONVERSION" "Cyan"
Write-Log "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Cyan"
Write-Log "==========================================================" "Cyan"
Write-Log ""

# Check if source file exists
if (-not (Test-Path $sourcePath)) {
    Write-Log "ERROR: Source file not found" "Red"
    Write-Log "Path: $sourcePath" "Red"
    Write-Log ""
    Write-Log "Press Enter to exit..."
    Read-Host
    exit 1
}

$fileInfo = Get-Item $sourcePath
Write-Log "[SOURCE FILE]" "Yellow"
Write-Log "  Path: $sourcePath" "White"
Write-Log "  Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" "White"
Write-Log "  Modified: $($fileInfo.LastWriteTime)" "White"
Write-Log ""

Write-Log "[STARTING CONVERSION]" "Yellow"
Write-Log "  Opening Excel..." "White"

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    
    Write-Log "  Loading workbook..." "White"
    $workbook = $excel.Workbooks.Open($sourcePath)
    $worksheet = $workbook.Sheets.Item(1)
    
    Write-Log "  Sheet name: $($worksheet.Name)" "White"
    Write-Log "  Row count: $($worksheet.UsedRange.Rows.Count)" "White"
    Write-Log "  Column count: $($worksheet.UsedRange.Columns.Count)" "White"
    Write-Log ""
    
    Write-Log "  Saving as CSV..." "White"
    # Format 6 = CSV, Format 23 = Text (Tab delimited), Format 24 = Unicode Text
    $worksheet.SaveAs($outputPath, 6)
    
    Write-Log "  Closing workbook..." "White"
    $workbook.Close($false)
    $excel.Quit()
    
    # Release COM objects
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($worksheet) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($workbook) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    
    Write-Log ""
    Write-Log "==========================================================" "Green"
    Write-Log "SUCCESS: CSV CREATED" "Green"
    Write-Log "==========================================================" "Green"
    
    if (Test-Path $outputPath) {
        $csvInfo = Get-Item $outputPath
        Write-Log "  Output: $outputPath" "Green"
        Write-Log "  Size: $([math]::Round($csvInfo.Length / 1MB, 2)) MB" "Green"
        Write-Log "  Created: $($csvInfo.CreationTime)" "Green"
    }
    
} catch {
    Write-Log ""
    Write-Log "==========================================================" "Red"
    Write-Log "ERROR DURING CONVERSION" "Red"
    Write-Log "==========================================================" "Red"
    Write-Log "Error Type: $($_.Exception.GetType().FullName)" "Red"
    Write-Log "Message: $($_.Exception.Message)" "Red"
    Write-Log "Line: $($_.InvocationInfo.ScriptLineNumber)" "Red"
    Write-Log "Stack Trace:" "Red"
    Write-Log $_.ScriptStackTrace "Red"
    Write-Log ""
    
    # Cleanup
    if ($workbook) { 
        try { $workbook.Close($false) } catch {}
    }
    if ($excel) { 
        try { $excel.Quit() } catch {}
    }
    
    Write-Log "Press Enter to exit..."
    Read-Host
    exit 1
}

Write-Log ""
Write-Log "Log saved to: $logPath" "Cyan"
Write-Log ""
Write-Log "Press Enter to exit..."
Read-Host
