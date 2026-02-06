# BACKFILL QUICK GUIDE - Missing Data (01/01/26 - 01/09/26)

**Date:** 2026-02-03  
**Issue:** Missing CAD data for January 1-9, 2026  
**Goal:** Backfill ArcGIS Dashboard ASAP

---

## Step 1: Verify the Gap (2 minutes)

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"

# Check what data you currently have
python scripts/backfill_gap_analysis.py --analyze --gap-start 2026-01-01 --gap-end 2026-01-09
```

**This will show you:**
- Do you have ANY records in Jan 1-9?
- What's the first record date?
- What's the last record before the gap?
- What's the first record after the gap?

---

## Step 2: Get the Backfill File

**Option A: Download from LawSoft**
1. Log into LawSoft
2. Export CAD data for date range: `2026-01-01` to `2026-01-09`
3. Save as: `2026_01_01_to_2026_01_09_CAD.xlsx`

**Option B: Check if it's in monthly file**
The file `05_EXPORTS\_CAD\monthly\2026\2026_01_CAD.xlsx` might already contain this data. Check the date range:

```powershell
python scripts/check_baseline_metadata.py --file "C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\monthly\2026\2026_01_CAD.xlsx"
```

---

## Step 3: Merge Backfill Data (5 minutes)

### A. Dry Run First (Preview)

```powershell
python scripts/backfill_gap_analysis.py `
    --merge `
    --backfill "C:\path\to\2026_01_01_to_2026_01_09_CAD.xlsx" `
    --dry-run
```

**This shows:**
✅ How many records will be added  
✅ How many duplicates will be removed  
✅ New date range  
✅ New record count  
❌ Does NOT save anything yet

### B. Actual Merge

```powershell
python scripts/backfill_gap_analysis.py `
    --merge `
    --backfill "C:\path\to\2026_01_01_to_2026_01_09_CAD.xlsx"
```

**Output:** New baseline file with gap filled

---

## Step 4: Update Manifest (30 seconds)

```powershell
python scripts/update_baseline_from_polished.py
```

This updates `manifest.json` so scripts know where the latest file is.

---

## Step 5: Deploy to ArcGIS (30 minutes)

### A. Copy to Server (Local Machine)

```powershell
cd docs\arcgis
.\Copy-PolishedToServer.ps1
```

### B. Run Backfill Publish (Server via RDP)

```powershell
# Connect to HPD2022LAWSOFT via RDP
cd "C:\HPD ESRI\04_Scripts"

# Test readiness
.\Test-PublishReadiness.ps1

# Run backfill (dry run first)
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" `
    -DryRun

# Actual run
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
```

---

## Duplicate Checking: YES, It's Automatic!

### How Duplicates Are Handled

**In consolidation script (`consolidate_cad_2019_2026.py`):**
```python
# Line 589-591: Deduplication by ReportNumberNew
combined = combined.drop_duplicates(subset=['ReportNumberNew'], keep='first')
```

**In backfill merge script (`backfill_gap_analysis.py`):**
```python
# Removes duplicates from backfill BEFORE merging
df_backfill_unique = df_backfill[~df_backfill['ReportNumberNew'].isin(baseline_ids)]
```

### What This Means

✅ **Duplicates are automatically removed**
- Script keeps the FIRST occurrence of each `ReportNumberNew`
- If case `26-000001` exists in baseline, it won't be added from backfill
- Only NEW cases are added

✅ **Safe to run multiple times**
- Running backfill merge twice won't create duplicates
- Script will just report "0 new records added"

✅ **Supplements are preserved**
- Case `26-000001` (original incident)
- Case `26-000001A` (supplement 1)
- Case `26-000001B` (supplement 2)
- All are kept (different `ReportNumberNew` values)

---

## Finding First Record of Jan 9

Run the gap analysis:

```powershell
python scripts/backfill_gap_analysis.py --analyze
```

**Output will show:**
```
Last 5 records BEFORE gap:
  2026-01-09 23:45:00 - 26-000089
  2026-01-09 22:30:00 - 26-000088
  2026-01-09 21:15:00 - 26-000087
  ...

First 5 records AFTER gap:
  2026-01-10 00:05:00 - 26-000090
  2026-01-10 00:15:00 - 26-000091
  ...
```

This tells you:
- **Last record of Jan 9:** `26-000089` at 23:45:00
- **First record of Jan 10:** `26-000090` at 00:05:00
- **First missing record:** Anything between these

---

## Expected Timeline

| Step | Time | Notes |
|------|------|-------|
| 1. Verify gap | 2 min | Quick analysis |
| 2. Get backfill file | 5 min | Export from LawSoft |
| 3. Merge data | 5 min | Includes dry run |
| 4. Update manifest | 30 sec | Auto-update |
| 5A. Copy to server | 2 min | Network copy |
| 5B. Run backfill publish | 15 min | Includes verification |
| 5C. Verify dashboard | 5 min | Spot checks |
| **TOTAL** | **~30-35 min** | **From start to dashboard updated** |

---

## Troubleshooting

### "No backfill file available"

Check if Jan 1-9 data is already in the monthly file:
```powershell
# Check what's in the monthly file
python scripts/check_baseline_metadata.py --file "C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\monthly\2026\2026_01_CAD.xlsx"
```

If it shows date range `2026-01-01 to 2026-01-31`, you already have the data! 

**The issue might be** that the consolidation script is filtering it out. Check the `END_DATE` in Line 71 of `consolidate_cad_2019_2026.py`.

### "Duplicate case numbers found"

**This is NORMAL and expected!** The script will automatically:
1. Identify duplicates
2. Keep baseline version (already processed/validated)
3. Discard backfill duplicates
4. Only add truly NEW records

### "Date range shows 2026-02-01 but missing Jan 1-9"

This means:
- Your baseline has data from Jan 10 onward
- Jan 1-9 is genuinely missing
- You NEED a backfill file for Jan 1-9

---

## Quick Commands Reference

```powershell
# 1. Analyze gap
python scripts/backfill_gap_analysis.py --analyze

# 2. Check metadata (without opening file)
python scripts/show_baseline_info.ps1

# 3. Merge backfill (dry run)
python scripts/backfill_gap_analysis.py --merge --backfill "path/to/file.xlsx" --dry-run

# 4. Merge backfill (actual)
python scripts/backfill_gap_analysis.py --merge --backfill "path/to/file.xlsx"

# 5. Update manifest
python scripts/update_baseline_from_polished.py

# 6. Deploy to server
.\docs\arcgis\Copy-PolishedToServer.ps1
```

---

## Priority: ASAP Backfill

Since you need this **ASAP**, recommended fast path:

### Fast Path (Skip ESRI Generator if already have polished file)

```powershell
# 1. If you already have the polished baseline (71.4 MB Excel):
#    Just add the missing Jan 1-9 data to it directly

# 2. Merge backfill
python scripts/backfill_gap_analysis.py `
    --merge `
    --backfill "C:\path\to\2026_01_01_to_2026_01_09_CAD.xlsx"

# 3. Update manifest
python scripts/update_baseline_from_polished.py

# 4. Copy to server and publish
cd docs\arcgis
.\Copy-PolishedToServer.ps1

# Then on server (RDP):
cd "C:\HPD ESRI\04_Scripts"
.\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
```

**Total time: ~20-25 minutes** (skips consolidation + ESRI generator steps)

---

**Need help? All scripts have `--help` flags:**
```powershell
python scripts/backfill_gap_analysis.py --help
python scripts/update_baseline_from_polished.py --help
```
