# Backfill Date Range

**Recommended range:** **2019-01-01 through 2026-02-15** (or through yesterday when you run).

As of 2026-02-16, the backfill should include all CAD data from the start of 2019 through **February 15, 2026** (inclusive). That keeps the dashboard current without including “today” until your daily process has run.

---

## Extend baseline with a fresh export (02/01–02/15)

If your **monthly file** (e.g. `2026_02_CAD.xlsx`) only goes through **02/03/2026** (e.g. last record 26-011287 at 02/03/2026 09:50:44), you can:

1. **Export from your source (FileMaker/CAD)** the records for **02/01/2026 through 02/15/2026** (one Excel file).
2. **Merge** that export into the current baseline; the script will **remove duplicates** (same `ReportNumberNew`) and **add only new records** (e.g. 02/04–02/15).

**Steps:**

```powershell
# 1. Put your new export somewhere, e.g.:
#    ...\05_EXPORTS\_CAD\monthly\2026\2026_02_01_to_02_15_CAD.xlsx

# 2. Dry run (see duplicate count and new records)
python scripts/backfill_gap_analysis.py --merge --backfill "C:\...\2026_02_01_to_02_15_CAD.xlsx" --dry-run

# 3. Run merge (updates baseline and generic pointer in 13_PROCESSED_DATA\ESRI_Polished\base\)
python scripts/backfill_gap_analysis.py --merge --backfill "C:\...\2026_02_01_to_02_15_CAD.xlsx"
```

- **Baseline** = current `CAD_ESRI_Polished_Baseline.xlsx` (through 02/03).
- **Backfill file** = your export 02/01–02/15.
- Duplicates (02/01–02/03) are **kept from baseline** and dropped from the backfill; only **new** records (02/04–02/15) are added.
- Output: merged file with date range through 02/15, and the generic `CAD_ESRI_Polished_Baseline.xlsx` is updated.

The merge script accepts both **"Time of Call"** and **TimeOfCall** column names.

**Output schema:** Merge output always matches the **baseline file’s columns and order** (ESRI polished schema). If the backfill file uses different names (e.g. `Time_Of_Call`, `How_Reported`), they are renamed to match the baseline. This keeps the file valid for the RDP backfill script (`complete_backfill_simplified.py`). The canonical column set is defined by the baseline you pass in (e.g. `CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx`); see `scripts/test_baseline.py` for the expected 20-column list.

---

## How the range is set

1. **Consolidation** (`consolidate_cad_2019_2026.py`)  
   - Uses `START_DATE` and `END_DATE`.  
   - Current: `END_DATE = 2026-02-28`.  
   - To cap at 2026-02-15, set:
     - `END_DATE = pd.Timestamp("2026-02-15 23:59:59")`  
   - Re-run consolidation so the baseline CSV (and any downstream polished Excel) covers 2019-01-01 through 2026-02-15.

2. **Baseline / polished Excel**  
   - The file you use for backfill (e.g. `CAD_ESRI_Polished_Baseline.xlsx`) should be built from that consolidation run so its date range is 2019-01-01 through 2026-02-15.  
   - Or extend the current baseline with a **merge** (see above) using an export 02/01–02/15.

3. **Gap analysis** (`backfill_gap_analysis.py`)  
   - `--gap-start` / `--gap-end` are for **checking a specific gap** (e.g. Jan 1–9, 2026), not the full backfill range.  
   - Use `--merge --backfill <path>` to merge a new export and extend the baseline through 02/15.

---

## Quick reference

| What                | Value / action |
|---------------------|----------------|
| Backfill start      | 2019-01-01     |
| Backfill end (as of 2026-02-16) | 2026-02-15     |
| Extend baseline | Export 02/01–02/15 from source, then `backfill_gap_analysis.py --merge --backfill <file>` |
| Set in consolidation | `END_DATE = pd.Timestamp("2026-02-15 23:59:59")` then re-run |
| Staging file on RDP | Must span this range and have `longitude`/`latitude` or `X_Coord`/`Y_Coord` |
