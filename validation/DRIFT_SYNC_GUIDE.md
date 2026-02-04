# Drift Detection & Reference Data Sync Guide

## Overview

The drift detection system identifies differences between your reference files and operational data, then helps you sync them.

---

## Workflow

### Step 1: Run Validation (Detects Drift)

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"

python validation/run_all_validations.py `
  -i "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx" `
  -o "validation/reports"
```

**Output:** `validation/reports/validation_summary_YYYYMMDD_HHMMSS.json`

---

### Step 2: Extract Drift to Review CSVs

```powershell
# Extract drift reports to easy-to-review CSV files
python validation/sync/extract_drift_reports.py `
  -i "validation/reports/validation_summary_20260204_003131.json" `
  -o "validation/reports/drift"
```

**Output:**
- `call_types_to_add_YYYYMMDD_HHMMSS.csv` - New call types found
- `call_types_unused_YYYYMMDD_HHMMSS.csv` - Call types not used recently
- `personnel_to_add_YYYYMMDD_HHMMSS.csv` - New personnel found

---

### Step 3: Review & Mark Actions in Excel

Open the CSV files and review each entry:

#### For `call_types_to_add_*.csv`:

| CallType | Frequency | Action | ConsolidateWith | Notes |
|----------|-----------|--------|-----------------|-------|
| Motor Vehicle Crash – Hit and Run | 2177 | **Add** | | New legitimate type |
| Relief/Personal | 1147 | **Consolidate** | Relief / Personal | Spacing variant |
| Shoplifting - 2C:20-11 | 442 | **Ignore** | | Duplicate with statute |

**Actions:**
- `Add` - Add to reference file as-is
- `Consolidate` - Map to existing type (specify in ConsolidateWith)
- `Ignore` - Skip this entry

#### For `personnel_to_add_*.csv`:

| Officer | CallCount | Action | Status | Notes |
|---------|-----------|--------|--------|-------|
| P.O. Matthew Tedesco 316 | 11971 | **Add** | Active | New hire 2024 |
| SPO. Aster Abueg 817 | 11740 | **Add** | Active | Promoted 2025 |

**Actions:**
- `Add` - Add to reference file
- `Consolidate` - Name variation (specify in ConsolidateWith)

---

### Step 4: Apply Approved Changes (Dry Run First)

```powershell
# DRY RUN - See what would change (no files modified)
python validation/sync/apply_drift_sync.py `
  --call-types "validation/reports/drift/call_types_to_add_20260204_003131.csv" `
  --personnel "validation/reports/drift/personnel_to_add_20260204_003131.csv"
```

**Review the output carefully!**

---

### Step 5: Apply Changes for Real

```powershell
# APPLY - Actually update reference files
python validation/sync/apply_drift_sync.py `
  --call-types "validation/reports/drift/call_types_to_add_20260204_003131.csv" `
  --personnel "validation/reports/drift/personnel_to_add_20260204_003131.csv" `
  --apply
```

**This will:**
- Create timestamped backups in `backups/` folders
- Add approved entries to reference files
- Print summary of changes

---

### Step 6: Verify Changes

```powershell
# Check what was updated
git status
git diff 09_Reference/Classifications/CallTypes/CallTypes_Master.csv
git diff 09_Reference/Personnel/Assignment_Master_V2.csv
```

---

### Step 7: Re-Run Validation

```powershell
# Run validation again to verify drift is resolved
python validation/run_all_validations.py `
  -i "path/to/baseline.xlsx" `
  -o "validation/reports"
```

**Expected:** Fewer "new" items detected, improved coverage percentage

---

### Step 8: Commit to Git

```powershell
git add validation/
git add ../09_Reference/

git commit -m "$(cat <<'EOF'
Reference Data Sync: Call Types and Personnel Updates

Drift Detection Results:
- Added 184 new call types to CallTypes_Master.csv
- Added 219 new personnel to Assignment_Master_V2.csv
- Backups created in respective backups/ folders

Impact:
- Call type coverage improved from 59% to XX%
- Personnel coverage improved from 44% to XX%
- Validation quality score: XX% (expected improvement)

Files synced based on validation run: YYYYMMDD_HHMMSS
EOF
)"
```

---

## Command Quick Reference

```powershell
# 1. Run validation
python validation/run_all_validations.py -i baseline.xlsx -o validation/reports

# 2. Extract drift to CSV
python validation/sync/extract_drift_reports.py -i validation/reports/validation_summary_*.json

# 3. [MANUAL] Review CSVs in Excel and mark actions

# 4. Dry run sync
python validation/sync/apply_drift_sync.py --call-types drift/call_types_to_add_*.csv --personnel drift/personnel_to_add_*.csv

# 5. Apply sync
python validation/sync/apply_drift_sync.py --call-types drift/call_types_to_add_*.csv --personnel drift/personnel_to_add_*.csv --apply

# 6. Verify and commit
git status
git diff
git add . && git commit
```

---

## File Locations

**Drift Detection Scripts:**
```
validation/sync/
├── call_type_drift_detector.py     (Core detector - already exists)
├── personnel_drift_detector.py     (Core detector - already exists)
├── extract_drift_reports.py        (NEW - Export to CSV)
└── apply_drift_sync.py              (NEW - Apply approved changes)
```

**Reference Files:**
```
09_Reference/
├── Classifications/CallTypes/
│   ├── CallTypes_Master.csv        (Target for call type updates)
│   └── backups/                    (Auto-created backups)
└── Personnel/
    ├── Assignment_Master_V2.csv    (Target for personnel updates)
    └── backups/                    (Auto-created backups)
```

**Drift Reports:**
```
validation/reports/drift/
├── call_types_to_add_YYYYMMDD.csv
├── call_types_unused_YYYYMMDD.csv
└── personnel_to_add_YYYYMMDD.csv
```

---

## Safety Features

1. **Backups:** Automatic timestamped backups before any changes
2. **Dry Run:** Default mode shows changes without modifying files
3. **Manual Review:** You approve each addition via CSV
4. **Git History:** All changes tracked in version control
5. **Rollback:** Can revert using backups or `git checkout`

---

## Tips

**For Call Types:**
- Look for spacing/punctuation variants to consolidate
- Check for duplicates with/without statute codes
- Verify new types are legitimate (not data entry errors)
- Mark rarely-used types for further investigation

**For Personnel:**
- Watch for name variations (e.g., with/without middle initials)
- Verify badge numbers match HR records
- Mark retired officers as Inactive
- Add notes for special cases (transfers, promotions)

**Frequency Matters:**
- High frequency (>1000) = Likely legitimate, add immediately
- Medium frequency (100-1000) = Review carefully
- Low frequency (<100) = Investigate before adding

---

## Troubleshooting

**Issue:** "No call types marked for addition"
- **Fix:** Open the CSV and set Action column to "Add" for entries you approve

**Issue:** Sync script fails with column mismatch
- **Fix:** Check reference file column names match script expectations
- Edit `apply_drift_sync.py` to match your column names

**Issue:** Git shows too many changes
- **Fix:** Review backups folder - may need to add to .gitignore

---

## Next Steps After First Sync

1. **Schedule Regular Drift Detection**
   - Run monthly or after major data updates
   - Track drift trends over time
   - Set up alerts for high drift (>50 new items)

2. **Maintain Reference Data Quality**
   - Quarterly review of unused items
   - Annual audit of all reference data
   - Document decision criteria for future syncs

3. **Automate Where Possible**
   - Auto-add high-frequency items (>1000 occurrences)
   - Flag suspicious items for manual review
   - Email drift reports to data stewards

---

**This drift detection and sync process ensures your reference data stays in sync with operational reality! 🔄**
