# Quick Baseline Info Display
# Shows date range, record count, and file details without opening Excel
#
# Usage: .\show_baseline_info.ps1

$ErrorActionPreference = "Stop"

$manifestPath = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\manifest.json"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   BASELINE DATASET INFO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $manifestPath)) {
    Write-Host "✗ Manifest not found: $manifestPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Run this first:" -ForegroundColor Yellow
    Write-Host "  python scripts/update_baseline_from_polished.py" -ForegroundColor White
    exit 1
}

try {
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    
    # Latest file info
    Write-Host "📊 LATEST BASELINE" -ForegroundColor Green
    Write-Host "  File: " -NoNewline
    Write-Host "$($manifest.latest.filename)" -ForegroundColor White
    Write-Host ""
    
    # Date range (the key info!)
    if ($manifest.latest.date_range) {
        Write-Host "📅 DATE RANGE" -ForegroundColor Green
        Write-Host "  Start: " -NoNewline
        Write-Host "$($manifest.latest.date_range.start)" -ForegroundColor White
        Write-Host "  End:   " -NoNewline
        Write-Host "$($manifest.latest.date_range.end)" -ForegroundColor White
        
        # Calculate days covered
        $startDate = [datetime]::Parse($manifest.latest.date_range.start)
        $endDate = [datetime]::Parse($manifest.latest.date_range.end)
        $days = ($endDate - $startDate).Days
        $years = [math]::Round($days / 365.25, 1)
        
        Write-Host "  Coverage: " -NoNewline
        Write-Host "$days days ($years years)" -ForegroundColor White
        Write-Host ""
    }
    
    # Record count
    if ($manifest.latest.record_count) {
        Write-Host "📈 RECORDS" -ForegroundColor Green
        Write-Host "  Total: " -NoNewline
        Write-Host "$($manifest.latest.record_count.ToString('N0'))" -ForegroundColor White
        Write-Host ""
    }
    
    # File info
    Write-Host "💾 FILE INFO" -ForegroundColor Green
    Write-Host "  Size: " -NoNewline
    Write-Host "$($manifest.latest.file_size_mb) MB" -ForegroundColor White
    Write-Host "  Updated: " -NoNewline
    $updateTime = [datetime]::Parse($manifest.latest.updated)
    Write-Host "$($updateTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
    Write-Host ""
    
    # File paths
    Write-Host "📁 LOCATIONS" -ForegroundColor Green
    Write-Host "  Generic: " -NoNewline
    Write-Host "$($manifest.latest.generic_path)" -ForegroundColor Gray
    Write-Host "  Versioned: " -NoNewline
    Write-Host "$($manifest.latest.full_path)" -ForegroundColor Gray
    Write-Host ""
    
    # Quick checks
    Write-Host "✓ STATUS CHECKS" -ForegroundColor Green
    
    # Check if files exist
    $genericExists = Test-Path $manifest.latest.generic_path
    $versionedExists = Test-Path $manifest.latest.full_path
    
    if ($genericExists) {
        Write-Host "  Generic pointer: " -NoNewline
        Write-Host "EXISTS ✓" -ForegroundColor Green
    }
    else {
        Write-Host "  Generic pointer: " -NoNewline
        Write-Host "MISSING ✗" -ForegroundColor Red
    }
    
    if ($versionedExists) {
        Write-Host "  Versioned archive: " -NoNewline
        Write-Host "EXISTS ✓" -ForegroundColor Green
    }
    else {
        Write-Host "  Versioned archive: " -NoNewline
        Write-Host "MISSING ✗" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
}
catch {
    Write-Host "✗ Error reading manifest: $_" -ForegroundColor Red
    exit 1
}
