# CAD Data Quality Validation System

**Version:** 1.0.0  
**Created:** 2026-02-04  
**Status:** Production-Ready  
**Quality Score:** 98.3% (Grade A) on 754,409 records

---

## Overview

A comprehensive data quality validation framework for CAD (Computer-Aided Dispatch) data. Validates all critical fields, detects reference data drift, and provides automated sync tools.

---

## Quick Start

```powershell
# Run full validation
python run_all_validations.py -i "path/to/baseline.xlsx" -o "reports/"

# With default paths
python run_all_validations.py \
  -i "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx" \
  -o "validation/reports"
```

**Output:**
- `validation_summary_YYYYMMDD_HHMMSS.json` - Machine-readable results
- `validation_report_YYYYMMDD_HHMMSS.md` - Human-readable report
- `validation_issues_YYYYMMDD_HHMMSS.xlsx` - Row-level issues (Excel)

---

## Components

### Field Validators (`validators/`)

9 validators covering all critical CAD fields:

| Validator | Field | Weight | Description |
|-----------|-------|--------|-------------|
| HowReportedValidator | How Reported | 15% | Call source domain (12 valid values) |
| DispositionValidator | Disposition | 15% | Outcome domain (25 valid values) |
| CaseNumberValidator | ReportNumberNew | 20% | Format validation (YY-NNNNNN) |
| IncidentValidator | Incident | 15% | Call type vs reference (823 types) |
| DateTimeValidator | Time fields | 15% | 4 datetime fields validation |
| DurationValidator | Duration fields | 5% | Response time, time spent |
| OfficerValidator | Officer | 5% | Personnel vs reference (387 officers) |
| GeographyValidator | FullAddress2 | 5% | Address and zone validation |
| DerivedFieldValidator | Calculated fields | 5% | Year, month, hour, day consistency |

### Drift Detectors (`sync/`)

2 detectors for reference data monitoring:

| Detector | Purpose | Output |
|----------|---------|--------|
| CallTypeDriftDetector | New/unused call types | Lists new types not in reference |
| PersonnelDriftDetector | New/inactive personnel | Lists new officers not in reference |

### Automation Tools (`sync/`)

| Tool | Purpose |
|------|---------|
| extract_drift_reports.py | Export drift to reviewable CSV files |
| extract_all_drift.py | Full extraction (no 50-item limit) |
| apply_drift_sync.py | Apply approved changes with backups |
| batch_mark_add.py | Bulk mark items for addition |

---

## Drift Sync Workflow

```powershell
# 1. Run validation (detects drift)
python run_all_validations.py -i baseline.xlsx -o reports/

# 2. Extract drift to CSV (for review)
python sync/extract_all_drift.py

# 3. Review CSVs, mark Action column as "Add"

# 4. Apply approved changes (dry run first)
python sync/apply_drift_sync.py --call-types "file.csv" --personnel "file.csv"

# 5. Apply for real
python sync/apply_drift_sync.py --call-types "file.csv" --personnel "file.csv" --apply
```

**See:** `DRIFT_SYNC_GUIDE.md` for complete instructions.

---

## Documentation

| File | Purpose |
|------|---------|
| README.md | This file - system overview |
| FIRST_PRODUCTION_RUN_SUMMARY.md | Results from first production run |
| NEXT_STEPS.md | Action items and recommendations |
| DRIFT_SYNC_GUIDE.md | Complete drift sync workflow |
| DRIFT_TOOLS_COMPLETE.md | Automation tools documentation |
| DRIFT_DATA_ANALYSIS.md | Data analysis and patterns |
| CAD_ESRI_DATA_DICTIONARY.md | Field definitions and types |
| EXISTING_LOGIC_INVENTORY.md | Existing validation logic catalog |
| VALIDATION_PROJECT_LOG.md | Project progress log |

---

## Directory Structure

```
validation/
├── run_all_validations.py     # Master orchestrator
├── README.md                  # This file
├── validators/                # 9 field validators
│   ├── __init__.py
│   ├── base_validator.py      # Base class
│   ├── how_reported_validator.py
│   ├── disposition_validator.py
│   ├── case_number_validator.py
│   ├── incident_validator.py
│   ├── datetime_validator.py
│   ├── duration_validator.py
│   ├── officer_validator.py
│   ├── geography_validator.py
│   └── derived_field_validator.py
├── sync/                      # Drift detection & sync
│   ├── __init__.py
│   ├── call_type_drift.py
│   ├── personnel_drift.py
│   ├── extract_drift_reports.py
│   ├── extract_all_drift.py
│   ├── apply_drift_sync.py
│   └── batch_mark_add.py
├── reports/                   # Validation results
│   ├── validation_summary_*.json
│   ├── validation_report_*.md
│   ├── validation_issues_*.xlsx
│   └── drift/                 # Drift CSV files
└── [documentation files]
```

---

## Reference Files

| File | Location | Records |
|------|----------|---------|
| CallTypes_Master.csv | 09_Reference/Classifications/CallTypes/ | 823 types |
| Assignment_Master_V2.csv | 09_Reference/Personnel/ | 387 personnel |

---

## Quality Scoring

**Formula:** Weighted average of all validator pass rates

**Weights:**
- CaseNumber: 20%
- HowReported: 15%
- Disposition: 15%
- Incident: 15%
- DateTime: 15%
- Duration: 5%
- Officer: 5%
- Geography: 5%
- DerivedFields: 5%

**Grades:**
- A+ (99-100%): Excellent
- A (95-99%): Good
- B (90-95%): Acceptable
- C (80-90%): Needs attention
- D (<80%): Critical issues

---

## First Production Run (2026-02-04)

- **Records:** 754,409
- **Quality Score:** 98.3% (Grade A)
- **Processing Time:** ~6 minutes
- **Major Finding:** Disposition field had 87,896 false positives (fixed)
- **Drift Detected:** 174 new call types, 219 new personnel (synced)

---

## Maintenance

**Regular Tasks:**
1. Run validation monthly on production baseline
2. Review drift reports quarterly
3. Sync reference data as needed
4. Update validation thresholds annually

**Scheduling:**
```powershell
# Example: Schedule weekly validation (Monday 6 AM)
# See NEXT_STEPS.md for PowerShell script
```

---

## Troubleshooting

**Issue:** "No such column" error
- **Fix:** Check column names match expected (with/without spaces)

**Issue:** Validation takes too long
- **Fix:** Ensure parallel processing enabled, use sampling for testing

**Issue:** Drift sync fails
- **Fix:** Check CSV format, ensure Action column marked correctly

---

## Contact

**Author:** R. A. Carucci  
**Department:** City of Hackensack Police Department  
**Repository:** cad_rms_data_quality  

---

**Status:** Production-Ready and Validated
