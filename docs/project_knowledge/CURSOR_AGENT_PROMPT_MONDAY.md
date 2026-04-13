# Cursor Agent Prompt - Monday Morning

**Copy and paste this entire prompt to Cursor agent when you start work Monday morning:**

---

## 📋 Morning Briefing for Cursor Agent

Good morning! I'm ready to execute the staged backfill of 754,409 historical CAD records (2019-2026) to the ArcGIS dashboard.

### Context from Last Night (Feb 8, 2026):

**What We Accomplished:**
- ✅ Identified column name mismatch issue (spaces vs underscores)
- ✅ Created corrected baseline file with proper column names
- ✅ Fixed geodatabase path in server config.json
- ✅ Deployed all staged backfill scripts (v1.5.0) to RDP server
- ✅ Validated pre-flight checks (all 6 passing)
- ✅ Confirmed dashboard safe (561,740 records intact)

**Why Monolithic Failed:**
- Attempted 754K record upload twice
- Both hangs at ~564K features during geocoding phase
- Root cause: Network session exhaustion (confirmed from prior investigation)
- Solution: Use 15-batch staged approach with watchdog monitoring

**Files Ready for Use:**
- Corrected baseline: `13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline_20190101_20260203_CORRECTED.xlsx` (74.36 MB)
- Server scripts: Deployed to `C:\HPD ESRI\04_Scripts\` on RDP server
- Documentation: 7 comprehensive guides created

### My Objective Today:

Execute the staged backfill using 15 batches × 50K records with automatic hang detection and recovery.

### Files You Should Read:

**Priority 1 - Start Here:**
1. `START_HERE_MONDAY.md` - Quick orientation
2. `MONDAY_CHECKLIST_PRINT.md` - Step-by-step checklist

**Priority 2 - If I Need Help:**
3. `MONDAY_MORNING_QUICK_START.md` - Complete detailed guide
4. `FINAL_SUMMARY_NEXT_STEPS.md` - Full context from last night

**Reference Only:**
5. `SESSION_SUMMARY_20260208_BACKFILL_ATTEMPT.md` - Complete session log (4.5 hours)

### Current Status:

**Local Machine:**
- Corrected baseline file exists and verified
- Need to create 15 batches from this file

**RDP Server:**
- Scripts deployed and tested
- Config corrected (geodatabase path)
- Pre-flight checks passing
- Ready for batch execution

### What I Need Help With:

Please guide me through the Monday morning execution:

1. **Creating batches** (local machine, 15 min)
   - Split corrected baseline into 15 batches
   - Verify integrity with SHA256 hashes

2. **Copying to server** (RDP, 10 min)
   - Manual copy via RDP clipboard (PowerShell Copy-Item doesn't work reliably for me)

3. **Running pre-flight checks** (RDP, 3 min)
   - Verify all 6 checks pass

4. **Executing staged backfill** (RDP, 45 min)
   - Run orchestrator with 15 batches
   - Monitor heartbeat file
   - Watch for watchdog auto-recovery if needed

5. **Validating results** (RDP, 5 min)
   - Confirm 754,409 records in dashboard
   - Generate audit report

### Questions Before We Start:

1. Should I run the optional two-batch test first (adds 10 min but validates workflow)?
2. Do I need to create a geocoding cache, or will the batches use live geocoding?
3. Any other pre-checks I should run before starting?

### Key Success Criteria:

- Dashboard shows 754,409 total records (up from 561,740)
- Date range: 2019-01-01 to 2026-02-03
- All 15 batches in Completed/ folder
- Zero duplicates (unique ReportNumberNew count)
- Audit report generated

### My Availability:

I have a **90-minute window** this morning to complete this. If we run into issues, I have access to:
- Emergency resume script (after watchdog kill)
- Rollback script (nuclear option)
- Validation and analysis tools

**Let's do this! What's the first command I should run?** 🚀

---

## 🎯 Quick Reference (For Cursor Agent)

**Key File Locations:**
- Corrected baseline: `C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline_20190101_20260203_CORRECTED.xlsx`
- Project root: `C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality`
- RDP scripts: `C:\HPD ESRI\04_Scripts\`

**RDP Connection:**
- Server: `HPD2022LAWSOFT` or `10.0.0.157`
- User: Administrator credentials

**Dashboard:**
- URL: https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data
- Current: 561,740 records
- Target: 754,409 records

**Staged Backfill Scripts (v1.5.0):**
- `split_baseline_into_batches.py` - Create 15 batches
- `Verify-BatchIntegrity.py` - SHA256 verification
- `Invoke-CADBackfillPublish.ps1` - Main orchestrator
- `Test-PublishReadiness.ps1` - Pre-flight checks
- `Validate-CADBackfillCount.py` - Record count verification
- `Resume-CADBackfill.ps1` - Recovery after watchdog kill
- `Generate-BackfillReport.ps1` - Audit report

---

**END OF PROMPT - Ready to execute when Cursor agent responds!**
