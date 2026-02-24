# Run geocoding for December 2025 CAD data only (~5-15 min).
# Requires ArcGIS Pro (propy). Run from repo root.
# Output: 13_PROCESSED_DATA\ESRI_Polished\cached\december_2025\2025_12_CAD_GEO_CACHED.xlsx

$ErrorActionPreference = "Stop"
$repoRoot = $PSScriptRoot
$scriptsDir = Join-Path $repoRoot "scripts"
$propy = "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"

if (-not (Test-Path $propy)) {
    Write-Host "ArcGIS Pro Python not found at: $propy" -ForegroundColor Red
    Write-Host "Install ArcGIS Pro or run create_geocoding_cache.py with --input and --output-name manually." -ForegroundColor Yellow
    exit 1
}

$decInput = Join-Path $env:USERPROFILE "OneDrive - City of Hackensack\05_EXPORTS\_CAD\monthly\2025\2025_12_CAD.xlsx"
if (-not (Test-Path $decInput)) {
    Write-Host "December 2025 file not found: $decInput" -ForegroundColor Red
    exit 2
}

$outDir = Join-Path $env:USERPROFILE "OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\cached\december_2025"
$outName = "2025_12_CAD_GEO_CACHED.xlsx"

Write-Host "Geocoding December 2025 CAD data..." -ForegroundColor Cyan
Write-Host "  Input:  $decInput" -ForegroundColor Gray
Write-Host "  Output: $outDir\$outName" -ForegroundColor Gray
Write-Host ""

& $propy (Join-Path $scriptsDir "create_geocoding_cache.py") --input $decInput --output-dir $outDir --output-name $outName
$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "Done. Geocoded file: $outDir\$outName" -ForegroundColor Green
}
exit $exitCode
