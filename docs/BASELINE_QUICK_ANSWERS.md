# QUICK ANSWERS - Baseline Update Questions

**Date:** 2026-02-03  
**Context:** After fixing 2026 monthly data inclusion (v1.3.1)

---

## Your Questions

### Q1: Can we add logic to save updated baseline versions when we append records?

**YES! ✅**

**Script created:** `scripts/update_baseline_from_polished.py`

**Usage:**
```powershell
# After generating polished ESRI output
python scripts/update_baseline_from_polished.py

# Preview what would happen (dry run)
python scripts/update_baseline_from_polished.py --dry-run
```

**What it does:**
1. Finds latest polished Excel from `CAD_Data_Cleaning_Engine/data/03_final/`
2. Extracts metadata (record count, date range)
3. Creates **versioned archive**: `CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx`
4. Updates **generic pointer**: `CAD_ESRI_Polished_Baseline.xlsx`
5. Updates `manifest.json` for programmatic discovery

---

### Q2: Should filename be generic ("CAD_ESRI_Polished_Baseline") or include date range?

**BOTH! ✅**

**Two-file strategy:**

| File Type | Example | Purpose |
|-----------|---------|---------|
| **Generic pointer** | `CAD_ESRI_Polished_Baseline.xlsx` | Scripts always reference this name |
| **Versioned archive** | `CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx` | Historical tracking & rollback |

**Directory structure:**
```
13_PROCESSED_DATA/ESRI_Polished/base/
├── CAD_ESRI_Polished_Baseline.xlsx                      ← Generic (scripts use this)
├── CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx    ← Archived (Jan 31 version)
└── CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx    ← Archived (Feb 3 version)
```

**Why both?**
- Generic = Easy for scripts to reference
- Versioned = Rollback capability + historical tracking
- `manifest.json` = Programmatic discovery of latest

---

### Q3: Issues from last night's chat logs?

**PROBLEM IDENTIFIED:** Incremental mode used wrong baseline and caused data loss

**What happened (2026-02-02 23:XX):**
- Attempted incremental mode
- Expected: 725,463 records (baseline 724,794 + new 669)
- **Actual: 559,651 records** ❌
- Lost 165,812 records!

**Root cause:**
The baseline file (`CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx`) is **already processed/deduplicated**. When incremental mode tried to append new records, it deduplicated **again**, incorrectly treating supplement/unit records as duplicates.

**Solution: Always use `--full` mode**
```powershell
python consolidate_cad_2019_2026.py --full
```

**Why?**
- Only takes 2-3 minutes with parallel loading
- Processes all 12 files (7 yearly + 5 monthly) from scratch
- Ensures consistency across entire dataset
- No risk of deduplication errors

**Config updated:**
- `incremental.enabled: false` (deprecated)
- Added warning note about data loss risk

---

### Q4: Do we manually update dashboard or let task scheduler run?

**HYBRID APPROACH:** Depends on use case

| Scenario | Method | Tool | When |
|----------|--------|------|------|
| **Daily exports** | Automatic | Task scheduler (`LawSoftESRICADExport`) | Every night at 12:30 AM |
| **Historical backfills** | Manual | `Invoke-CADBackfillPublish.ps1` | On-demand when you need to refresh dashboard |
| **Baseline updates** | Semi-automatic | `update_baseline_from_polished.py` | After generating polished output |

**Daily export workflow (automated):**
```
FileMaker export (12:05 AM) 
    → Copy to staging 
    → Run TransformCallData_tbx1 
    → Dashboard updates automatically
```

**Backfill workflow (manual):**
```powershell
# LOCAL: Copy polished to server
.\Copy-PolishedToServer.ps1

# SERVER (via RDP): Run backfill orchestrator
cd "C:\HPD ESRI\04_Scripts"
.\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
```

**Staging pattern:** Model always reads from fixed path (`_STAGING\ESRI_CADExport.xlsx`). Orchestrator swaps file content, publishes, then restores default export.

---

## Recommended Monthly Workflow

When you download new monthly CAD/RMS data (e.g., `2026_02_CAD.xlsx`, `2026_03_CAD.xlsx`):

```powershell
# 1. Consolidate all data (2-3 min)
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
python consolidate_cad_2019_2026.py --full

# 2. Generate polished ESRI output (3-5 min)
cd "../CAD_Data_Cleaning_Engine"
python scripts/enhanced_esri_output_generator.py `
    --input "data/01_raw/2019_to_2026_01_30_CAD.csv" `
    --output-dir "data/03_final" `
    --format excel

# 3. Update baseline (30 sec)
cd "../cad_rms_data_quality"
python scripts/update_baseline_from_polished.py

# 4. (Optional) Deploy to server
# Use Invoke-CADBackfillPublish.ps1 workflow when ready
```

**Total time: ~7-10 minutes**

---

## Key Files Created/Updated

| File | Purpose | Status |
|------|---------|--------|
| `scripts/update_baseline_from_polished.py` | Auto-update baseline from latest polished | ✅ NEW |
| `BASELINE_UPDATE_STRATEGY.md` | Comprehensive guide | ✅ NEW |
| `config/consolidation_sources.yaml` | Updated with generic pointer + deprecation notes | ✅ UPDATED |

---

## Configuration Changes

**Before (v1.3.1):**
```yaml
baseline:
  path: 'C:\...\CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx'
incremental:
  enabled: true
  mode: 'append'
```

**After (current):**
```yaml
baseline:
  path: 'C:\...\CAD_ESRI_Polished_Baseline.xlsx'  # Generic pointer
  versioned_path: 'C:\...\CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx'
  notes: 'WARNING: Incremental mode NOT recommended.'
incremental:
  enabled: false  # DEPRECATED
  mode: 'full'
  deprecation_note: 'Use --full mode instead.'
```

---

## Summary

✅ **Auto-save logic:** YES - `update_baseline_from_polished.py`  
✅ **File naming:** BOTH - Generic pointer + versioned archive  
✅ **Last night's issue:** Incremental mode deprecated, always use `--full`  
✅ **Dashboard updates:** Hybrid - Daily automated, backfills manual

**Recommended approach: Always use `--full` consolidation mode**
- Takes only 2-3 minutes
- Ensures data consistency
- No risk of deduplication errors
- Includes all monthly files from config

---

**See also:**
- `BASELINE_UPDATE_STRATEGY.md` - Full documentation
- `config/consolidation_sources.yaml` - Updated configuration
- `scripts/update_baseline_from_polished.py` - Baseline update script
