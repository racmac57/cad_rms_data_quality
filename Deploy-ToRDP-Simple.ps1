# Deploy-ToRDP-Simple.ps1
# Purpose: Deploy updated scripts and docs from local repo to RDP server
# Uses File Explorer's cached credentials (no Get-Credential needed)
# Author: R. A. Carucci
# Date: 2026-02-15

param(
    [switch]$DryRun,
    [switch]$NoBackup,
    [string]$RepoRoot = "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
)

Write-Host "`n=== Deploy to RDP Server ===" -ForegroundColor Cyan
Write-Host "Mode: $(if ($DryRun) {'DRY-RUN (no changes)'} else {'LIVE deployment'})" -ForegroundColor $(if ($DryRun) {'Yellow'} else {'Green'})

# Target paths
$rdpScripts = "\\HPD2022LAWSOFT\C$\HPD ESRI\04_Scripts"
$rdpDocs = "\\HPD2022LAWSOFT\C$\HPD ESRI"
$backupRoot = "\\HPD2022LAWSOFT\C$\HPD ESRI\00_Backups"
$logDir = "$RepoRoot\deploy_logs"
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$logFile = "$logDir\Deploy_$timestamp.log"

# Create log directory
if (-not (Test-Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory -Force | Out-Null
}

Function Write-Log {
    Param([string]$Message)
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMsg = "$stamp : $Message"
    Write-Host $logMsg
    $logMsg | Out-File -FilePath $logFile -Append
}

# Pre-flight checks
Write-Host "`nPre-flight checks..." -ForegroundColor Yellow

if (-not (Test-Path $rdpScripts)) {
    Write-Log "ERROR: Cannot access RDP scripts directory: $rdpScripts"
    Write-Log "Action: Open File Explorer and browse to \\HPD2022LAWSOFT\C$ to authenticate first"
    exit 2
}
Write-Log "[OK] RDP scripts directory accessible"

if (-not (Test-Path $rdpDocs)) {
    Write-Log "ERROR: Cannot access RDP docs directory: $rdpDocs"
    exit 2
}
Write-Log "[OK] RDP docs directory accessible"

# Create backup (unless skipped)
if (-not $NoBackup -and -not $DryRun) {
    Write-Host "`nCreating backup..." -ForegroundColor Yellow
    $backupFolder = "$backupRoot\ScriptsDeploy_$timestamp"
    
    try {
        New-Item -Path $backupFolder -ItemType Directory -Force | Out-Null
        
        # Backup existing scripts
        Get-ChildItem $rdpScripts -Include *.py,*.ps1,*.json -File | ForEach-Object {
            Copy-Item $_.FullName $backupFolder -Force
            Write-Log "  Backed up: $($_.Name)"
        }
        
        # Backup existing docs
        @("SUMMARY.md", "README.md", "CHANGELOG.md") | ForEach-Object {
            $docPath = Join-Path $rdpDocs $_
            if (Test-Path $docPath) {
                Copy-Item $docPath $backupFolder -Force
                Write-Log "  Backed up: $_"
            }
        }
        
        Write-Log "[OK] Backup complete: $backupFolder"
    } catch {
        Write-Log "ERROR: Backup failed: $($_.Exception.Message)"
        exit 4
    }
} elseif ($NoBackup) {
    Write-Log "[SKIPPED] Backup disabled with -NoBackup switch"
} else {
    Write-Log "[DRY-RUN] Would create backup at: $backupRoot\ScriptsDeploy_$timestamp"
}

# Deploy scripts
Write-Host "`nDeploying scripts..." -ForegroundColor Yellow

$scriptFiles = Get-ChildItem "$RepoRoot\scripts" -Include *.py,*.ps1,*.json -File -Recurse

if ($DryRun) {
    Write-Log "[DRY-RUN] Would deploy $($scriptFiles.Count) files to: $rdpScripts"
    $scriptFiles | ForEach-Object { Write-Log "  - $($_.Name)" }
} else {
    $copyCount = 0
    $scriptFiles | ForEach-Object {
        try {
            Copy-Item $_.FullName $rdpScripts -Force
            Write-Log "  Deployed: $($_.Name)"
            $copyCount++
        } catch {
            Write-Log "  ERROR copying $($_.Name): $($_.Exception.Message)"
        }
    }
    Write-Log "[OK] Deployed $copyCount scripts to: $rdpScripts"
}

# Deploy documentation
Write-Host "`nDeploying documentation..." -ForegroundColor Yellow

$docFiles = @("SUMMARY.md", "README.md", "CHANGELOG.md")

if ($DryRun) {
    Write-Log "[DRY-RUN] Would deploy docs to: $rdpDocs"
    $docFiles | ForEach-Object { Write-Log "  - $_" }
} else {
    $docCount = 0
    $docFiles | ForEach-Object {
        $sourcePath = Join-Path $RepoRoot $_
        $targetPath = Join-Path $rdpDocs $_
        
        if (Test-Path $sourcePath) {
            try {
                Copy-Item $sourcePath $targetPath -Force
                Write-Log "  Deployed: $_"
                $docCount++
            } catch {
                Write-Log "  ERROR copying ${_}: $($_.Exception.Message)"
            }
        } else {
            Write-Log "  WARNING: Source file not found: $sourcePath"
        }
    }
    Write-Log "[OK] Deployed $docCount docs to: $rdpDocs"
}

# Summary
Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Log "Deployment finished at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Log "Log file: $logFile"

if (-not $DryRun) {
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Review log: $logFile"
    Write-Host "  2. Verify on RDP: Check C:\HPD ESRI\04_Scripts\ for updated files"
    Write-Host "  3. Test: Run monitor_dashboard_health.py on RDP"
}
