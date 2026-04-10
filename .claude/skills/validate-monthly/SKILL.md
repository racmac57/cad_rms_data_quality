---
name: validate-monthly
description: Run monthly CAD or RMS export validation, parse the quality score, and surface action items. Use when a new monthly export arrives and needs quality checks before publishing.
disable-model-invocation: true
argument-hint: [cad|rms] [YYYY-MM]
allowed-tools: Bash(python *) Bash(pip *) Read Grep Glob
---

# Monthly Export Validation

Run the validation pipeline for a monthly CAD or RMS export and summarize results.

## Arguments

- `$0` -- Export type: `cad` or `rms` (required)
- `$1` -- Month: `YYYY-MM` format, e.g., `2026-03` (optional, defaults to most recent)

## Step-by-Step

### 1. Determine the input file

Read `config/consolidation_sources.yaml` to find the source path for the requested month.

**CAD path pattern:** `C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\monthly\{YYYY}\{YYYY}_{MM}_CAD.xlsx`
**RMS path pattern:** `C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\monthly\{YYYY}\{YYYY}_{MM}_RMS.xlsx`

If no month specified, find the most recent monthly file:
```bash
# Check what monthly files exist in the config
grep -A2 "month:" config/consolidation_sources.yaml | tail -6
```

If running locally (not on the Windows machine), tell the user the file is only accessible from the server and provide the path they need to copy from.

### 2. Validate the export file

**For CAD:**
```bash
python validation/run_all_validations.py \
    --input "<path_to_monthly_cad_file>" \
    --output "monthly_validation/reports/$(date +%Y_%m_%d)_cad" \
    --validators HowReported,Disposition,CaseNumber,Incident,DateTime,Duration,Geography
```

**For RMS:**
```bash
python -m monthly_validation.scripts.validate_rms
```

If the validation script is not runnable locally (e.g., paths are Windows-only), generate the command for the user to run on the server.

### 3. Parse and summarize results

After validation runs, read the generated reports:

- **Metrics JSON:** `monthly_validation/reports/<run_dir>/metrics.json` or `consolidation/reports/<run_dir>/consolidation_metrics.json`
- **Summary:** `monthly_validation/reports/<run_dir>/validation_summary.html`
- **Action items:** `monthly_validation/reports/<run_dir>/action_items.xlsx`

### 4. Quality assessment

Apply thresholds from `config/validation_rules.yaml`:

| Metric | Threshold | Action |
|--------|-----------|--------|
| Quality score | >= 95 | Pass |
| Quality score | 80-94 | Warning -- review action items |
| Quality score | < 80 | Fail -- do not publish until resolved |
| Duplicate rate | <= 1% | Pass |
| NULL required fields | <= 5% | Pass |
| Record count | 2,000-5,000/month | Normal range for CAD |
| Record count | < 2,000 or > 5,000 | Flag anomaly |

### 5. Report to user

Present a summary:

```
## Monthly Validation: {type} {YYYY-MM}

**Quality Score:** XX/100 (PASS/WARN/FAIL)
**Records:** X,XXX (expected: 2,000-5,000)
**Duplicates:** X.XX%

### Field Completeness
- ReportNumberNew: XX.X%
- Incident: XX.X%
- FullAddress2: XX.X%
- ...

### Action Items (if any)
1. [Priority 1] ...
2. [Priority 2] ...

### Recommendation
- PUBLISH / REVIEW BEFORE PUBLISHING / DO NOT PUBLISH
```

## Key Validators (from validation/validators/)

| Validator | Checks |
|-----------|--------|
| `CaseNumberValidator` | Pattern `^\d{2}-\d{6}([A-Z])?$`, uniqueness |
| `HowReportedValidator` | Domain values (9-1-1, Phone, Walk-In, etc.), normalization |
| `DispositionValidator` | Required, concatenated value splitting |
| `IncidentValidator` | Non-null, matches known call types |
| `DateTimeValidator` | Parseable dates, chronological order |
| `DurationValidator` | Response time calculations, exclusion rules |
| `GeographyValidator` | Lat/lon populated, within Hackensack bounds |
| `OfficerValidator` | Personnel field validation |
| `DerivedFieldValidator` | Computed fields match source data |

## Drift Detection

Also run drift detectors if the user asks for a thorough check:
```bash
python validation/run_all_validations.py \
    --input "<path>" \
    --output "monthly_validation/reports/$(date +%Y_%m_%d)_$0"
# Includes CallTypeDriftDetector and PersonnelDriftDetector
```
