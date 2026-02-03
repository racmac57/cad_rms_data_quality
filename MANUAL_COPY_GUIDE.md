# Manual Copy to Server - Quick Guide

## Current Situation
The automated copy script requires admin privileges to access `\\HPD2022LAWSOFT\c$`.

## ✅ OPTION 1: Manual Copy (Easiest)

### Step 1: Copy file locally
1. Open File Explorer
2. Navigate to: `C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base`
3. Copy file: `CAD_ESRI_Polished_Baseline.xlsx` (76.1 MB)

### Step 2: RDP to server
1. Open Remote Desktop Connection
2. Connect to: `HPD2022LAWSOFT`
3. Paste file to: `C:\HPD ESRI\03_Data\CAD\Backfill\`
4. Rename to: `CAD_Consolidated_2019_2026.xlsx`

---

## ✅ OPTION 2: PowerShell with Credentials

Run PowerShell **AS ADMINISTRATOR** on your local machine:

```powershell
# Set credentials (replace with your admin account)
$cred = Get-Credential

# Copy file
$source = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx"
$dest = "\\HPD2022LAWSOFT\c$\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"

# Create network drive temporarily
New-PSDrive -Name "Z" -PSProvider FileSystem -Root "\\HPD2022LAWSOFT\c$" -Credential $cred

# Copy
Copy-Item $source "Z:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" -Force

# Remove drive
Remove-PSDrive -Name "Z"

Write-Host "[OK] File copied successfully!" -ForegroundColor Green
```

---

## ✅ OPTION 3: Use RDP Copy-Paste (Recommended)

This is usually the most reliable:

1. **RDP to HPD2022LAWSOFT** with clipboard enabled
2. **On your local machine**: Copy the baseline file to clipboard (Ctrl+C)
3. **In RDP session**: Navigate to `C:\HPD ESRI\03_Data\CAD\Backfill\`
4. **Paste** (Ctrl+V) - RDP will transfer the file automatically
5. **Rename** to `CAD_Consolidated_2019_2026.xlsx`

---

## 🎯 After File is Copied

Once the file is on the server at:
`C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx`

Run the backfill publish:

```powershell
cd "C:\HPD ESRI\04_Scripts"

# Test mode first
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" `
    -DryRun

# Actual run
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
```

---

## 📋 File Details

- **Source File**: `CAD_ESRI_Polished_Baseline.xlsx`
- **Source Location**: `C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\`
- **Destination**: `C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx` (on HPD2022LAWSOFT)
- **File Size**: 76.1 MB
- **Records**: 754,409
- **Date Range**: 2019-01-01 to 2026-02-03

---

## ⏱️ Estimated Time

- **File copy via RDP**: ~30 seconds (depending on network)
- **Backfill publish (dry run)**: ~2-3 minutes
- **Backfill publish (actual)**: ~10-15 minutes
- **Total**: ~15-20 minutes

---

## ✅ Verification Checklist

Before running backfill publish:
- [ ] File exists at `C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx`
- [ ] File size is ~76 MB
- [ ] File opens successfully in Excel (spot check)
- [ ] Sheet name is "Sheet1" (required by ArcGIS tool)

---

**Recommendation:** Use **Option 3 (RDP Copy-Paste)** - it's the most reliable and doesn't require network share configuration.
