# PROMPT FOR CURSOR AGENT - Monday Morning, Feb 9, 2026

**Copy and paste this entire message to start your Monday session:**

---

## Context for Agent

Hi! I'm ready to execute the staged CAD backfill today (Monday, February 9, 2026).

**Last Night's Work (Feb 8, 2026):**
- Attempted monolithic backfill of 754K records - failed as expected (hangs at 564K)
- Identified column name mismatch: ESRI generator outputs spaces, ArcGIS model expects underscores
- Created corrected baseline file with proper column names
- Fixed geodatabase path in config.json on server
- Validated all pre-flight checks passing
- Dashboard verified safe: 561,740 records intact

**Files Created:**
- `SESSION_SUMMARY_20260208_BACKFILL_ATTEMPT.md` - Complete 4.5-hour session log
- `MONDAY_MORNING_QUICK_START.md` - Step-by-step execution guide
- `MONDAY_CHECKLIST_PRINT.md` - Quick reference checklist
- `FINAL_SUMMARY_NEXT_STEPS.md` - Comprehensive overview
- `START_HERE_MONDAY.md` - Orientation guide
- `CLAUDE.md` - Updated with v1.5.1 notes

**Corrected Baseline File:**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline_20190101_20260203_CORRECTED.xlsx
```
- Size: 74.36 MB
- Records: 754,409 (2019-01-01 to 2026-02-03)
- Format: Underscores in column names (Time_Of_Call, How_Reported) ✅

**Server Configuration:**
- Scripts deployed: `C:\HPD ESRI\04_Scripts\`
- Geodatabase path corrected in config.json
- Pre-flight checks: All 6 passing
- Staging file restored: 0.22 MB default export

**Today's Mission:**
Execute the staged backfill system (v1.5.0) with 15 batches × 50K records each, using the corrected baseline file.

---

## What I Need Help With Today

Please guide me through executing the staged backfill using the documentation in:
1. `START_HERE_MONDAY.md` (orientation)
2. `MONDAY_MORNING_QUICK_START.md` (detailed guide)
3. `MONDAY_CHECKLIST_PRINT.md` (quick reference)

**Steps I need to complete:**
1. Create 15 batches from corrected baseline (local machine)
2. Copy batches to RDP server
3. Run pre-flight checks
4. Execute staged backfill (45 minutes)
5. Validate results (754,409 records)
6. Generate audit report

**Estimated Time:** 90 minutes total

---

## Key Questions

Before we start, please confirm:
1. Should I read all the documentation first, or just jump to `MONDAY_MORNING_QUICK_START.md`?
2. Do you recommend running the optional two-batch test first, or go straight to full 15-batch execution?
3. Any last-minute checks I should do before starting?

**I'm ready to begin when you are!** 🚀

---

## Quick Commands Reference

**On Local Machine:**
```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
python scripts\split_baseline_into_batches.py
python scripts\Verify-BatchIntegrity.py
```

**On RDP Server:**
```powershell
cd "C:\HPD ESRI\04_Scripts"
.\Test-PublishReadiness.ps1 -ConfigPath ".\config.json" -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\Batches\BATCH_01.xlsx"
.\Invoke-CADBackfillPublish.ps1 -Staged -BatchFolder "C:\HPD ESRI\03_Data\CAD\Backfill\Batches"
```

---

## Emergency Info

**If something goes wrong:**
- Resume after hang: `.\Resume-CADBackfill.ps1`
- Validate count: `propy.bat Validate-CADBackfillCount.py`
- Rollback (nuclear): `propy.bat Rollback-CADBackfill.py`

**Dashboard URL:**
https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data

**Expected Result:**
- Dashboard: 754,409 records (up from 561,740)
- Date range: 2019-01-01 to 2026-02-03
- All 15 batches in Completed/ folder
- Zero hangs (watchdog monitoring active)

---

## Agent Instructions

Please:
1. Read `START_HERE_MONDAY.md` to understand the full context
2. Review `MONDAY_MORNING_QUICK_START.md` for detailed steps
3. Walk me through each step, confirming outputs match expectations
4. Monitor for issues and suggest troubleshooting if needed
5. Help me validate the final result

**Let's get 754K historical records into the dashboard today!** 💪
