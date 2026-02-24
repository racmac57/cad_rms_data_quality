# Run next steps after merge: update manifest from merged output, then deploy to RDP.
# Optionally run the merge first (with correct-schema baseline).
# Usage:
#   .\scripts\Do-NextSteps.ps1                    # Update manifest from latest in base, then deploy
#   .\scripts\Do-NextSteps.ps1 -RunMerge         # Run merge (dry-run + confirm), then manifest + deploy
#   .\scripts\Do-NextSteps.ps1 -DeployOnly       # Only deploy scripts/docs to RDP
#   .\scripts\Do-NextSteps.ps1 -DeployOnly -DryRun
param(
    [switch]$RunMerge,
    [switch]$DeployOnly,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ProjectRoot = "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
$BaseDir = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base"

Set-Location $ProjectRoot

# --- Merge (optional) ---
if ($RunMerge) {
    & "$ProjectRoot\scripts\Run-MergeFeb2026.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# --- Update manifest from latest baseline in base (skip if DeployOnly) ---
if (-not $DeployOnly) {
    $latest = Get-ChildItem -Path $BaseDir -Filter "CAD_ESRI_Polished_Baseline_*.xlsx" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latest) {
        Write-Host "`n=== Update manifest ===" -ForegroundColor Cyan
        & python scripts/update_baseline_from_polished.py --source $latest.FullName
        if ($LASTEXITCODE -ne 0) { Write-Warning "Manifest update had issues (exit $LASTEXITCODE)" }
    } else {
        Write-Host "No versioned baseline found in $BaseDir; skipping manifest update." -ForegroundColor Yellow
    }
}

# --- Deploy to RDP ---
Write-Host "`n=== Deploy to RDP ===" -ForegroundColor Cyan
& "$ProjectRoot\Deploy-ToRDP-Simple.ps1" @(if ($DryRun) { "-DryRun" })
exit $LASTEXITCODE
