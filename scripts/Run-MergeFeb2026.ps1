# Merge 2026_02_CAD.xlsx (02/01-02/15) into baseline. Run from repo root or scripts folder.
# Uses correct-schema baseline (20260203) so output matches ESRI polished schema for backfill.
$ErrorActionPreference = "Stop"
$ProjectRoot = "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
$BaseDir = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base"
$BackfillFile = "C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\monthly\2026\2026_02_CAD.xlsx"
# Baseline with correct schema (same columns/order as backfill script expects)
$BaselineCorrectSchema = Join-Path $BaseDir "CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx"

Set-Location $ProjectRoot
if (-not (Test-Path $BackfillFile)) {
    Write-Error "Backfill file not found: $BackfillFile"
    exit 1
}
if (-not (Test-Path $BaselineCorrectSchema)) {
    Write-Error "Correct-schema baseline not found: $BaselineCorrectSchema"
    exit 1
}

# Dry run first
Write-Host "=== DRY RUN ===" -ForegroundColor Cyan
& python scripts/backfill_gap_analysis.py --merge --baseline $BaselineCorrectSchema --backfill $BackfillFile --dry-run
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$confirm = Read-Host "Proceed with actual merge? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Cancelled."
    exit 0
}

Write-Host "`n=== MERGE ===" -ForegroundColor Cyan
& python scripts/backfill_gap_analysis.py --merge --baseline $BaselineCorrectSchema --backfill $BackfillFile
exit $LASTEXITCODE
