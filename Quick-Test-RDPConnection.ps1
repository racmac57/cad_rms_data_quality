# Quick-Test-RDPConnection.ps1
# Run this from your local machine to validate RDP connectivity

Write-Host "`n=== RDP Connection Test ===" -ForegroundColor Cyan

$serverHost = "HPD2022LAWSOFT"
$serverIP = "10.0.0.157"
$testPath = "HPD ESRI\04_Scripts"
$useHost = $null  # Initialize to avoid implicit undefined behavior

# Test 1: Network connectivity (SMB port 445)
Write-Host "`nTest 1: Checking SMB port 445..." -ForegroundColor Yellow

$hostTest = Test-NetConnection -ComputerName $serverHost -Port 445 -WarningAction SilentlyContinue
$ipTest = Test-NetConnection -ComputerName $serverIP -Port 445 -WarningAction SilentlyContinue

if ($hostTest.TcpTestSucceeded) {
    Write-Host "  [OK] Hostname ($serverHost): Port 445 OPEN" -ForegroundColor Green
    $useHost = $serverHost
} else {
    Write-Host "  [X] Hostname ($serverHost): Port 445 BLOCKED/UNREACHABLE" -ForegroundColor Red
}

if ($ipTest.TcpTestSucceeded) {
    Write-Host "  [OK] IP ($serverIP): Port 445 OPEN" -ForegroundColor Green
    if (-not $useHost) { $useHost = $serverIP }
} else {
    Write-Host "  [X] IP ($serverIP): Port 445 BLOCKED/UNREACHABLE" -ForegroundColor Red
}

if (-not $useHost) {
    Write-Host "`nFAILED: Neither hostname nor IP reachable on port 445" -ForegroundColor Red
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "  - Not connected to VPN or LAN" -ForegroundColor Yellow
    Write-Host "  - Windows Firewall blocking SMB" -ForegroundColor Yellow
    Write-Host "  - Server is offline" -ForegroundColor Yellow
    exit 2
}

Write-Host "`nWill use: $useHost" -ForegroundColor Cyan

# Test 2: UNC path accessibility (without credentials first)
Write-Host "`nTest 2: Testing UNC path (no auth yet)..." -ForegroundColor Yellow

$uncPath = "\\$useHost\C$"
if (Test-Path $uncPath -ErrorAction SilentlyContinue) {
    Write-Host "  [OK] UNC path accessible: $uncPath" -ForegroundColor Green
    $needsCreds = $false
} else {
    Write-Host "  [!] UNC path requires authentication: $uncPath" -ForegroundColor Yellow
    $needsCreds = $true
}

# Test 3: Credential authentication (if needed)
if ($needsCreds) {
    Write-Host "`nTest 3: Prompting for credentials..." -ForegroundColor Yellow
    $cred = Get-Credential -Message "Enter RDP admin credentials (domain\username)"
    
    if (-not $cred) {
        Write-Host "  [X] No credentials provided" -ForegroundColor Red
        exit 3
    }
    
    Write-Host "  Attempting to map network drive..." -ForegroundColor Yellow
    
    try {
        $driveLetter = "Z"
        # Remove if already exists
        if (Test-Path "${driveLetter}:") {
            Remove-PSDrive -Name $driveLetter -Force -ErrorAction SilentlyContinue
        }
        
        New-PSDrive -Name $driveLetter -PSProvider FileSystem -Root $uncPath -Credential $cred -ErrorAction Stop | Out-Null
        Write-Host "  [OK] Authentication successful! Mapped to ${driveLetter}:" -ForegroundColor Green
        
        # Test 4: Check if target directory exists
        Write-Host "`nTest 4: Checking target directory..." -ForegroundColor Yellow
        $targetPath = "${driveLetter}:\$testPath"
        
        if (Test-Path $targetPath) {
            Write-Host "  [OK] Target directory exists: $targetPath" -ForegroundColor Green
            
            # List some files
            $files = Get-ChildItem $targetPath -File | Select-Object -First 5
            Write-Host "`n  Found files:" -ForegroundColor Cyan
            $files | ForEach-Object { Write-Host "    - $($_.Name)" -ForegroundColor Gray }
            
        } else {
            Write-Host "  [X] Target directory NOT found: $targetPath" -ForegroundColor Red
            Write-Host "    Expected: ${driveLetter}:\HPD ESRI\04_Scripts" -ForegroundColor Yellow
        }
        
        # Test 5: Write permission test
        Write-Host "`nTest 5: Testing write permissions..." -ForegroundColor Yellow
        $testFile = "${driveLetter}:\HPD ESRI\04_Scripts\_out\connection_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
        
        try {
            "Connection test from $env:COMPUTERNAME at $(Get-Date)" | Out-File -FilePath $testFile -ErrorAction Stop
            Write-Host "  [OK] Write permission OK" -ForegroundColor Green
            Write-Host "    Test file created: $testFile" -ForegroundColor Gray
            
            # Clean up test file
            Remove-Item $testFile -ErrorAction SilentlyContinue
            
        } catch {
            Write-Host "  [X] Write permission DENIED" -ForegroundColor Red
            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        # Cleanup
        Remove-PSDrive -Name $driveLetter -Force
        Write-Host "`nCleaned up mapped drive" -ForegroundColor Gray
        
    } catch {
        Write-Host "  [X] Authentication FAILED" -ForegroundColor Red
        Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "`nPossible causes:" -ForegroundColor Yellow
        Write-Host "  - Wrong username/password" -ForegroundColor Yellow
        Write-Host "  - Account doesn't have admin rights" -ForegroundColor Yellow
        Write-Host "  - Need domain prefix (HACKENSACK\username)" -ForegroundColor Yellow
        exit 3
    }
} else {
    Write-Host "`nSKIPPED Tests 3-5: Already authenticated with current credentials" -ForegroundColor Cyan
}

Write-Host "`n=== ALL TESTS PASSED ===" -ForegroundColor Green
Write-Host "You can proceed with deployment using: $useHost" -ForegroundColor Cyan
