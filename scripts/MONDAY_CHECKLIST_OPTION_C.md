# Monday Morning Checklist - Option C (Hybrid Strategy)

**Date:** Monday, February 9, 2026  
**Strategy:** Truncate + Staged Backfill (Best of Both Worlds)  
**Time Needed:** 65 minutes  
**Start:** ~9:00 AM | **Finish:** ~10:05 AM

---

## 🎯 What Makes Option C Different

**Why Hybrid is Better:**
- ✅ Fixes root cause (truncate eliminates update matching overhead)
- ✅ Uses your proven staged backfill tooling (15 batches × 50K)
- ✅ Faster than original plan (65 min vs 90 min)
- ✅ No ModelBuilder changes needed today
- ✅ Sets foundation for long-term optimization

---

## â˜'ï¸ PRE-FLIGHT (Before You Start)

- [ ] Read this entire checklist
- [ ] Batches already created from Saturday (15 files + manifest) ✅
- [ ] Batches already copied to `C:\HPD ESRI\03_Data\CAD\Backfill\Batches\` ✅
- [ ] Pre-flight checks passing from Saturday ✅
- [ ] Admin credentials ready for RDP
- [ ] Dashboard URL bookmarked: https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2

---

## â±ï¸ PHASE 0: Get Service URL (5 min)

**NEW STEP - Required for backup/truncate scripts**

```powershell
cd "C:\HPD ESRI\04_Scripts"
C:\PROGRA~1\ArcGIS\Pro\bin\Python\Scripts\propy.bat get_service_url.py
```

**Expected:**
- [ ] Script outputs the actual FeatureServer REST endpoint URL
- [ ] URL saved to `C:\HPD ESRI\04_Scripts\service_url.txt`
- [ ] Copy this URL - you'll paste it into 3 scripts

**Manual Fallback (if script fails):**
1. Open ArcGIS Pro
2. Catalog pane → Portal → My Content
3. Find CFStable layer
4. Right-click → Copy URL
5. Use that URL in scripts

**Paste URL into these scripts:**
- [ ] `backup_current_layer.py` (line 19: SERVICE_URL = "...")
- [ ] `truncate_online_layer.py` (line 19: SERVICE_URL = "...")
- [ ] `restore_from_backup.py` (line 19: SERVICE_URL = "...")

---

## â±ï¸ PHASE 1: Backup Current Layer (10 min)

**CRITICAL - Do not skip this step!**

```powershell
cd "C:\HPD ESRI\04_Scripts"
C:\PROGRA~1\ArcGIS\Pro\bin\Python\Scripts\propy.bat backup_current_layer.py
```

**Expected:**
- [ ] Connection successful to online service
- [ ] Current count: 561,740 records (or close)
- [ ] Geodatabase created: `C:\HPD ESRI\00_Backups\CAD_Backfill_20260209\Backup.gdb`
- [ ] Export completes in 5-10 minutes
- [ ] Backup validated: Count = 561,740
- [ ] Checksum calculated and saved
- [ ] Metadata file created: `backup_metadata.txt`
- [ ] Success message: "✅ BACKUP COMPLETED SUCCESSFULLY"

**If backup fails:**
- Check internet connection
- Verify SERVICE_URL is correct
- Ensure sufficient disk space (need ~500 MB)
- Review log: `C:\HPD ESRI\00_Backups\CAD_Backfill_20260209\backup_log.txt`

---

## â±ï¸ PHASE 2: Truncate Online Layer (2 min)

**DESTRUCTIVE - Ensure backup completed successfully!**

```powershell
cd "C:\HPD ESRI\04_Scripts"
C:\PROGRA~1\ArcGIS\Pro\bin\Python\Scripts\propy.bat truncate_online_layer.py
```

**Expected:**
- [ ] 5 pre-flight checks all pass:
  1. âœ… Backup exists
  2. âœ… Backup count matches (561,740)
  3. âœ… Backup metadata displays
  4. âœ… Online service connection successful
  5. âœ… Truncate permissions available
- [ ] Triple confirmation prompts:
  1. Type: `TRUNCATE`
  2. Type: `[your_username]`
  3. Type: `DELETE ALL RECORDS`
- [ ] Truncation completes in ~30 seconds
- [ ] Verification: Online count = 0 records
- [ ] Truncate record saved
- [ ] Success message: "✅ TRUNCATE COMPLETED SUCCESSFULLY"
- [ ] Next step instructions displayed

**If truncate fails:**
- Check permissions (must be layer owner or org admin)
- Review log: `C:\HPD ESRI\00_Backups\CAD_Backfill_20260209\truncate_log.txt`
- If partial failure, run `restore_from_backup.py` to rollback
- DO NOT PROCEED with backfill if count ≠ 0

---

## â±ï¸ PHASE 3: Staged Backfill (45 min)

**Same as original plan - no changes needed!**

```powershell
cd "C:\HPD ESRI\04_Scripts"
.\Invoke-CADBackfillPublish.ps1 -Staged -BatchFolder "C:\HPD ESRI\03_Data\CAD\Backfill\Batches"
```

**Expected:**
- [ ] Batch 01: "OVERWRITE" mode (but target is empty, so it's INSERT)
- [ ] Batch 02-15: "APPEND" mode (pure INSERT, no matching)
- [ ] Each batch: ~2-3 minutes (FASTER than original estimate!)
- [ ] Cooling period: 60-120s between batches
- [ ] Total time: ~45 minutes (vs 90 min with matching overhead)
- [ ] All 15 batches move to `Completed/` folder
- [ ] Heartbeat.txt updates every 30-60s
- [ ] PowerShell shows "SUCCESS" for all batches

**Monitor During Run:**
- [ ] Check `_STAGING\heartbeat.txt` - Date Modified updates regularly
- [ ] Check `Batches\Completed\` - Batches appear as they finish
- [ ] Watch PowerShell output for errors

**If hang detected (watchdog kills process):**
```powershell
.\Resume-CADBackfill.ps1
```

---

## â±ï¸ PHASE 4: Validate Results (5 min)

```powershell
cd "C:\HPD ESRI\04_Scripts"
C:\PROGRA~1\ArcGIS\Pro\bin\Python\Scripts\propy.bat Validate-CADBackfillCount.py
```

**Expected:**
- [ ] Dashboard: 754,409 records
- [ ] Expected: 754,409 records
- [ ] Difference: 0
- [ ] SUCCESS message

**Dashboard Visual Check:**
- [ ] Open: https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data
- [ ] Total: ~754K (up from 0 after truncate)
- [ ] Date range: 2019-01-01 to 2026-02-03 visible
- [ ] No obvious gaps or anomalies

**How_Reported Domain Check (NEW):**
```python
# In ArcGIS Pro Python window
import arcpy
layer = "YOUR_SERVICE_URL_HERE"
values = set()
with arcpy.da.SearchCursor(layer, ["How_Reported"]) as cursor:
    for row in cursor:
        values.add(row[0])
print("Unique How_Reported values:", sorted(values))
# Should NOT contain "Phone/911" combined value
```

- [ ] No "Phone/911" artifacts present
- [ ] All values are from expected domain (Phone, 9-1-1, Radio, etc.)

---

## â±ï¸ PHASE 5: Generate Report (3 min)

```powershell
cd "C:\HPD ESRI\04_Scripts"
.\Generate-BackfillReport.ps1
```

**Expected:**
- [ ] CSV created in `C:\HPD ESRI\05_Reports\`
- [ ] Contains: batch numbers, timestamps, durations, counts
- [ ] All 15 batches show "SUCCESS"
- [ ] Total records = 754,409

---

## âœ… FINAL VERIFICATION

**Before celebrating, confirm:**
- [ ] All 15 batches in `Completed/` folder
- [ ] Dashboard shows 754,409 records (exactly)
- [ ] Date range: 2019-01-01 to 2026-02-03 (complete)
- [ ] No "Phone/911" combined values in How_Reported field
- [ ] Audit report generated successfully
- [ ] No batches in `Failed/` folder
- [ ] PowerShell final message: "SUCCESS"
- [ ] Backup still intact at: `C:\HPD ESRI\00_Backups\CAD_Backfill_20260209\Backup.gdb\CFStable_PreBackfill_561740`

---

## ðŸš¨ EMERGENCY PROCEDURES

### If Backup Fails (Phase 1)
- Check disk space: Need ~500 MB free
- Verify internet connection stable
- Confirm SERVICE_URL is correct REST endpoint
- Review `backup_log.txt` for specific error
- **DO NOT PROCEED** to truncate without valid backup

### If Truncate Fails (Phase 2)
- Verify you're layer owner or org admin
- Check online layer is not locked by another process
- Review `truncate_log.txt` for error details
- If count ≠ 0 after truncate, DO NOT PROCEED
- Contact support if permissions issue

### If Backfill Fails Partway (Phase 3)
```powershell
# Option 1: Resume from where it stopped
.\Resume-CADBackfill.ps1

# Option 2: Rollback to backup and start over
C:\PROGRA~1\ArcGIS\Pro\bin\Python\Scripts\propy.bat restore_from_backup.py
# Type "ROLLBACK" to confirm
```

### If Record Count Wrong (Phase 4)
```powershell
# Check for duplicates in ArcGIS Pro
# Query: SELECT ReportNumberNew, COUNT(*) FROM CFStable GROUP BY ReportNumberNew HAVING COUNT(*) > 1

# If duplicates or count mismatch, rollback:
C:\PROGRA~1\ArcGIS\Pro\bin\Python\Scripts\propy.bat restore_from_backup.py
```

---

## ðŸ"ž HELP RESOURCES

**Execution Guides:**
- This checklist (Option C specific)
- `MONDAY_MORNING_QUICK_START.md` (original plan, for reference)

**Session Logs:**
- `SESSION_SUMMARY_20260208_BACKFILL_ATTEMPT.md` (Saturday's work)
- `FINAL_SUMMARY_NEXT_STEPS.md` (Saturday's summary)

**Emergency Scripts:**
- Restore backup: `restore_from_backup.py`
- Resume backfill: `Resume-CADBackfill.ps1`
- Validate count: `Validate-CADBackfillCount.py`

**Logs to Review if Issues:**
- Backup: `C:\HPD ESRI\00_Backups\CAD_Backfill_20260209\backup_log.txt`
- Truncate: `C:\HPD ESRI\00_Backups\CAD_Backfill_20260209\truncate_log.txt`
- Restore: `C:\HPD ESRI\00_Backups\CAD_Backfill_20260209\restore_log.txt`
- Backfill: Watch PowerShell output and heartbeat.txt

---

## ðŸŽ‰ POST-SUCCESS TASKS

**1. Update documentation (local machine):**
- [ ] Create `BACKFILL_SUCCESS_REPORT_20260209.md`
- [ ] Update `CLAUDE.md` with v1.5.1 completion metrics
- [ ] Update `CHANGELOG.md` with Option C results

**2. Git commit:**
```bash
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
git add .
git commit -m "feat: successful Option C hybrid backfill (truncate + staged)

- Backup created: 561,740 records
- Truncate successful: 0 records verified
- Staged backfill: 15 batches × 50K records
- Final count: 754,409 records (2019-2026)
- Completion time: XX minutes
- Root cause fixed: No update matching overhead"
git push
```

**3. Archive backups (keep for 1 week minimum):**
```powershell
# DO NOT delete backup until you're 100% confident backfill is correct
# Keep backup for at least 1 week
# After 1 week, compress and archive if desired
```

**4. Plan next week's optimization:**
- Update ModelBuilder to use truncate + append by default
- Standardize ESRI generator column names (underscores)
- Document Option C approach for future backfills

---

## ⏱️ TIMELINE COMPARISON

| Phase | Original Plan | Option C | Improvement |
|-------|---------------|----------|-------------|
| Prep (batches) | 15 min | 0 min | ✅ Already done |
| Get service URL | - | 5 min | New step |
| Backup | - | 10 min | New step |
| Truncate | - | 2 min | New step |
| Execute | 90 min | 45 min | ✅ 50% faster |
| Validate | 5 min | 5 min | Same |
| **TOTAL** | **110 min** | **67 min** | **✅ 39% faster** |

---

## 📊 KEY DIFFERENCES FROM ORIGINAL PLAN

**What Changed:**
1. **NEW:** Phase 0 - Get service URL from dashboard item
2. **NEW:** Phase 1 - Backup current layer (safety net)
3. **NEW:** Phase 2 - Truncate online layer (eliminates matching overhead)
4. **SAME:** Phase 3 - Staged backfill (your proven system)
5. **ENHANCED:** Phase 4 - Added How_Reported domain validation

**Why It's Better:**
- ✅ Fixes root cause (no update matching on 561K existing records)
- ✅ Faster execution (45 min vs 90 min for backfill phase)
- ✅ Emergency rollback available (restore from backup)
- ✅ No ModelBuilder changes needed today
- ✅ Foundation for future optimizations

**What Stayed the Same:**
- Your 15-batch staging system (already tested)
- Watchdog monitoring (already deployed)
- Batch verification (already validated)
- Pre-flight checks (already passing)

---

**ðŸš€ YOU'RE READY! This approach combines the best of both worlds.**

**Start Time:** ___:___ AM  
**Backup Complete:** ___:___ AM  
**Truncate Complete:** ___:___ AM  
**Backfill Complete:** ___:___ AM  
**Validation Complete:** ___:___ AM  
**End Time:** ___:___ AM  
**Success:** â˜ YES â˜ NO (If no, see emergency procedures above)
