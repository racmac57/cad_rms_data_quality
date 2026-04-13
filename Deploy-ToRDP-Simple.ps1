# Deploy-ToRDP-Simple.ps1
# Purpose: Deploy updated scripts and docs from local repo to RDP server
# Tries cached access first; on Access Denied prompts for credentials and maps drive
# Author: R. A. Carucci
# Date: 2026-02-15

param(
    [switch]$DryRun,
    [switch]$NoBackup,
    [switch]$PromptForCreds = $false,
    [switch]$OpenExplorer,
    [string]$ServerHost = "HPD2022LAWSOFT",
    [string]$ServerIP = "10.0.0.157",
    [string]$RepoRoot = "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
)

$ErrorActionPreference = "Stop"
$script:UseDrive = $false   # true when we mapped RDP: with credentials
$script:ResolvedRoot = $null

Write-Host "`n=== Deploy to RDP Server ===" -ForegroundColor Cyan
Write-Host "Mode: $(if ($DryRun) {'DRY-RUN (no changes)'} else {'LIVE deployment'})" -ForegroundColor $(if ($DryRun) {'Yellow'} else {'Green'})

$logDir = "$RepoRoot\deploy_logs"
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$logFile = "$logDir\Deploy_$timestamp.log"
if (-not (Test-Path $logDir)) { New-Item -Path $logDir -ItemType Directory -Force | Out-Null }

Function Write-Log {
    Param([string]$Message)
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMsg = "$stamp : $Message"
    Write-Host $logMsg
    $logMsg | Out-File -FilePath $logFile -Append
}

# ---------- 1) Detect existing SMB connections (warn about conflicts) ----------
Write-Host "`nPre-flight: Checking for existing SMB connections..." -ForegroundColor Yellow
$netUse = net use 2>$null
$conflict = $netUse | Select-String -Pattern "\\\\$ServerHost\\|\\\\$ServerIP\\" -AllMatches
if ($conflict) {
    Write-Log "WARNING: Existing connection(s) to server may cause 'Access is denied' without prompting:"
    $conflict | ForEach-Object { Write-Log "  $($_.Line.Trim())" }
    Write-Log "To remove and retry: net use \\$ServerHost\C$ /delete"
    Write-Log "Or: net use \\$ServerIP\C$ /delete"
}

# ---------- 2) Try hostname then IP (quiet Test-Path) ----------
$uncHost = "\\$ServerHost\C$"
$uncIP = "\\$ServerIP\C$"
$scriptsPathHost = "$uncHost\HPD ESRI\04_Scripts"
$scriptsPathIP = "$uncIP\HPD ESRI\04_Scripts"

# If user only wants to open Explorer to sign in, do that and exit
if ($OpenExplorer) {
    Write-Host "`nOpening File Explorer to server share..." -ForegroundColor Cyan
    Start-Process "explorer.exe" -ArgumentList $uncHost
    Write-Log "Opened: $uncHost"
    Write-Host "  Sign in in the Explorer window if prompted." -ForegroundColor Yellow
    Write-Host "  Then run deploy again:  .\Deploy-ToRDP-Simple.ps1" -ForegroundColor Green
    exit 0
}

$okHost = Test-Path $scriptsPathHost -ErrorAction SilentlyContinue
$okIP = $false
if (-not $okHost) {
    $okIP = Test-Path $scriptsPathIP -ErrorAction SilentlyContinue
}

if ($okHost) {
    $script:ResolvedRoot = $uncHost
    Write-Log "[OK] RDP scripts directory accessible (hostname): $scriptsPathHost"
} elseif ($okIP) {
    $script:ResolvedRoot = $uncIP
    Write-Log "[OK] RDP scripts directory accessible (IP): $scriptsPathIP"
} else {
    # ---------- 3a) Retry: net use (no password) to attach cached Explorer credential to this session ----------
    Write-Log "Cannot access RDP scripts directory. Trying net use with cached credentials..."
    $netUseOk = $false
    foreach ($root in @($uncHost, $uncIP)) {
        $result = net use $root 2>&1
        if ($LASTEXITCODE -eq 0) {
            $netUseOk = $true
            Write-Log "[OK] net use $root succeeded (cached credential attached)"
            break
        }
    }
    if ($netUseOk) {
        $okHost = Test-Path $scriptsPathHost -ErrorAction SilentlyContinue
        if (-not $okHost) { $okIP = Test-Path $scriptsPathIP -ErrorAction SilentlyContinue }
        if ($okHost) {
            $script:ResolvedRoot = $uncHost
            Write-Log "[OK] RDP scripts directory accessible (hostname): $scriptsPathHost"
        } elseif ($okIP) {
            $script:ResolvedRoot = $uncIP
            Write-Log "[OK] RDP scripts directory accessible (IP): $scriptsPathIP"
        }
    }
}

if (-not $script:ResolvedRoot) {
    # ---------- 3b) Still no access — show manual options ----------
    Write-Log "ERROR: Cannot access RDP scripts directory (hostname or IP)."
    Write-Log "  Tried: $scriptsPathHost"
    Write-Log "  Tried: $scriptsPathIP"

    Write-Host ""
    Write-Host "PowerShell may not see the credential you used in Explorer." -ForegroundColor Yellow
    Write-Host "Option A - Run deploy from the share (same window as sign-in):" -ForegroundColor Cyan
    Write-Host "  1. In the Explorer window for \\HPD2022LAWSOFT\C$, click the address bar." -ForegroundColor White
    Write-Host "  2. Type:  cmd  and press Enter (opens Command Prompt in that share)." -ForegroundColor White
    Write-Host "  3. Run:  cd /d `"$RepoRoot`"  then  powershell -NoProfile -ExecutionPolicy Bypass -File .\Deploy-ToRDP-Simple.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Option B - Manual copy: drag the contents of  scripts\  to  \\HPD2022LAWSOFT\C$\HPD ESRI\04_Scripts\  in Explorer." -ForegroundColor Cyan
    Write-Host ""

    if (-not $PromptForCreds) {
        Write-Log "Action: Use Option A or B above, or run with -PromptForCreds to try credential prompt."
        exit 2
    }

    Write-Host "Prompting for credentials (you requested -PromptForCreds)..." -ForegroundColor Yellow
    $cred = Get-Credential -Message "Enter RDP admin credentials (e.g. HACKENSACK\administrator)"
    if (-not $cred) {
        Write-Log "ERROR: No credentials provided."
        exit 3
    }

    # Remove existing RDP drive if present
    if (Get-PSDrive -Name RDP -ErrorAction SilentlyContinue) {
        Remove-PSDrive -Name RDP -Force -ErrorAction SilentlyContinue
    }

    $mapped = $false
    foreach ($root in @($uncHost, $uncIP)) {
        try {
            New-PSDrive -Name RDP -PSProvider FileSystem -Root $root -Credential $cred -ErrorAction Stop | Out-Null
            $script:ResolvedRoot = $root
            $script:UseDrive = $true
            $mapped = $true
            Write-Log "[OK] Mapped RDP: to $root"
            break
        } catch {
            Write-Log "  Failed with $root : $($_.Exception.Message)"
        }
    }

    if (-not $mapped) {
        Write-Log "ERROR: Could not map drive with provided credentials. Try -OpenExplorer workflow above."
        exit 3
    }

    # Verify scripts path exists on mapped drive
    if (-not (Test-Path "RDP:\HPD ESRI\04_Scripts" -ErrorAction SilentlyContinue)) {
        Write-Log "ERROR: Path RDP:\HPD ESRI\04_Scripts not found after mapping."
        Remove-PSDrive -Name RDP -Force -ErrorAction SilentlyContinue
        exit 2
    }
}

# ---------- 4) Set paths (UNC or RDP:) ----------
if ($script:UseDrive) {
    $rdpScripts = "RDP:\HPD ESRI\04_Scripts"
    $rdpDocs = "RDP:\HPD ESRI"
    $backupRoot = "RDP:\HPD ESRI\00_Backups"
} else {
    $rdpScripts = "$script:ResolvedRoot\HPD ESRI\04_Scripts"
    $rdpDocs = "$script:ResolvedRoot\HPD ESRI"
    $backupRoot = "$script:ResolvedRoot\HPD ESRI\00_Backups"
}

# Second path check for docs
if (-not (Test-Path $rdpDocs -ErrorAction SilentlyContinue)) {
    Write-Log "ERROR: Cannot access RDP docs directory: $rdpDocs"
    if ($script:UseDrive) { Remove-PSDrive -Name RDP -Force -ErrorAction SilentlyContinue }
    exit 2
}
Write-Log "[OK] RDP docs directory accessible"

try {
    # ---------- 5) Create backup (unless skipped) ----------
    if (-not $NoBackup -and -not $DryRun) {
        Write-Host "`nCreating backup..." -ForegroundColor Yellow
        $backupFolder = "$backupRoot\ScriptsDeploy_$timestamp"
        try {
            New-Item -Path $backupFolder -ItemType Directory -Force | Out-Null
            Get-ChildItem $rdpScripts -Include *.py,*.ps1,*.json -File -ErrorAction SilentlyContinue | ForEach-Object {
                Copy-Item $_.FullName $backupFolder -Force
                Write-Log "  Backed up: $($_.Name)"
            }
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
            throw
        }
    } elseif ($NoBackup) {
        Write-Log "[SKIPPED] Backup disabled with -NoBackup switch"
    } else {
        Write-Log "[DRY-RUN] Would create backup at: $backupRoot\ScriptsDeploy_$timestamp"
    }

    # ---------- 6) Deploy scripts ----------
    Write-Host "`nDeploying scripts..." -ForegroundColor Yellow
    $scriptFiles = Get-ChildItem "$RepoRoot\scripts" -Include *.py,*.ps1,*.json -File -Recurse -ErrorAction SilentlyContinue
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

    # ---------- 7) Deploy documentation ----------
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

    Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
    Write-Log "Deployment finished at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Log "Log file: $logFile"
    if (-not $DryRun) {
        Write-Host "`nNext steps:" -ForegroundColor Cyan
        Write-Host "  1. Review log: $logFile"
        Write-Host "  2. Verify on RDP: Check C:\HPD ESRI\04_Scripts\ for updated files"
        Write-Host "  3. Test: Run monitor_dashboard_health.py on RDP"
    }
} finally {
    if ($script:UseDrive) {
        Remove-PSDrive -Name RDP -Force -ErrorAction SilentlyContinue
        Write-Log "Cleaned up mapped drive RDP:"
    }
}
