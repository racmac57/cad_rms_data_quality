# Quick: List all baseline files with their date ranges
#
# Usage: .\list_baselines.ps1

$baseDir = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base"

Write-Host ""
Write-Host "BASELINE FILES:" -ForegroundColor Cyan
Write-Host "Location: $baseDir" -ForegroundColor Gray
Write-Host ""

Get-ChildItem $baseDir -Filter "*.xlsx" | 
Sort-Object LastWriteTime -Descending |
ForEach-Object {
    $name = $_.Name
    $sizeMB = [math]::Round($_.Length / 1MB, 1)
    $modified = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
        
    # Extract date range from filename if present
    if ($name -match "_(\d{8})_(\d{8})\.xlsx$") {
        $startDate = $matches[1]
        $endDate = $matches[2]
        $startFormatted = "$($startDate.Substring(0,4))-$($startDate.Substring(4,2))-$($startDate.Substring(6,2))"
        $endFormatted = "$($endDate.Substring(0,4))-$($endDate.Substring(4,2))-$($endDate.Substring(6,2))"
            
        Write-Host "📅 $startFormatted to $endFormatted" -ForegroundColor Green
        Write-Host "   $name" -ForegroundColor White
        Write-Host "   Size: $sizeMB MB | Modified: $modified" -ForegroundColor Gray
    }
    elseif ($name -eq "CAD_ESRI_Polished_Baseline.xlsx") {
        Write-Host "📌 CURRENT (Generic Pointer)" -ForegroundColor Cyan
        Write-Host "   $name" -ForegroundColor White
        Write-Host "   Size: $sizeMB MB | Modified: $modified" -ForegroundColor Gray
    }
    else {
        Write-Host "📄 $name" -ForegroundColor Yellow
        Write-Host "   Size: $sizeMB MB | Modified: $modified" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "Tip: The versioned filename shows the date range!" -ForegroundColor Yellow
Write-Host "     Example: CAD_ESRI_Polished_Baseline_20190101_20260202.xlsx" -ForegroundColor Gray
Write-Host "              means data from 2019-01-01 to 2026-02-02" -ForegroundColor Gray
Write-Host ""
