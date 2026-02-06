# Validation System Documentation Index

**Created:** 2026-02-04  
**Purpose:** Central index of all validation system documentation

---

## Primary Documentation

| Document | Purpose | Last Updated |
|----------|---------|--------------|
| [README.md](README.md) | System overview, quick start, components | 2026-02-04 |
| [FIRST_PRODUCTION_RUN_SUMMARY.md](FIRST_PRODUCTION_RUN_SUMMARY.md) | First production run results & findings | 2026-02-04 |
| [NEXT_STEPS.md](NEXT_STEPS.md) | Action items and recommendations | 2026-02-04 |
| [DRIFT_SYNC_GUIDE.md](DRIFT_SYNC_GUIDE.md) | Complete drift sync workflow | 2026-02-04 |

---

## Technical Reference

| Document | Purpose | Last Updated |
|----------|---------|--------------|
| [CAD_ESRI_DATA_DICTIONARY.md](CAD_ESRI_DATA_DICTIONARY.md) | Field definitions and types | 2026-02-04 |
| [EXISTING_LOGIC_INVENTORY.md](EXISTING_LOGIC_INVENTORY.md) | Existing validation logic catalog | 2026-02-04 |
| [PHASE3_VALIDATOR_PLAN.md](PHASE3_VALIDATOR_PLAN.md) | Validator implementation plan | 2026-02-04 |
| [DRIFT_DATA_ANALYSIS.md](DRIFT_DATA_ANALYSIS.md) | Drift data analysis and patterns | 2026-02-04 |
| [DRIFT_TOOLS_COMPLETE.md](DRIFT_TOOLS_COMPLETE.md) | Automation tools documentation | 2026-02-04 |

---

## Project Logs

| Document | Purpose | Last Updated |
|----------|---------|--------------|
| [VALIDATION_PROJECT_LOG.md](VALIDATION_PROJECT_LOG.md) | Project progress log | 2026-02-04 |

---

## Validation Reports

Location: `validation/reports/`

| Report | Content |
|--------|---------|
| validation_summary_YYYYMMDD_HHMMSS.json | Machine-readable validation results |
| validation_report_YYYYMMDD_HHMMSS.md | Human-readable validation report |
| validation_issues_YYYYMMDD_HHMMSS.xlsx | Row-level issues (Excel) |

**Latest Reports (2026-02-04):**
- `validation_summary_20260204_003131.json`
- `validation_report_20260204_003131.md`
- `validation_issues_20260204_003131.xlsx`

---

## Drift Reports

Location: `validation/reports/drift/`

| Report | Content |
|--------|---------|
| call_types_ALL_to_add_*.csv | All new call types detected |
| call_types_approved_*.csv | Approved call type additions |
| personnel_ALL_to_add_*.csv | All new personnel detected |
| personnel_approved_*.csv | Approved personnel additions |

---

## Code Documentation

### Validators (`validators/`)

| File | Purpose |
|------|---------|
| base_validator.py | Base class for all validators |
| how_reported_validator.py | How Reported field validator (12 valid values) |
| disposition_validator.py | Disposition field validator (25 valid values) |
| case_number_validator.py | Case number format validator (YY-NNNNNN) |
| incident_validator.py | Incident/call type validator (823 types) |
| datetime_validator.py | DateTime fields validator (4 fields) |
| duration_validator.py | Duration/time fields validator |
| officer_validator.py | Officer/personnel validator (387 officers) |
| geography_validator.py | Address and zone validator |
| derived_field_validator.py | Derived/calculated fields validator |

### Drift Detection & Sync (`sync/`)

| File | Purpose |
|------|---------|
| call_type_drift.py | Call type drift detector |
| personnel_drift.py | Personnel drift detector |
| extract_drift_reports.py | Export drift to CSV files |
| extract_all_drift.py | Full extraction (no limits) |
| apply_drift_sync.py | Apply approved changes with backups |
| batch_mark_add.py | Bulk mark items for addition |

### Orchestration

| File | Purpose |
|------|---------|
| run_all_validations.py | Master orchestrator - runs all validators |

---

## Reference Files (External)

| File | Location | Records |
|------|----------|---------|
| CallTypes_Master.csv | 09_Reference/Classifications/CallTypes/ | 823 |
| Assignment_Master_V2.csv | 09_Reference/Personnel/ | 387 |
| CAD_ESRI_Polished_Baseline.xlsx | 13_PROCESSED_DATA/ESRI_Polished/base/ | 754,409 |

---

## Related Project Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| README.md | cad_rms_data_quality/ | Main project README |
| CHANGELOG.md | cad_rms_data_quality/ | Version history |
| Claude.md | cad_rms_data_quality/ | AI agent guidelines |

---

## Quick Links

**Run Validation:**
```powershell
python run_all_validations.py -i "path/to/baseline.xlsx" -o "reports/"
```

**View Latest Report:**
```powershell
code validation/reports/validation_report_20260204_003131.md
```

**Sync Reference Data:**
```powershell
python sync/apply_drift_sync.py --call-types "drift/call_types.csv" --apply
```

---

**Maintained by:** R. A. Carucci  
**Last Updated:** 2026-02-04
