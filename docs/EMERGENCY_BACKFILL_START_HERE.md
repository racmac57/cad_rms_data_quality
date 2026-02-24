# EMERGENCY BACKFILL - Quick Start

**Status:** No baseline files found - need to build from scratch
**Time Required:** ~15-20 minutes total

---

## Current Situation

Based on system check:
- ❌ No baseline file exists yet in `13_PROCESSED_DATA\ESRI_Polished\base\`
- ❌ No polished Excel in `CAD_Data_Cleaning_Engine\data\03_final\`
- ❌ No consolidated CSV in `CAD_Data_Cleaning_Engine\data\01_raw\`

**You need to run the full pipeline first.**

---

## FAST TRACK: Build Baseline Now (15-20 minutes)

### Step 1: Consolidate CAD Data (2-3 min)

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"

# Run full consolidation (includes all monthly files)
python consolidate_cad_2019_2026.py --full
```

**Expected output:**
- Total records: ~753,903
- Date range: 2019-01-01 to 2026-02-01
- Output: `CAD_Data_Cleaning_Engine\data\01_raw\2019_to_2026_01_30_CAD.csv`

---

### Step 2: Generate ESRI Polished Output (3-5 min)

```powershell
cd "..\CAD_Data_Cleaning_Engine"

# Generate polished Excel
python scripts\enhanced_esri_output_generator.py `
    --input "data\01_raw\2019_to_2026_01_30_CAD.csv" `
    --output-dir "data\03_final" `
    --format excel
```

**Expected output:**
- Polished Excel file: `CAD_ESRI_POLISHED_YYYYMMDD_HHMMSS.xlsx`
- Size: ~70-75 MB
- Location: `data\03_final\`

---

### Step 3: Create Baseline (30 sec)

```powershell
cd "..\cad_rms_data_quality"

# Copy polished to baseline location and update manifest
python scripts\update_baseline_from_polished.py
```

**This creates:**
- Generic pointer: `CAD_ESRI_Polished_Baseline.xlsx`
- Versioned archive: `CAD_ESRI_Polished_Baseline_20190101_20260202.xlsx`
- manifest.json: Latest file registry

---

### Step 4: Analyze Gap for Jan 1-9 (2 min)

```powershell
# Now you can check for the gap
python scripts\backfill_gap_analysis.py --analyze --gap-start 2026-01-01 --gap-end 2026-01-09
```

**This will tell you:**
- Do you have records for Jan 1-9?
- What's the first record date?
- Is there actually a gap?

---

### Step 5: If Gap Exists - Get Backfill Data (5 min)

**Option A:** Check if data is in monthly file

```powershell
# The 2026_01_CAD.xlsx file might already have Jan 1-9 data
# Check its date range
python scripts\check_baseline_metadata.py --file "C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\monthly\2026\2026_01_CAD.xlsx"
```

**Option B:** Export from LawSoft
1. Log into LawSoft
2. Export CAD data: 2026-01-01 to 2026-01-09
3. Save as: `2026_01_01_to_2026_01_09_CAD.xlsx`

---

### Step 6: Merge Backfill (if needed) (3 min)

```powershell
# Dry run first
python scripts\backfill_gap_analysis.py `
    --merge `
    --backfill "path\to\backfill.xlsx" `
    --dry-run

# Actual merge
python scripts\backfill_gap_analysis.py `
    --merge `
    --backfill "path\to\backfill.xlsx"

# Update manifest
python scripts\update_baseline_from_polished.py
```

---

### Step 7: Deploy to Server (30 min)

```powershell
# Copy to server (local machine)
cd docs\arcgis
.\Copy-PolishedToServer.ps1

# On server (via RDP):
cd "C:\HPD ESRI\04_Scripts"
.\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
```

---

## Alternative: Skip Gap Analysis (If you know data is complete)

If you're confident the monthly files already have all the data:

```powershell
# 1. Consolidate
python consolidate_cad_2019_2026.py --full

# 2. Generate polished
cd ..\CAD_Data_Cleaning_Engine
python scripts\enhanced_esri_output_generator.py --input "data\01_raw\2019_to_2026_01_30_CAD.csv" --output-dir "data\03_final" --format excel

# 3. Create baseline
cd ..\cad_rms_data_quality
python scripts\update_baseline_from_polished.py

# 4. Deploy
cd docs\arcgis
.\Copy-PolishedToServer.ps1
```

**Total time: ~10-15 minutes** (skips gap analysis and backfill)

---

## Why No Baseline Exists Yet

The baseline file is created AFTER you:
1. ✅ Run consolidation (`consolidate_cad_2019_2026.py`)
2. ✅ Generate polished output (`enhanced_esri_output_generator.py`)
3. ✅ Copy to baseline location (`update_baseline_from_polished.py`)

You're at step 0 right now - need to build everything from scratch.

---

## Next Steps

**Start now:**
```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
python consolidate_cad_2019_2026.py --full
```

Then come back to this guide for the next steps.

---

**Estimated total time if gap exists:** 15-20 minutes  
**Estimated total time if no gap:** 10-15 minutes  
**Plus deployment:** +15-30 minutes

**Total ASAP timeline:** 25-50 minutes from start to dashboard updated
