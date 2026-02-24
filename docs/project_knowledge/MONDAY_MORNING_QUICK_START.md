# Monday Morning Quick Start - Staged Backfill Execution

**Date:** Monday, February 9, 2026  
**Time Required:** 90 minutes  
**Status:** ✅ All Prerequisites Complete

---

## 🎯 Your Mission Today

**Upload 754,409 historical CAD records (2019-2026) to ArcGIS dashboard using the staged backfill system.**

**Why Staged?**  
Last night we confirmed that the monolithic 754K upload hangs at ~564K features. The staged system processes 15 batches of 50K records each with automatic hang detection.

---

## ✅ What's Already Done

- ✅ **Corrected baseline file created** (column names fixed: spaces → underscores)
- ✅ **Server scripts deployed** (config.json geodatabase path corrected)
- ✅ **Pre-flight checks operational** (tested last night)
- ✅ **Dashboard verified safe** (561,740 records intact)
- ✅ **Staged backfill system ready** (v1.5.0 with watchdog monitoring)

---

## 📋 Quick Start Checklist

### STEP 1: Create Staged Batches (Local Machine, 15 min)

**Open PowerShell on your local machine:**

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"

# Split corrected baseline into 15 batches
python scripts\split_baseline_into_batches.py

# Verify integrity (SHA256 hashes, record counts)
python scripts\Verify-BatchIntegrity.py
```

**Expected Output:**
```
✅ 15 batch files created: BATCH_01.xlsx through BATCH_15.xlsx
✅ Total records: 754,409
✅ Batch manifest created with SHA256 hashes
✅ Location: 13_PROCESSED_DATA\ESRI_Polished\staged_batches\
```

---

### STEP 2: Copy Batches to Server (RDP, 10 min)

**1. Open File Explorer on local machine:**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\staged_batches\
```

**2. Select all files:**
- `BATCH_01.xlsx` through `BATCH_15.xlsx`
- `batch_manifest.json`
- **Total:** 16 files

**3. Copy files (Ctrl+C)**

**4. On RDP server, create destination:**
```powershell
New-Item -ItemType Directory -Path "C:\HPD ESRI\03_Data\CAD\Backfill\Batches" -Force
```

**5. Navigate to destination and paste (Ctrl+V):**
```
C:\HPD ESRI\03_Data\CAD\Backfill\Batches\
```

**6. Verify all 16 files present:**
```powershell
Get-ChildItem "C:\HPD ESRI\03_Data\CAD\Backfill\Batches" | Measure-Object
# Should show: Count = 16
```

---

### STEP 3: Run Pre-Flight Checks (RDP, 3 min)

**On RDP server:**

```powershell
cd "C:\HPD ESRI\04_Scripts"

# Verify system readiness
.\Test-PublishReadiness.ps1 `
    -ConfigPath "C:\HPD ESRI\04_Scripts\config.json" `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\Batches\BATCH_01.xlsx"
```

**Expected:** All 6 checks pass (same as last night)

**If any fail:**
- Lock file exists: Remove if stale
- Scheduled task running: Wait for completion
- ArcGIS Pro open: Close it

---

### STEP 4A: OPTIONAL - Two-Batch Test Run (RDP, 10 min)

**Recommended for safety - tests workflow before full run:**

```powershell
# Move batches 3-15 to temporary location
New-Item -ItemType Directory -Path "C:\HPD ESRI\03_Data\CAD\Backfill\Queue" -Force

Move-Item "C:\HPD ESRI\03_Data\CAD\Backfill\Batches\BATCH_*.xlsx" `
    -Destination "C:\HPD ESRI\03_Data\CAD\Backfill\Queue\" `
    -Exclude "BATCH_01.xlsx","BATCH_02.xlsx"

# Run staged backfill with only 2 batches
.\Invoke-CADBackfillPublish.ps1 `
    -Staged `
    -BatchFolder "C:\HPD ESRI\03_Data\CAD\Backfill\Batches"
```

**Watch for:**
- Batch 01: "OVERWRITE" mode
- Batch 02: "APPEND" mode
- Both complete in 4-6 minutes
- Heartbeat updates visible in `_STAGING\heartbeat.txt`

**If successful:**
```powershell
# Move remaining batches back
Move-Item "C:\HPD ESRI\03_Data\CAD\Backfill\Queue\BATCH_*.xlsx" `
    -Destination "C:\HPD ESRI\03_Data\CAD\Backfill\Batches\"
```

---

### STEP 4B: Full Staged Backfill (RDP, 45 min)

**Execute all 15 batches:**

```powershell
cd "C:\HPD ESRI\04_Scripts"

# Run full staged backfill
.\Invoke-CADBackfillPublish.ps1 `
    -Staged `
    -BatchFolder "C:\HPD ESRI\03_Data\CAD\Backfill\Batches"
```

**What You'll See:**

```
======================================================================
STAGED BACKFILL - 15 BATCHES
======================================================================

Processing BATCH_01.xlsx (OVERWRITE mode)...
  [OK] Hash verified
  [OK] Swapped to staging
  [OK] Tool completed (50,294 records)
  Cooling period: 60 seconds

Processing BATCH_02.xlsx (APPEND mode)...
  [OK] Hash verified
  [OK] Swapped to staging
  [OK] Tool completed (50,294 records)
  Cooling period: 60 seconds

... (continues for all 15 batches) ...

======================================================================
[SUCCESS] All 15 batches completed!
Total records processed: 754,409
Total duration: 43 minutes
======================================================================
```

**Monitoring During Run:**

1. **Heartbeat Check:**
   - Navigate to `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\`
   - Right-click `heartbeat.txt` → Properties
   - "Date Modified" should update every 30-60 seconds

2. **Progress Check:**
   - Open `C:\HPD ESRI\03_Data\CAD\Backfill\Batches\Completed\`
   - Each completed batch moves here

3. **If Hang Detected:**
   - Watchdog automatically kills process after 5 minutes
   - Batch preserved in `_STAGING` for inspection
   - Run resume script (see troubleshooting below)

---

### STEP 5: Validate Results (RDP, 5 min)

**Check record count:**

```powershell
cd "C:\HPD ESRI\04_Scripts"

# Query ArcGIS Online layer
C:\PROGRA~1\ArcGIS\Pro\bin\Python\Scripts\propy.bat Validate-CADBackfillCount.py
```

**Expected Output:**
```
✅ SUCCESS: Record count matches baseline exactly
   Dashboard: 754,409 records
   Expected:  754,409 records
   Difference: 0
```

**Verify dashboard visually:**
1. Open: https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data
2. Check:
   - Total: ~754K records (up from 561K)
   - Date range: 2019-01-01 to 2026-02-03
   - Last record: Recent (Feb 2026)

---

### STEP 6: Generate Audit Report (RDP, 3 min)

```powershell
.\Generate-BackfillReport.ps1
```

**Creates:** `C:\HPD ESRI\05_Reports\BackfillAudit_YYYYMMDD_HHMMSS.csv`

**Contains:**
- Batch number
- Start/end timestamps
- Duration per batch
- Records processed
- Success/failure status

---

## 🚨 Troubleshooting

### Issue: Batch Hangs (No Heartbeat Update for 5+ Minutes)

**Watchdog will automatically:**
1. Kill the Python process
2. Clean staging files
3. Preserve the problematic batch
4. Stop execution

**Your action:**
```powershell
# Run resume script
.\Resume-CADBackfill.ps1
```

**This will:**
- Clean stale files (`_LOCK.txt`, `heartbeat.txt`)
- Detect remaining batches
- Continue from where it stopped

---

### Issue: Hash Verification Fails

**Error:** `"Hash mismatch for BATCH_XX.xlsx"`

**Fix:**
1. Re-copy that specific batch from local machine
2. Verify file size matches manifest
3. Re-run staged backfill (it will skip completed batches)

---

### Issue: Record Count Doesn't Match

**Dashboard shows more/less than 754,409:**

```powershell
# Check for duplicates
# (Open ArcGIS Pro and query CFStable layer)

# If needed, rollback and restart
propy.bat Rollback-CADBackfill.py
# Type "WIPE" to confirm truncation
```

---

### Issue: "Append" Mode Not Working (Batch 02 Overwrites)

**Symptom:** Batch 02 shows ~50K records instead of ~100K cumulative

**Check:**
1. Verify `is_first_batch.txt` marker exists after Batch 01
   ```powershell
   Test-Path "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\is_first_batch.txt"
   ```

2. If missing, manually create before Batch 02:
   ```powershell
   "Initial batch completed" | Out-File "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\is_first_batch.txt"
   ```

3. Run resume script to continue

---

## ⏱️ Timeline

| Time | Activity | Duration |
|------|----------|----------|
| 9:00 AM | Create batches (local) | 15 min |
| 9:15 AM | Copy to server (RDP) | 10 min |
| 9:25 AM | Pre-flight checks | 3 min |
| 9:28 AM | **OPTIONAL:** Two-batch test | 10 min |
| 9:38 AM | **Full staged backfill** | 45 min |
| 10:23 AM | Validate results | 5 min |
| 10:28 AM | Generate report | 3 min |
| **10:31 AM** | **DONE ✅** | **91 min total** |

---

## ✅ Success Criteria

**When you're done, confirm:**

- ✅ All 15 batches in `Completed/` folder
- ✅ Dashboard shows ~754K records (up from 561K)
- ✅ Date range: 2019-01-01 to 2026-02-03
- ✅ No duplicate ReportNumberNew values
- ✅ Audit report generated
- ✅ No batches in `Failed/` folder
- ✅ Zero watchdog kills (or all resumed successfully)

---

## 📞 Need Help?

**Documentation:**
- Tonight's session: `SESSION_SUMMARY_20260208_BACKFILL_ATTEMPT.md`
- Complete plan: `STAGED_BACKFILL_PLAN_FINAL.md`
- Investigation: `BACKFILL_INVESTIGATION_20260205.md`

**Key Scripts:**
- Resume: `Resume-CADBackfill.ps1`
- Validate: `Validate-CADBackfillCount.py`
- Rollback: `Rollback-CADBackfill.py`
- Analyze: `Analyze-WatchdogHangs.ps1`

---

## 🎉 After Success

**1. Update documentation (local machine):**
```powershell
# Update CLAUDE.md with v1.5.1 release notes
# Create BACKFILL_SUCCESS_REPORT_20260209.md
# Update CHANGELOG.md
```

**2. Git commit:**
```bash
git add .
git commit -m "feat: successful staged backfill of 754K historical records (v1.5.1)

- 15 batches processed successfully
- Total records: 754,409 (2019-2026)
- Watchdog monitoring: 0 hangs detected
- Dashboard verified: date range and record counts correct
- Completion time: XX minutes"

git push
```

**3. Clean up server (optional):**
```powershell
# Archive batches
Move-Item "C:\HPD ESRI\03_Data\CAD\Backfill\Batches\Completed\*" `
    -Destination "C:\HPD ESRI\00_Backups\CAD_Backfill_20260209\"
```

---

**You've got this! The hard work was done last night (fixing column names, setting up scripts). Today is just execution.** 🚀

**Good luck!**
