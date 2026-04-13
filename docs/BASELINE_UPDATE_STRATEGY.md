# Baseline Update Strategy

**Created:** 2026-02-03  
**Author:** R. A. Carucci  
**Status:** Production Strategy

---

## Overview

This document answers your questions about baseline file management and provides a comprehensive strategy for keeping the baseline current with monthly updates.

---

## Questions & Answers

### Q1: Can we add logic to auto-save updated baseline versions?

**Answer: YES** - But we need to clarify which baseline we're updating.

### Q2: Should the filename be generic or include date range?

**Answer: BOTH** - Use a "latest pointer" pattern:
- **Generic name**: `CAD_ESRI_Polished_Baseline.xlsx` (easy for scripts)
- **Versioned archive**: `CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx` (tracking/rollback)
- **Manifest.json**: Programmatic discovery

### Q3: Do we manually update the dashboard or use the task scheduler?

**Answer: HYBRID APPROACH**
- **For backfills**: Manual (using `Invoke-CADBackfillPublish.ps1`)
- **For daily updates**: Automatic (task scheduler)
- **Baseline updates**: Semi-automatic (run script after polished generation)

---

## The Two Baseline Files (Critical Understanding)

From last night's chat logs, we discovered there are **two types of baseline files** that serve different purposes:

### 1. Raw Consolidated CSV (Input for ESRI Generator)

```
Location: CAD_Data_Cleaning_Engine/data/01_raw/
File: 2019_to_2026_01_30_CAD.csv
Size: 217.5 MB
Records: 753,903 (includes all supplements/units)
Purpose: Input for enhanced_esri_output_generator.py
```

**This is NOT suitable for incremental mode because:**
- It's the raw consolidated output
- Hasn't been through RMS backfill yet
- Hasn't been normalized yet
- Contains all duplicate events (supplements, unit records)

### 2. ESRI Polished Excel (Production Baseline)

```
Location: 13_PROCESSED_DATA/ESRI_Polished/base/
File: CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx
Size: 71.4 MB
Records: 724,794 (deduplicated, normalized)
Purpose: Production-ready for ArcGIS deployment
```

**This is the correct baseline for:**
- ArcGIS dashboard backfills
- Monthly incremental appends (after processing through ESRI generator)
- Server deployments

---

## Recommended Workflow

### Scenario A: Monthly Update (Incremental)

**When**: You have new 2026_02_CAD.xlsx and 2026_03_CAD.xlsx monthly files

**Steps:**

```powershell
# Step 1: Run FULL consolidation (includes all monthly files)
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
python consolidate_cad_2019_2026.py --full

# Step 2: Generate polished ESRI output (this processes the raw consolidated CSV)
cd "../CAD_Data_Cleaning_Engine"
python scripts/enhanced_esri_output_generator.py `
    --input "data/01_raw/2019_to_2026_01_30_CAD.csv" `
    --output-dir "data/03_final" `
    --format excel

# Step 3: Update baseline in 13_PROCESSED_DATA
cd "../cad_rms_data_quality"
python scripts/update_baseline_from_polished.py

# Step 4: (Optional) Copy to server for deployment
python scripts/copy_polished_to_processed_and_update_manifest.py
```

**Why Full Mode?**
- Incremental mode failed last night because the baseline is already processed
- Full mode re-processes everything from yearly + monthly files (only takes ~2-3 minutes)
- Ensures consistency across entire dataset

### Scenario B: Backfill Dashboard (On-Demand)

**When**: You want to update the ArcGIS dashboard with historical + recent data

**Steps:**

```powershell
# On LOCAL machine: Copy polished file to server
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\arcgis"
.\Copy-PolishedToServer.ps1

# On SERVER (via RDP): Run backfill orchestrator
cd "C:\HPD ESRI\04_Scripts"
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
```

**This uses the staging file pattern:**
- Model reads from fixed path (`_STAGING\ESRI_CADExport.xlsx`)
- Orchestrator swaps in your backfill file → publishes → swaps back to default export
- No manual model editing required

---

## Directory Structure (Updated)

```
13_PROCESSED_DATA/
├── manifest.json                                    # Latest file registry
├── README.md
└── ESRI_Polished/
    ├── base/
    │   ├── CAD_ESRI_Polished_Baseline.xlsx          # Generic "latest" pointer (71.4 MB)
    │   ├── CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx  # Archived baseline
    │   └── CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx  # NEW (after Feb update)
    ├── incremental/
    │   └── 2026_02_03_append/                       # Date-stamped incremental runs
    │       └── CAD_ESRI_Polished_20260203_123456.xlsx
    └── full_rebuild/                                # Full consolidation outputs
        └── 2026_02_03_full/
            └── CAD_ESRI_Polished_20260203_234500.xlsx
```

---

## File Naming Convention

### Baseline Files

**Generic (symlink-style):**
```
CAD_ESRI_Polished_Baseline.xlsx
```
- Always points to latest baseline
- Scripts reference this name
- Overwritten with each update

**Versioned (archive):**
```
CAD_ESRI_Polished_Baseline_YYYYMMDD_YYYYMMDD.xlsx
```
- Example: `CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx`
- First date: Dataset start (2019-01-01)
- Second date: Dataset end (2026-02-03)
- Preserved for historical tracking

### Incremental Run Outputs

```
ESRI_Polished/incremental/YYYY_MM_DD_append/
└── CAD_ESRI_Polished_YYYYMMDD_HHMMSS.xlsx
```

Example: `2026_02_03_append/CAD_ESRI_Polished_20260203_143052.xlsx`

---

## Manifest.json Structure

The manifest tracks the latest baseline for programmatic discovery:

```json
{
  "latest": {
    "filename": "CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx",
    "generic_pointer": "CAD_ESRI_Polished_Baseline.xlsx",
    "full_path": "C:\\...\\13_PROCESSED_DATA\\ESRI_Polished\\base\\CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx",
    "generic_path": "C:\\...\\13_PROCESSED_DATA\\ESRI_Polished\\base\\CAD_ESRI_Polished_Baseline.xlsx",
    "record_count": 753903,
    "date_range": {
      "start": "2019-01-01",
      "end": "2026-02-03"
    },
    "file_size_mb": 72.1,
    "updated": "2026-02-03T14:30:52",
    "source_file": "CAD_ESRI_POLISHED_20260203_143052.xlsx",
    "run_type": "baseline_update"
  },
  "baseline": {
    "path": "C:\\...\\base\\CAD_ESRI_Polished_Baseline.xlsx",
    "versioned_path": "C:\\...\\base\\CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx",
    "record_count": 753903,
    "date_range": {
      "start": "2019-01-01",
      "end": "2026-02-03"
    }
  },
  "history": {
    "last_update": "2026-02-03T14:30:52",
    "update_method": "update_baseline_from_polished.py"
  }
}
```

---

## Task Scheduler Interaction

### Daily Export Publishing (Automated)

**Task Name:** `LawSoftESRICADExport`  
**Schedule:** Daily at 12:30 AM  
**What it does:**

```powershell
# 1. FileMaker exports fresh data to default location
# 2. Scheduled task copies to staging
Copy-Item `
    "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx" `
    "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx" -Force

# 3. Runs TransformCallData_tbx1 tool (reads from staging)
# 4. Dashboard updates automatically
```

**Note:** This publishes **daily incremental data only** (last 24 hours of CAD events), not the full baseline.

### Backfill Publishing (Manual)

**When:** You want to refresh the dashboard with historical + recent data  
**Tool:** `Invoke-CADBackfillPublish.ps1`  
**What it does:**

1. Checks for lock file (prevents collisions with scheduled task)
2. Swaps in your backfill file → staging
3. Runs TransformCallData_tbx1 tool
4. Swaps default export back → staging
5. Dashboard now shows historical data

---

## The "Incremental Mode" Issue (From Last Night)

**Problem:**
You tried to run incremental mode, but it lost data:
- Expected: 725,463 records (baseline 724,794 + new 669)
- Actual: 559,651 records

**Root Cause:**
The baseline file (`CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx`) is **already processed/deduplicated**. When incremental mode loaded it and tried to append new monthly data, it deduplicated **again**, incorrectly treating the baseline as if it needed deduplication.

**Solution:**
Always use `--full` mode for consolidations. It only takes 2-3 minutes and ensures consistency.

---

## Best Practices

### DO:
✅ Run `--full` consolidation when adding monthly files  
✅ Use `update_baseline_from_polished.py` after generating polished output  
✅ Keep both generic and versioned baseline files  
✅ Check manifest.json for latest file paths  
✅ Use dry-run mode to preview changes (`--dry-run`)

### DON'T:
❌ Use incremental mode with polished baseline (causes data loss)  
❌ Manually edit baseline filenames (let script handle it)  
❌ Skip updating manifest.json (breaks programmatic discovery)  
❌ Delete old versioned baselines (they're your rollback safety net)

---

## Troubleshooting

### Issue: "Baseline file not found"

**Solution:**
```powershell
# Check if baseline exists
Test-Path "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx"

# If missing, run update script
python scripts/update_baseline_from_polished.py
```

### Issue: "Record count mismatch after incremental run"

**Solution:**
Don't use incremental mode. Use `--full` instead:
```powershell
python consolidate_cad_2019_2026.py --full
```

### Issue: "Manifest.json out of date"

**Solution:**
```powershell
# Re-run baseline update to refresh manifest
python scripts/update_baseline_from_polished.py
```

---

## Summary

**To answer your original questions:**

1. **Auto-save logic?** → YES - Use `update_baseline_from_polished.py` after generating polished output
2. **Generic vs dated name?** → BOTH - Generic pointer (`CAD_ESRI_Polished_Baseline.xlsx`) + versioned archive
3. **Manual or task scheduler?** → HYBRID:
   - Daily exports: Automated via task scheduler
   - Backfills: Manual via orchestrator
   - Baseline updates: Semi-automatic via script

**Recommended monthly workflow:**
```powershell
# 1. Consolidate (2-3 min)
python consolidate_cad_2019_2026.py --full

# 2. Generate polished (3-5 min)
python ../CAD_Data_Cleaning_Engine/scripts/enhanced_esri_output_generator.py --input "..." --output-dir "..."

# 3. Update baseline (30 sec)
python scripts/update_baseline_from_polished.py

# 4. Deploy to server (when ready)
# Use Invoke-CADBackfillPublish.ps1 workflow
```

---

**Version:** 1.0  
**Last Updated:** 2026-02-03
