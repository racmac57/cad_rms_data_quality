# Monday Morning Checklist - Print This!

**Date:** Monday, February 9, 2026  
**Time Needed:** 90 minutes  
**Start:** ~9:00 AM | **Finish:** ~10:30 AM

---

## ☑️ Before You Start

- [ ] Read `MONDAY_MORNING_QUICK_START.md` (complete guide)
- [ ] Have admin credentials for RDP ready
- [ ] Verify OneDrive synced on local machine

---

## 📋 Execution Steps

### ⏱️ STEP 1: Create Batches (Local, 15 min)

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
python scripts\split_baseline_into_batches.py
python scripts\Verify-BatchIntegrity.py
```

**Expected:**
- [ ] 15 files created: BATCH_01.xlsx through BATCH_15.xlsx
- [ ] 1 manifest: batch_manifest.json
- [ ] Total records: 754,409
- [ ] All SHA256 hashes generated

**Location:** `13_PROCESSED_DATA\ESRI_Polished\staged_batches\`

---

### ⏱️ STEP 2: Copy to Server (RDP, 10 min)

**1. On local machine:**
- [ ] Open `13_PROCESSED_DATA\ESRI_Polished\staged_batches\`
- [ ] Select all 16 files (15 batches + manifest)
- [ ] Copy (Ctrl+C)

**2. On RDP server:**
```powershell
New-Item -ItemType Directory -Path "C:\HPD ESRI\03_Data\CAD\Backfill\Batches" -Force
```
- [ ] Navigate to `C:\HPD ESRI\03_Data\CAD\Backfill\Batches\`
- [ ] Paste (Ctrl+V)
- [ ] Verify 16 files present

---

### ⏱️ STEP 3: Pre-Flight Checks (RDP, 3 min)

```powershell
cd "C:\HPD ESRI\04_Scripts"
.\Test-PublishReadiness.ps1 -ConfigPath "C:\HPD ESRI\04_Scripts\config.json" -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\Batches\BATCH_01.xlsx"
```

**Expected:**
- [ ] ✅ Lock file check: PASS
- [ ] ✅ Scheduled task check: PASS
- [ ] ✅ ArcGIS process check: PASS
- [ ] ✅ Geodatabase lock: PASS
- [ ] ✅ Excel sheet check: PASS
- [ ] ✅ Disk space: PASS

---

### ⏱️ STEP 4 (OPTIONAL): Two-Batch Test (RDP, 10 min)

**Only if you want extra safety:**

```powershell
# Move batches 3-15 to temp location
New-Item -ItemType Directory -Path "C:\HPD ESRI\03_Data\CAD\Backfill\Queue" -Force
Move-Item "C:\HPD ESRI\03_Data\CAD\Backfill\Batches\BATCH_*.xlsx" -Destination "C:\HPD ESRI\03_Data\CAD\Backfill\Queue\" -Exclude "BATCH_01.xlsx","BATCH_02.xlsx"

# Run with 2 batches
.\Invoke-CADBackfillPublish.ps1 -Staged -BatchFolder "C:\HPD ESRI\03_Data\CAD\Backfill\Batches"
```

**Expected:**
- [ ] Batch 01: "OVERWRITE" mode
- [ ] Batch 02: "APPEND" mode
- [ ] Both complete in 4-6 minutes
- [ ] Heartbeat.txt updates visible

**If successful:**
```powershell
Move-Item "C:\HPD ESRI\03_Data\CAD\Backfill\Queue\BATCH_*.xlsx" -Destination "C:\HPD ESRI\03_Data\CAD\Backfill\Batches\"
```

---

### ⏱️ STEP 5: Full Backfill (RDP, 45 min)

```powershell
.\Invoke-CADBackfillPublish.ps1 -Staged -BatchFolder "C:\HPD ESRI\03_Data\CAD\Backfill\Batches"
```

**Monitor During Run:**
- [ ] Check `_STAGING\heartbeat.txt` - Date Modified updates every 30-60s
- [ ] Check `Batches\Completed\` - Batches move here when done
- [ ] Watch PowerShell output for progress

**Expected:**
- [ ] Each batch: 2-3 minutes
- [ ] 15 batches total
- [ ] Cooling period: 60-120s between batches
- [ ] Total time: ~45 minutes

---

### ⏱️ STEP 6: Validate (RDP, 5 min)

```powershell
C:\PROGRA~1\ArcGIS\Pro\bin\Python\Scripts\propy.bat Validate-CADBackfillCount.py
```

**Expected:**
- [ ] Dashboard: 754,409 records
- [ ] Expected: 754,409 records
- [ ] Difference: 0
- [ ] SUCCESS message

**Dashboard Visual Check:**
- [ ] Open: https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data
- [ ] Total: ~754K (up from 561K)
- [ ] Date range: 2019-01-01 to 2026-02-03

---

### ⏱️ STEP 7: Generate Report (RDP, 3 min)

```powershell
.\Generate-BackfillReport.ps1
```

**Expected:**
- [ ] CSV created in `C:\HPD ESRI\05_Reports\`
- [ ] Contains: batch numbers, timestamps, durations, counts
- [ ] All 15 batches show "SUCCESS"

---

## ✅ Final Checklist

**Verify before celebrating:**
- [ ] All 15 batches in `Completed/` folder
- [ ] Dashboard shows 754,409 records
- [ ] Date range: 2019-01-01 to 2026-02-03
- [ ] Audit report generated
- [ ] No batches in `Failed/` folder
- [ ] PowerShell shows "SUCCESS"

---

## 🚨 If Something Goes Wrong

### Hang Detected (No heartbeat for 5+ min)
```powershell
# Watchdog will auto-kill, then run:
.\Resume-CADBackfill.ps1
```

### Record Count Wrong
```powershell
# Check for duplicates in ArcGIS Pro
# If needed, rollback:
propy.bat Rollback-CADBackfill.py
# Type "WIPE" to confirm
```

### Hash Mismatch
- Re-copy specific batch from local machine
- Re-run staged backfill (skips completed batches)

---

## 📞 Help Resources

**Step-by-Step Guide:**
- `MONDAY_MORNING_QUICK_START.md`

**Full Session Log:**
- `SESSION_SUMMARY_20260208_BACKFILL_ATTEMPT.md`

**Complete Plan:**
- `STAGED_BACKFILL_PLAN_FINAL.md`

**Emergency Scripts:**
- Resume: `Resume-CADBackfill.ps1`
- Validate: `Validate-CADBackfillCount.py`
- Rollback: `Rollback-CADBackfill.py`

---

## 🎉 After Success

**1. Update docs (local machine):**
- [ ] Create `BACKFILL_SUCCESS_REPORT_20260209.md`
- [ ] Update `CLAUDE.md` with completion metrics
- [ ] Update `CHANGELOG.md` with v1.5.1

**2. Git commit:**
```bash
git add .
git commit -m "feat: successful staged backfill of 754K historical records (v1.5.1)"
git push
```

**3. Clean up server:**
```powershell
# Archive batches and reports
Move-Item "C:\HPD ESRI\03_Data\CAD\Backfill\Batches\Completed\*" -Destination "C:\HPD ESRI\00_Backups\CAD_Backfill_20260209\"
```

---

**🚀 YOU'VE GOT THIS! The hard work was done last night. Today is just execution.**

**Start Time:** ___:___ AM  
**End Time:** ___:___ AM  
**Success:** ☐ YES ☐ NO (If no, see help resources above)
