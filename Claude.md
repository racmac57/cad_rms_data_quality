# Claude.md - CAD/RMS Data Quality System Context

This file provides context and rules for any Claude instance working in this repository. It lives at the repo root and complements any `.claude/` settings directory if present.

---

## Project Purpose

This repository contains a unified data quality system for CAD (Computer-Aided Dispatch) and RMS (Records Management System) exports. It consolidates best practices from multiple legacy projects and provides:

1. **Historical Consolidation** (Component 1): Merge 2019-2025 CAD data into single validated dataset for ArcGIS Pro dashboards (714K records, ~543K unique cases)
2. **Monthly Validation** (Component 2): Reusable validation scripts for ongoing CAD and RMS exports with detailed quality reporting
3. **Single Source of Truth**: Unified system replacing fragmented legacy projects (RMS_Data_ETL, RMS_Data_Processing, RMS_CAD_Combined_ETL)

---

## Project Status & Implementation Progress

### ✅ Phase 1: Consolidation Complete (2026-01-31)
- 724,794 records consolidated (2019-01-01 to 2026-01-30)
- ESRI polished output generated: `CAD_ESRI_POLISHED_20260131_014644.xlsx`
- Production script: `consolidate_cad_2019_2026.py`

### ✅ Expansion Plan Milestone 1: Paths & Baseline (2026-02-01)
- Created `13_PROCESSED_DATA/ESRI_Polished/` directory structure
- Copied baseline file (724,794 records) to `base/` directory
- Created `manifest.json` for latest file tracking
- Added baseline, incremental, performance, processed_data sections to config
- Config version updated to 2.0.0

### ✅ Expansion Plan Milestone 3: Server Copy + ArcPy (2026-02-01)
- Updated `copy_consolidated_dataset_to_server.ps1` to read from `manifest.json` (v2.0.0)
- Added `-DryRun` switch for testing, file integrity verification
- Created `docs/arcgis/import_cad_polished_to_geodatabase.py` - arcpy ExcelToTable script
- Created `docs/arcgis/README.md` - Workflow guide with order of operations

### ✅ Expansion Plan Milestone 4: Speed Optimizations (2026-02-02)
- Added parallel Excel loading with `ThreadPoolExecutor` (8 workers)
- Added chunked reading for files >50MB using openpyxl read_only mode
- Implemented baseline + incremental append mode
- Memory optimization: dtype downcasting (66-68% reduction)
- Added `--full` and `--dry-run` CLI flags

### ✅ Expansion Plan Milestone 5: Monthly Processing (2026-02-02)
- Created `monthly_validation/scripts/validate_cad.py` - Full CAD validation CLI
- Created `monthly_validation/scripts/validate_rms.py` - Full RMS validation CLI
- Quality scoring (0-100) with category breakdown
- Action items export (Excel with P1/P2/P3 priority sheets)
- HTML validation summary report with visual quality indicators
- JSON metrics for trend analysis
- Auto-generated report directories (YYYY_MM_DD_cad/, YYYY_MM_DD_rms/)
- Added `monthly_processing` section to config (v2.1.0)

### ✅ Expansion Plan Milestone 6: Legacy Archive (2026-02-02)
- Moved 5 legacy projects to `02_ETL_Scripts/_Archive/`
- Created `_Archive/README.md` with detailed migration notes
- Archived: CAD_Data_Cleaning_Engine, Combined_CAD_RMS, RMS_CAD_Combined_ETL, RMS_Data_ETL, RMS_Data_Processing
- cad_rms_data_quality is now the single active project

### v1.3.0 - ArcGIS Pro Backfill Automation (2026-02-02)
- **Problem**: Manual backfill process took 5+ hours with manual RDP copying, model editing, ArcPy errors, disorganized verification
- **Solution**: Staging file pattern + orchestration scripts reduce time to ~30 minutes
- **Tool discovery**: Created `discover_tool_info.py`, confirmed callable `arcpy.TransformCallData_tbx1()`
- **Configuration**: `config.json` with all paths, task names, expected counts (from manifest), tool callables
- **Orchestration**: `Invoke-CADBackfillPublish.ps1` with atomic swaps (SHA256 verification), auto-restore on error, collision control
- **Pre-flight checks**: `Test-PublishReadiness.ps1` - lock files, scheduled tasks, process check, geodatabase lock, Excel sheet validation
- **Python runner**: `run_publish_call_data.py` reads config and calls `arcpy.TransformCallData_tbx1()` via propy.bat
- **File copy**: `Copy-PolishedToServer.ps1` reads manifest.json, uses robocopy with retry, SMB share support
- **Documentation**: `README_Backfill_Process.md` - complete user guide for backfill automation

### v1.3.2 - Complete Baseline Generation & Testing (2026-02-03)
- **ESRI Generator Restored**: Found archived `enhanced_esri_output_generator.py` (v3.0, Dec 2025) and copied to active CAD_Data_Cleaning_Engine
- **Critical Bug Fixed**: Added column rename logic (TimeOfCall → Time of Call, etc.) so generator works with consolidated CSV format
- **Baseline Files Created**: Both generic (`CAD_ESRI_Polished_Baseline.xlsx`) and versioned (`CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx`) in 13_PROCESSED_DATA
- **Record Count**: 754,409 records (2019-01-01 to 2026-02-03) with 100% valid dates
- **Jan 1-9 Gap Filled**: Confirmed 3,101 records present for previously missing period
- **Testing Suite**: Created comprehensive test scripts (test_baseline.py, quick_test_baseline.py, backfill_gap_analysis.py)
- **All Tests Pass**: 10/10 validation checks passed - baseline is production-ready for ArcGIS deployment
- **Processing Time**: Full pipeline (consolidation → generation → testing) completed in ~51 minutes

### v1.3.4 - Backfill Investigation (2026-02-05)
- **Problem**: One-time backfill of 754K historical CAD records to ArcGIS dashboard failed twice, consistently hanging at feature 564916 (end of geocoding phase)
- **Investigation**: No error logs (silent hang), suggesting network timeout, database lock, or memory issue
- **System Status**: ✅ Emergency restore mechanism successfully cleaned up environment, system stable for nightly automated task
- **Data Quality**: ✅ Baseline file excellent quality (99.97%), Phone/911 fix applied, Jan 1-9 gap filled - data is ready, issue is with publishing process
- **Next Steps**: Test with smaller dataset (2024-2026, ~100K records), check geodatabase locks, or implement batch processing/API upload
- **Documentation**: Created `BACKFILL_INVESTIGATION_20260205.md` with comprehensive findings and recommendations

### v1.4.0 - Comprehensive Validation System Complete (2026-02-04)

**Status:** ✅ COMPLETE AND PRODUCTION-READY

**Summary:** Built a comprehensive data quality validation system for 754,409 CAD records.

**Components Built:**
- **9 Field Validators** (`validation/validators/`):
  - HowReportedValidator - Call source domain (100% pass)
  - DispositionValidator - Outcome domain (100% after fix)
  - CaseNumberValidator - Format YY-NNNNNN (99.99% pass)
  - IncidentValidator - Call type vs 823 reference types
  - DateTimeValidator - 4 datetime fields validation
  - DurationValidator - Response time, time spent
  - OfficerValidator - Personnel vs 387 reference
  - GeographyValidator - Address and zone
  - DerivedFieldValidator - Calculated field consistency

- **2 Drift Detectors** (`validation/sync/`):
  - CallTypeDriftDetector - New/unused call types
  - PersonnelDriftDetector - New/inactive personnel

- **Automation Tools** (`validation/sync/`):
  - extract_drift_reports.py - Export drift to CSV
  - extract_all_drift.py - Full extraction (no 50-item limit)
  - apply_drift_sync.py - Apply changes with backups
  - batch_mark_add.py - Bulk operations

- **Master Orchestrator** (`validation/run_all_validations.py`):
  - Single command runs all validators
  - Output formats: JSON, Excel, Markdown
  - Quality scoring with configurable weights
  - ~6 minutes for 754k records

**First Production Run Results:**
- **Quality Score:** 98.3% (Grade A)
- **Records:** 754,409
- **Date Range:** 2019-01-01 to 2026-02-04

**Issues Found and Fixed:**
1. **Disposition:** 87,896 false positives (11.7%) - Missing 5 valid values fixed
2. **Call Type Drift:** 174 new types synced (649 → 823)
3. **Personnel Drift:** 219 new officers synced (168 → 387)

**Git History (6 commits):**
```
2f088cb Post-Validation Cleanup: Disposition Fix & Reference Data Sync
96454fb Phase 5 Complete: Master Validation Orchestrator
e8a114f Phase 4 Complete: Drift Detectors Implementation
3952bff Phase 3 Complete: Field Validators Implementation
621d6d5 Phase 2 Complete: Data Dictionary & Validator Planning
b1ea6b7 Phase 1 Complete: Discovery & Reference Data Consolidation
```

**Key Files:**
- `validation/run_all_validations.py` - Master orchestrator
- `validation/validators/` - 9 field validators
- `validation/sync/` - Drift detectors + automation
- `validation/reports/` - Latest validation results

**Documentation:**
- `validation/README.md` - System overview
- `validation/FIRST_PRODUCTION_RUN_SUMMARY.md` - First run results
- `validation/DRIFT_SYNC_GUIDE.md` - Reference data sync workflow
- `validation/NEXT_STEPS.md` - Action items

**Next Steps:**
1. Run second validation to verify 99.8%+ score
2. Schedule weekly/monthly validation runs
3. Implement enhanced drift detection logic

---

### v1.3.3 - Phone/911 Dashboard Data Quality Fix (2026-02-04)
- **Problem**: Dashboard displayed "Phone/911" combined value (174,949 records, 31% of data) instead of separate "Phone" and "9-1-1" categories
- **Root Cause**: ArcGIS Pro Model Builder "Publish Call Data" tool had Calculate Field (2) with Arcade expression combining values
- **Investigation**: Created diagnostic ArcPy scripts, verified raw data had NO "Phone/911", traced to Model Builder transformation
- **Fix Applied**: Changed Arcade expression from `iif($feature.How_Reported=='9-1-1'||$feature.How_Reported=='Phone','Phone/911',...)` to `$feature.How_Reported`
- **Local Results**: ✅ 565,870 records processed | ✅ Zero "Phone/911" values | ✅ Phone: 109,569 (19.36%) | ✅ 9-1-1: 61,916 (10.94%)
- **CSV Export**: ✅ VERIFIED `CFSTable_2019_2026_FULL_20260203_231437.csv` (565,870 records, 167.53 MB) in `consolidation/output/`
  - Date range: 2019-01-01 to 2026-02-03 (7+ years, 2,590 days)
  - All 41 expected columns present
  - Zero "Phone/911" values confirmed in exported data
  - Phone and 9-1-1 properly separated (171,485 total records)
  - Only 16 null Call IDs (0.003% - negligible)
  - Quality verified via `verify_csv_export.py`
  - Ready for comprehensive validation
- **ArcGIS Online**: ⏳ Upload failed after 56 minutes (network timeout), needs retry during off-peak hours
- **RDP Export Process**: Export initially failed - geodatabase on RDP server cannot write to local OneDrive paths
  - Solution: Export to `C:\Temp` on RDP, then manual copy to local machine via RDP clipboard
  - File successfully transferred (167.53 MB) and verified
- **Additional Observations**: 2,000+ geocoding failures (NULL geometry), date conversion warnings, +4,131 record increase from baseline
- **Documentation**: Created SESSION_SUMMARY_PHONE911_FIX_20260203.txt, NEXT_ACTIONS_PHONE911_FIX.md, verify_csv_export.py, updated OPUS_BRIEFING_COMPREHENSIVE_VALIDATION.md
- **Timeline**: Complete investigation, fix, verification, and CSV export in 2 hours (9:48 PM - 11:30 PM)

### v1.3.1 - 2026 Monthly Data Fix (2026-02-02)
- **Fixed monthly file loading**: `run_full_consolidation()` now reads and loads monthly files from `config/consolidation_sources.yaml`; was only loading yearly files despite config entries.
- **Extended date range**: Changed `END_DATE` from `2026-01-30` to `2026-02-28` to allow February data inclusion.
- **Result**: Full consolidation now includes 753,903 records (was 714,689), date range 2019-01-01 to 2026-02-01 (was 2025-12-31).
- **Monthly files loaded**: 5 additional files (2025 Q4: Oct/Nov/Dec, 2026: Jan/Feb) plus 7 yearly files = 12 total files.
- **Processing time**: ~2 minutes for 12-file consolidation with parallel loading (8 workers).

### v1.2.6 - Incremental 2026 Run & Validation Fixes (2026-02-02)
- **Incremental consolidation**: Config uses 2026_01/02 CAD (and RMS) monthly paths; incremental mode uses only 2026 monthly files; January filtered by baseline IDs; February from 2026-02-01 onward. See `config/consolidation_sources.yaml` and `INCREMENTAL_RUN_GUIDE.md`.
- **Copy script**: `scripts/copy_polished_to_processed_and_update_manifest.py` copies latest polished Excel to 13_PROCESSED_DATA and updates manifest.json (for `copy_consolidated_dataset_to_server.ps1` and ArcGIS).
- **ReportNumberNew validation**: In `monthly_validation/scripts/validate_cad.py`, case-number column is forced to string on load and normalized (strip quotes, convert Excel numeric artifacts to YY-NNNNNN); regex pattern fallback when YAML pattern does not match; valid values like 26-000001 no longer flagged (quality score improved 68 → 93 for January CAD).

### ✅ Expansion Plan Complete

| Milestone | Description | Status |
|-----------|-------------|--------|
| 1. Paths & Baseline | 13_PROCESSED_DATA, baseline file, config sections | ✅ Complete |
| 2. Reports Reorganization | consolidation/reports/YYYY_MM_DD_* structure | ✅ Complete |
| 3. Server Copy + ArcPy | Update PowerShell to use manifest, add arcpy script | ✅ Complete |
| 4. Speed Optimizations | Parallel loading, chunked reads, incremental mode | ✅ Complete |
| 5. Monthly Processing | validate_cad.py, validate_rms.py, action items | ✅ Complete |
| 6. Legacy Archive | Move legacy projects to _Archive | ✅ Complete |

**Plan Reference:** `docs/Plan_Review_Package_For_Claude/CAD_RMS_Data_Quality_Expansion_Plan_ENHANCED.md`

---

## Directory Roles

| Directory | Purpose | Outputs |
|-----------|---------|---------|
| `config/` | Configuration files (schemas, validation rules, source paths) | YAML/JSON configs |
| `consolidation/` | Historical data consolidation scripts and outputs | `2019_2026_CAD_Consolidated.csv`, `2019_2026_CAD_ArcGIS_Ready.csv` |
| `consolidation/scripts/` | Consolidation and ArcGIS preparation scripts | N/A (executes workflows) |
| `consolidation/output/` | Consolidated datasets (715K records, 2019-2025) | CSV files |
| `consolidation/reports/` | Consolidation validation reports | HTML, Excel, JSON |
| `consolidation/logs/` | Consolidation processing logs | `*.log` |
| `monthly_validation/` | Ongoing monthly validation workflows | N/A |
| `monthly_validation/scripts/` | CAD/RMS validation CLI tools | N/A (executes workflows) |
| `monthly_validation/templates/` | HTML report templates | Jinja2 templates |
| `monthly_validation/reports/` | Monthly validation reports by date | `YYYY_MM_DD_*/` subdirectories |
| `monthly_validation/logs/` | Monthly validation logs | `*.log` |
| `shared/` | Shared utilities (validators, processors, reporting) | N/A (library code) |
| `shared/validators/` | Validation framework (pre-run, post-run, parallel validation, quality scoring) | N/A |
| `shared/processors/` | Processing logic (normalization, address standardization, datetime handling) | N/A |
| `shared/reporting/` | Report generators (HTML, Excel, JSON) | N/A |
| `shared/utils/` | Utilities (schema loader, hash utils, audit trail) | N/A |
| `tests/` | Pytest test suite with fixtures | N/A |
| `tests/fixtures/` | Sample data for testing | CSV/Excel samples |
| `docs/` | Documentation (architecture, migration notes, user guides) | Markdown files |
| `docs/arcgis/` | ArcGIS import scripts, automation, and backfill documentation | Python scripts, PowerShell, README, config |

---

## Processed Data Location (13_PROCESSED_DATA)

**Location:** `C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\`

This directory stores production-ready ESRI polished datasets **outside** the repo (large files excluded from git).

```
13_PROCESSED_DATA/
├── manifest.json                    # Latest file registry (READ THIS FIRST!)
├── README.md                        # Usage documentation
└── ESRI_Polished/
    ├── base/                        # Immutable baseline (724,794 records)
    │   └── CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx
    ├── incremental/                 # Incremental run outputs (YYYY_MM_DD_append/)
    └── full_rebuild/                # Full consolidation outputs (YYYY_MM_DD_full/)
```

### Baseline + Incremental Mode

**Purpose:** Avoid re-reading 7 years of data for each consolidation run.

**How it works:**
1. **Baseline file** contains 724,794 records (2019-01-01 to 2026-01-30)
2. Incremental runs load baseline once, then append only new monthly data
3. `manifest.json` tracks the latest polished file for scripts/server copy

**Configuration:** See `config/consolidation_sources.yaml` sections:
- `baseline` - Path, date range, record count
- `incremental` - Mode (append/full), dedup strategy
- `processed_data` - Root paths, manifest location

### Finding the Latest Polished File

```python
# Python
import json
from pathlib import Path
PROCESSED_ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA")
manifest = json.loads((PROCESSED_ROOT / "manifest.json").read_text())
latest_path = manifest["latest"]["full_path"]
record_count = manifest["latest"]["record_count"]
```

```powershell
# PowerShell
$manifest = Get-Content "C:\...\13_PROCESSED_DATA\manifest.json" | ConvertFrom-Json
$latestPath = $manifest.latest.full_path
```

---

## Key Entry Points

### Consolidation Workflow (Component 1)
Run from repo root:
```bash
# Historical consolidation (2019-2026, baseline + incremental)
python consolidate_cad_2019_2026.py

# After CAD_Data_Cleaning_Engine produces polished Excel: copy to 13_PROCESSED_DATA and update manifest
python scripts/copy_polished_to_processed_and_update_manifest.py
```
See `INCREMENTAL_RUN_GUIDE.md` for full order of operations (consolidate → cleaning engine → copy script).

### Monthly Validation Workflow (Component 2)
```bash
# Validate monthly CAD export
python monthly_validation/scripts/validate_cad.py --input "path/to/monthly_export.xlsx" --output "monthly_validation/reports/2026_02_01_cad/"

# Validate monthly RMS export
python monthly_validation/scripts/validate_rms.py --input "path/to/monthly_export.xlsx" --output "monthly_validation/reports/2026_02_01_rms/"
```

### Makefile Targets
```bash
make setup           # Install dependencies
make test            # Run pytest suite
make consolidate     # Run historical consolidation (2019-2026)
make validate-cad    # Validate monthly CAD export (requires INPUT=path)
make validate-rms    # Validate monthly RMS export (requires INPUT=path)
```

---

## Conventions

### Python & Environment
- **Python 3.9+** required
- Run all commands from **repo root**
- Dependencies managed via `requirements.txt` and `pyproject.toml`
- Use `pip install -r requirements.txt` to install

### Code Organization
- **Shared utilities** go in `shared/` (validators, processors, reporting, utils)
- **Consolidation scripts** go in `consolidation/scripts/`
- **Monthly validation scripts** go in `monthly_validation/scripts/`
- **Never duplicate code** - use shared utilities for common functionality

### Paths & Configuration
- **Always use config files** - Paths defined in `config/schemas.yaml`, `config/validation_rules.yaml`, `config/consolidation_sources.yaml`
- **Reference Standards** - Load schemas from `09_Reference/Standards` via `shared/utils/schema_loader.py` (do NOT duplicate)
- **No hardcoded paths** - Use config or relative paths
- Respect `.gitignore` (outputs, logs, large CSVs excluded)

### Code Quality
- Linting: `ruff check shared`
- Type checking: `mypy shared`
- Testing: `pytest`
- Run `make test` before committing

---

## Authoritative Sources

### Primary Schema Source: 09_Reference/Standards
**Location:** `C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Standards`  
**Version:** v2.3.0 (Updated: 2026-01-17)

**Key Files (Referenced, Not Copied):**
- `unified_data_dictionary/schemas/canonical_schema.json` - Master field definitions
- `unified_data_dictionary/schemas/cad_fields_schema_latest.json` - CAD field validation
- `unified_data_dictionary/schemas/rms_fields_schema_latest.json` - RMS field validation
- `CAD_RMS/DataDictionary/current/schema/cad_to_rms_field_map.json` - Field mappings
- `CAD_RMS/DataDictionary/current/schema/multi_column_matching_strategy.md` - Matching logic
- `mappings/field_mappings/mapping_rules.md` - ETL transformation rules (7 mapping types)
- `config/response_time_filters.json` - Response time calculation filters
- `mappings/call_types_*.csv` - 649 call types mapped to 11 ESRI categories

### Primary Logic Source: CAD_Data_Cleaning_Engine
**Location:** `C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine`  
**Status:** Active (Updated: Dec 2025)

**Extracted Components:**
- Validation framework (pre-run/post-run checks)
- Advanced Normalization Rules v3.2 (concatenated values, pattern-based normalization, default assignment)
- Parallel validation (26.7x performance gain via vectorization)
- RMS backfill logic (quality-scored selection, intelligent deduplication)
- Audit trail and file integrity checking (hash-based)

### Secondary Sources
- **RMS_Data_ETL**: Address standardization with `usaddress` library, USPS validation, reverse geocoding, fuzzy matching
- **RMS_Data_Processing**: Time artifact fixes (handles "1" values in time fields)
- **dv_doj**: Reporting templates and patterns

---

## Data and Safety

### Data Locations
- **CAD Source Files (2012-2025)**: `C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\yearly\`
- **CAD Monthly Files (2025 Q4)**: `C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\monthly\`
- **Note**: Directory structure updated to v2.0.0 (2026-01-30) - using canonical yearly/ path
- **Consolidated Outputs**: `consolidation/output/`
- **Monthly Validation Reports**: `monthly_validation/reports/`
- **Logs**: `consolidation/logs/`, `monthly_validation/logs/`

### Security Rules
- **Never commit PII or credentials**
- Case numbers, addresses, and demographic data are sensitive
- Do not expose sensitive data in logs, error messages, or public outputs
- Review staged files before committing
- Large CSV outputs are excluded via `.gitignore`

### Expected Data Volumes
- **Historical Consolidation**: 714,689 CAD records (2019-2025, 7 years)
- **Full History**: 1,401,462 CAD records (2012-2025, 14 years)
- **Unique Cases (2019-2025)**: ~543,000 after deduplication
- **Monthly Exports**: ~2,500-3,000 records per month
- **Quality Thresholds**: ≥95/100 for consolidated data, ≥80/100 for monthly exports
- **Note**: Records include all CAD events (incidents + supplements + unit records), not just incident reports

---

## Testing

### Test Files
- `tests/test_validators.py` - Validator unit tests
- `tests/test_processors.py` - Processor unit tests
- `tests/test_consolidation.py` - Integration tests for consolidation workflow
- `tests/test_schema_loader.py` - Schema loading tests
- `tests/fixtures/` - Sample data for testing

### Running Tests
```bash
pytest                              # Run all tests
pytest tests/test_validators.py -v # Run validator tests
pytest -v --cov=shared --cov-report=html  # Run with coverage
make test                           # Run all tests via Makefile
```

---

## Documentation & References

### Source of Truth Files
- **`README.md`** - Complete project overview, structure, data sources, validation rules
- **`CHANGELOG.md`** - Version history and release notes
- **`PLAN.md`** - Detailed implementation plan with architecture diagrams
- **`NEXT_STEPS.md`** - Phase-by-phase implementation guide with code templates

### User Guides (in `docs/`)
- `ARCHITECTURE.md` - System design and data flow diagrams
- `MIGRATION_NOTES.md` - What was extracted from legacy projects and why
- `CONSOLIDATION_GUIDE.md` - How to run historical consolidation
- `MONTHLY_VALIDATION_GUIDE.md` - How to automate monthly validation
- `STANDARDS_REFERENCE.md` - How to use 09_Reference/Standards schemas

---

## Project-Specific Rules

### 1. Schema Loading (CRITICAL)
- **ALWAYS** load schemas from `09_Reference/Standards` via `shared/utils/schema_loader.py`
- **NEVER** duplicate schema files - reference them from Standards directory
- Validate that schema paths exist before loading
- Use `config/schemas.yaml` to manage paths

### 2. Validation Framework
- Use **pre-run checks** before processing (environment, dependencies, file existence)
- Use **post-run checks** after processing (record counts, quality scores, outputs created)
- Apply **parallel validation** for performance (vectorized operations, bulk error logging)
- Generate **quality scores** (0-100 scale) for all datasets

### 3. Advanced Normalization Rules v3.2
- Handle concatenated values ("DispersedComplete" → "Dispersed")
- Apply pattern-based normalization (HowReported: "R" → "Radio", "P" → "Phone")
- Assign default values for 100% domain compliance
- See `shared/processors/field_normalizer.py`

### 4. Address Validation
- Apply USPS standardization using `usaddress` library
- Use reverse geocoding validation (if ArcGIS available)
- Apply fuzzy matching with ≥90% threshold
- Exclude Police HQ: "225 State Street"
- See `shared/processors/address_standardizer.py`

### 5. Multi-Column Matching Strategy
- **Primary Key Match**: `ReportNumberNew` ↔ `CaseNumber` (confidence 1.0)
- **Temporal + Address Match**: Date + Time + Address (confidence ≥0.85)
- **Officer + Temporal Match**: Officer + Date + Time (confidence ≥0.80)
- **Address + Zone + Date Match**: Address + Zone + Date (confidence ≥0.75)
- See `09_Reference/Standards/CAD_RMS/DataDictionary/current/schema/multi_column_matching_strategy.md`

### 6. Quality Scoring (0-100)
- **Required fields present**: 30 points
- **Valid formats**: 25 points
- **Address quality**: 20 points
- **Domain compliance**: 15 points
- **Consistency checks**: 10 points

### 7. Single Source-of-Truth
- Keep `README.md`, `CHANGELOG.md`, `PLAN.md`, and `NEXT_STEPS.md` as canonical documentation
- **Do NOT** create duplicate or variant documentation files
- Update existing files rather than creating new ones

---

## Validation Rules Reference

### Case Number Format
- Pattern: `^\d{2}-\d{6}([A-Z])?$`
- Examples: `25-000001`, `25-000001A` (supplemental)
- Must be non-null and preserved as text

### Call Type Categories (11 ESRI Categories)
1. Administrative and Support (122 types)
2. Assistance and Mutual Aid (21 types)
3. Community Engagement (20 types)
4. Criminal Incidents (201 types)
5. Emergency Response (33 types)
6. Investigations and Follow-Ups (44 types)
7. Juvenile-Related Incidents (16 types)
8. Public Safety and Welfare (85 types)
9. Regulatory and Ordinance (31 types)
10. Special Operations and Tactical (19 types)
11. Traffic and Motor Vehicle (57 types)

**Total:** 649 call types mapped

### Response Time Filters
**Exclude from Response Time Calculations:**
- HowReported: "Self-Initiated"
- Categories: Regulatory, Administrative, Investigations, Community Engagement
- Specific incidents: TAPS, Patrol Check, Traffic Detail, etc.
- See `09_Reference/Standards/config/response_time_filters.json`

---

## Workflows

### Historical Consolidation Pipeline (Component 1)
```
8 CAD files (2019-2026) → consolidate_cad.py → validation → normalization → 
quality scoring → 2019_2026_CAD_Consolidated.csv → prepare_arcgis.py → 
2019_2026_CAD_ArcGIS_Ready.csv
```

### Monthly Validation Pipeline (Component 2)
```
Monthly CAD/RMS export → validate_cad.py / validate_rms.py → 
pre-run checks → schema validation → field validation → quality scoring → 
anomaly detection → HTML/Excel/JSON reports
```

### Schema Loading Workflow
```
config/schemas.yaml → schema_loader.py → 09_Reference/Standards → 
load JSON/YAML schemas → return to validation/processing logic
```

---

## Common Commands Reference

```bash
# Setup
pip install -r requirements.txt
make setup

# Historical consolidation
python consolidation/scripts/consolidate_cad.py
python consolidation/scripts/prepare_arcgis.py

# Monthly validation
python monthly_validation/scripts/validate_cad.py --input "path/to/export.xlsx"
python monthly_validation/scripts/validate_rms.py --input "path/to/export.xlsx"

# Testing
pytest
pytest tests/test_validators.py -v
pytest --cov=shared --cov-report=html

# Quality assurance
make test
```

---

## When Working on This Project

### Before Starting
1. **Read EXTRACTION_REPORT.txt first** - Complete guide to Phase 2 (Python module extraction)
2. **Review README.md** - Current project status and Phase 1 completion
3. **Check CHANGELOG.md** - Latest changes (v1.0.1)
4. **Review NEXT_STEPS.md** - Phase-by-phase roadmap

### Phase 2: Extracting Python Modules from Chat Transcripts

**IMPORTANT:** The Python modules (~5000 lines total) are fully designed and production-ready in the chat export files. They should be extracted exactly as designed to preserve formatting, structure, and logic.

**Extraction Order** (Follow dependencies):
1. **schema_loader.py** (no dependencies) - Extract from `docs/Claude-Data_cleaning_project_implementation_roadmap/chunk_00001.txt`
2. **field_normalizer.py** (depends on schema_loader) - Extract from `chunk_00003.txt`  
3. **validation_engine.py** (depends on schema_loader) - Extract from `chunk_00006.txt`
4. **quality_scorer.py** (minimal dependencies) - Extract from `chunks 00008 & 00009.txt`
5. **consolidate_cad.py** (depends on ALL above) - Extract from `chunk_00009.txt` (FINALIZED version, not stub)
6. **run_consolidation.py** (depends on consolidate_cad) - Extract from `chunk_00010.txt`
7. **Makefile** - Extract from `chunk_00010.txt`

**Why Manual Extraction:**
- Files are extremely large (~5000 lines combined)
- Automated extraction risks token limits and truncation
- Manual extraction ensures complete code preservation
- Allows verification of each module before proceeding

**After Extraction:**
```powershell
# Create __init__.py files
New-Item -ItemType File shared/__init__.py, shared/utils/__init__.py, shared/processors/__init__.py, shared/validators/__init__.py, consolidation/__init__.py, consolidation/scripts/__init__.py

# Install dependencies
pip install -r requirements.txt

# Test imports
python -c "from shared.utils.schema_loader import ConfigLoader"
python -c "from shared.processors.field_normalizer import FieldNormalizer"

# Validate schemas
python -m shared.utils.schema_loader

# Run dry-run
python run_consolidation.py --dry-run --verbose
```

### During Development (After Phase 2 Complete)
1. **Use existing engines** - Don't duplicate logic from shared/
2. **Load schemas via schema_loader.py** - Never hardcode paths
3. **Follow the 6-step pipeline order** - Load → Normalize → Validate → Score → Deduplicate → Export
4. **Use config files for paths** - All paths in config/*.yaml
5. **Preserve original values when normalizing** - Use _raw_* columns

### Before Committing
1. **Run make lint** - Fix any issues
2. **Run make test** - All tests pass (when tests exist)
3. **Run python run_consolidation.py --dry-run** - Pipeline completes
4. **Update CHANGELOG.md** - Document significant changes
5. **Never commit PII** - Review outputs before committing

### Adding New Features
1. Check if existing engine can be extended
2. Add to shared/ if reusable across components
3. Add CLI interface for standalone usage
4. Add Makefile target if appropriate  
5. Update documentation (README.md, Claude.md)

---

## Configuration Files Reference

### config/schemas.yaml
Points to authoritative schemas in 09_Reference/Standards. Uses ${variable} expansion.
- `standards_root` - Base path to Standards directory
- `schemas` - JSON schema files (canonical, cad, rms, transformation)
- `mappings` - Field mapping files and call types
- `config` - Runtime configuration (response_time_filters)

### config/validation_rules.yaml
Validation patterns and quality scoring configuration.
- `case_number` - Format validation pattern
- `required_fields` - By data source (cad/rms)
- `address` - USPS validation, fuzzy matching, exclusions
- `domain_validation` - Valid values and normalization patterns
- `quality_scoring` - Weights and thresholds (0-100 scale)
- `anomaly_detection` - Variance and null rate thresholds
- `response_time_exclusions` - Filters for response time calculations

### config/consolidation_sources.yaml (v2.0.0)
Source file paths for 2019-2026 CAD consolidation. **Updated 2026-02-01** with baseline/incremental/performance sections.

**Source Configuration:**
- `sources.yearly` - Array of yearly CAD files with paths and expected counts
- `sources.monthly` - Monthly CAD files (2025 Q4, 2026)

**Baseline Configuration (NEW):**
- `baseline.enabled` - Enable baseline mode (true/false)
- `baseline.path` - Path to baseline polished file in 13_PROCESSED_DATA
- `baseline.date_range` - Start/end dates covered by baseline
- `baseline.record_count` - Expected record count for validation

**Incremental Configuration (NEW):**
- `incremental.enabled` - Enable incremental processing
- `incremental.mode` - "append" (add new records) or "full" (rebuild)
- `incremental.last_run_date` - Auto-updated after each run
- `incremental.dedup_strategy` - "keep_latest", "keep_first", or "keep_all_supplements"

**Performance Configuration (NEW):**
- `performance.parallel_loading.enabled` - Enable parallel Excel loading
- `performance.parallel_loading.max_workers` - Number of parallel workers (default: 8)
- `performance.chunked_reading.enabled` - Enable chunked reading for large files
- `performance.chunked_reading.threshold_mb` - Size threshold for chunked reads
- `performance.memory_optimization.use_categories` - Convert strings to categorical
- `performance.esri_generation.n_workers` - Workers for ESRI output generator

**Processed Data Configuration (NEW):**
- `processed_data.root` - Path to 13_PROCESSED_DATA
- `processed_data.esri_polished.base_dir` - Baseline file location
- `processed_data.esri_polished.incremental_dir` - Incremental outputs
- `processed_data.manifest_path` - Path to manifest.json

**Output/Validation:**
- `output` - Directory and filename configuration
- `validation` - Quality score thresholds, duplicate rate limits
- `metadata` - Config version, last updated, schema reference

---

## ArcGIS Pro Backfill Automation (v1.3.0)

### Overview
Automated workflow for backfilling ArcGIS Pro dashboard with polished CAD data, reducing manual process from 5+ hours to ~30 minutes.

### Core Strategy: Staging File Pattern
- ArcGIS Pro model reads from **fixed staging path**: `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx`
- For backfill: swap file content (not model nodes)
- Daily publish: scheduled task copies default export → staging before running tool
- Collision control: lock files prevent concurrent publishes

### Key Scripts (docs/arcgis/)

#### Tool Discovery
- **discover_tool_info.py** - Discovers exact ArcPy callable from toolbox
  - Confirmed: `arcpy.TransformCallData_tbx1()` from `LawEnforcementDataManagement.atbx`
  - Toolbox alias: `tbx1`
  - Run via: `propy.bat` (ArcGIS Pro Python environment)

#### Configuration
- **config.json** - Central configuration
  - Paths: ArcGIS project, toolbox, geodatabase, staging, backfill sources
  - Scheduled tasks: `LawSoftESRICADExport`, `LawSoftESRINIBRSExport`
  - Expected counts: Read from `13_PROCESSED_DATA/manifest.json`
  - Tool callable: `arcpy.TransformCallData_tbx1()`
  - Safe hours: 8 AM - 11 PM (avoid midnight scheduled tasks)

#### Orchestration
- **Invoke-CADBackfillPublish.ps1** - Main orchestrator
  - Pre-flight checks (lock, tasks, processes, geodatabase, sheet name)
  - Atomic swap: backfill → staging (with SHA256 hash verification)
  - Run publish: calls `run_publish_call_data.py` via propy.bat
  - Auto-restore: default export → staging (with size verification)
  - Lock file: metadata (PID, user, timestamp), stale detection (>2 hours)
  - Emergency restore: cleanup in finally block

- **run_publish_call_data.py** - Python runner
  - Reads config.json
  - Imports toolbox: `arcpy.ImportToolbox(toolbox_path, "tbx1")`
  - Calls: `arcpy.TransformCallData_tbx1()`
  - Captures geoprocessing messages
  - Returns exit code (0=success, 1=warnings, 2=errors)

#### Pre-Flight Checks
- **Test-PublishReadiness.ps1**
  - Lock file: Check existence + stale detection (auto-cleanup if process dead)
  - Scheduled tasks: Check if `LawSoftESRICADExport` or `LawSoftESRINIBRSExport` are running
  - Processes: Block if geoprocessing workers active (not just ArcGIS Pro open)
  - Geodatabase lock: Ensure `CAD_Data.gdb` writable
  - Excel validation: Verify "Sheet1" exists in backfill file
  - Disk space: >5 GB free required

#### File Copy
- **Copy-PolishedToServer.ps1** - Local machine → server
  - Reads `13_PROCESSED_DATA/manifest.json` for latest polished file
  - Robocopy with retry (3 attempts, 5s wait)
  - SMB share preferred (`\\HPD2022LAWSOFT\Share\`)
  - Admin share fallback (`\\HPD2022LAWSOFT\c$\`)
  - File integrity: size comparison after copy

### Backfill Workflow
1. **On local machine**: Run `Copy-PolishedToServer.ps1` to copy polished file to server
2. **On server (RDP)**: Run `Invoke-CADBackfillPublish.ps1 -BackfillFile "path" [-DryRun]`
3. **Verify**: Check dashboard date range and record counts

### One-Time Setup (Manual)
1. Create staging directory: `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\`
2. Copy 7 scripts from `docs/arcgis/` to `C:\HPD ESRI\04_Scripts\` on server
3. Update ArcGIS Pro model: Change Input Spreadsheet to `_STAGING\ESRI_CADExport.xlsx`
4. Update scheduled task: Add staging refresh (copy default → staging) as **FIRST** action in `LawSoftESRICADExport`

### Documentation
- **README_Backfill_Process.md** - Complete user guide with setup, workflow, troubleshooting

---

## When Working on This Project (Original)

1. **Read first** - Review `README.md`, `PLAN.md`, and `NEXT_STEPS.md` before making changes
2. **Use existing patterns** - Follow established code organization in `shared/`
3. **Reference Standards** - Load schemas from `09_Reference/Standards`, never duplicate
4. **Test your changes** - Run `pytest` or `make test`
5. **Document changes** - Update `CHANGELOG.md` for significant changes
6. **Respect data sensitivity** - Never expose PII or sensitive fields in logs/outputs
7. **Prefer edits over new files** - Modify existing scripts when possible
8. **Use config files** - Define paths in YAML configs, not hardcoded in scripts
9. **Follow validation framework** - Use pre-run checks, parallel validation, post-run checks
10. **Generate quality scores** - All datasets should have 0-100 quality scores

---

## Architecture Principles

1. **Reference, Don't Duplicate** - Schemas loaded from `09_Reference/Standards` (not copied)
2. **Single Source of Truth** - One authoritative location for validation rules and field definitions
3. **Modular Design** - Shared utilities reusable across consolidation and monthly validation
4. **Production-Ready** - Pre-run/post-run checks, audit trails, comprehensive logging
5. **Performance-Optimized** - Vectorized operations, parallel processing, quality scoring
6. **Configuration-Driven** - Paths, rules, and thresholds in YAML/JSON configs

---

## Legacy Projects (Archived)

These projects have been moved to `02_ETL_Scripts/_Archive/` (Milestone 6, 2026-02-02):

- **CAD_Data_Cleaning_Engine** - Validation framework, ESRI generator, normalization rules
- **Combined_CAD_RMS** - CAD+RMS matching logic, PowerBI/Excel dashboards
- **RMS_CAD_Combined_ETL** - Empty skeleton project (never developed)
- **RMS_Data_ETL** - Address standardization, ArcGIS deployment guides
- **RMS_Data_Processing** - Time artifact fixes, quality reporting

**Archive Location:** `C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\_Archive\`

See `_Archive/README.md` for detailed migration notes per project.

---

## Critical Lessons Learned (v1.5.1 - Feb 8, 2026)

### Column Name Format Requirements

**CRITICAL:** The ArcGIS Pro Model Builder "Publish Call Data" tool uses SQL WHERE clauses that expect **underscores** in column names, but the ESRI generator outputs **spaces**.

**Affected Columns:**
- `Time_Of_Call` (model) vs `Time of Call` (generator)
- `How_Reported` (model) vs `How Reported` (generator)

**Impact:** Model filter `"Time_Of_Call IS NOT NULL"` matches 0 rows when column is named `Time of Call`, causing complete dataset skip.

**Solution:**
1. **Corrected baseline file created:** `CAD_ESRI_Polished_Baseline_20190101_20260203_CORRECTED.xlsx`
2. **PowerShell script for correction:**
   ```powershell
   # Rename columns: spaces → underscores
   $columnRenames = @{
       "How Reported" = "How_Reported"
       "Time of Call" = "Time_Of_Call"
   }
   # Apply to baseline file before batch splitting
   ```

**Prevention:** Update ESRI generator to output underscores by default, or add column name validation to pre-flight checks.

### Monolithic Upload Failure Confirmed

**Observation:** Second attempt with corrected baseline still hung at ~564K features during geocoding phase.

**Confirmation:** This matches the findings in `BACKFILL_INVESTIGATION_20260205.md` exactly:
- Hang location: ~564,916 features
- Phase: Geocoding (live Esri World Geocoder)
- Symptoms: Silent hang, 0% CPU, no error logs
- Root cause: Network session exhaustion

**Conclusion:** Monolithic 754K upload approach is **not viable**. Staged backfill with 15 batches × 50K records is **mandatory**.

### Emergency Staging File Restoration

**Issue:** After Ctrl+C kill, staging file was still 74 MB baseline (should be 0.22 MB default export).

**Risk:** Scheduled task at 12:30 AM would have failed or published wrong data.

**Manual Fix Applied:**
```powershell
Copy-Item "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx" `
    -Destination "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx" -Force
```

**Improvement Needed:** Enhance `Invoke-CADBackfillPublish.ps1` to ensure restore happens even on Ctrl+C (trap signal, force restore in finally block).

### Dashboard Safety Verification

**Critical Finding:** Failed backfill attempts are **non-destructive**.

**Evidence:**
- Before: 561,739 records
- After failed attempts: 561,740 records (+1 test record only)
- Last record unchanged: 26-011287 (Feb 3, 2026)
- Date range unchanged
- Scheduled task ran successfully at 12:30 AM

**Lesson:** The "1 features were appended" message was from the Table Select test phase, not actual historical data upload. Dashboard remains safe during failures.

---

**Current Version:** 1.5.1 (Column Name Fix + Staged Backfill Ready)
**Created:** 2026-01-29  
**Last Updated:** 2026-02-09  
**Author:** R. A. Carucci  
**Status:** 🟡 v1.5.1 Preparation Complete | 🚀 Monday Morning Execution Ready

**v1.5.1 Preparation Summary (2026-02-08/09):**
- ✅ **Column Name Issue Identified** - ESRI generator outputs spaces, model expects underscores
- ✅ **Corrected Baseline Created** - Fixed `Time of Call` → `Time_Of_Call`, `How Reported` → `How_Reported`
- ✅ **Monolithic Upload Confirmed Failed** - Hang at 564K features during geocoding (consistent with investigation)
- ✅ **Server Configuration Fixed** - Geodatabase path corrected to `LawEnforcementDataManagement.gdb`
- ✅ **Dashboard Verified Safe** - 561,740 records intact after failed backfill attempt
- ✅ **Pre-Flight Checks Validated** - All 6 checks passing on server
- ✅ **Emergency Restoration Tested** - Staging file manually restored after Ctrl+C kill
- 📅 **Monday Ready** - Corrected baseline + staged backfill system deployment (90 min)

**New Scripts Created (8 total, 2,930 lines):**
1. `scripts/create_geocoding_cache.py` (302 lines) - Offline geocoding with quality gates
2. `scripts/split_baseline_into_batches.py` (309 lines) - Chronological batch splitter with SHA256
3. `scripts/Verify-BatchIntegrity.py` (334 lines) - Pre-deployment integrity verification
4. `docs/arcgis/Resume-CADBackfill.ps1` (305 lines) - Post-watchdog recovery with cleanup
5. `docs/arcgis/Validate-CADBackfillCount.py` (304 lines) - ArcGIS Online record count verification
6. `docs/arcgis/Rollback-CADBackfill.py` (324 lines) - Emergency truncation with WIPE confirmation
7. `docs/arcgis/Generate-BackfillReport.ps1` (284 lines) - Batch audit log generator
8. `docs/arcgis/Analyze-WatchdogHangs.ps1` (351 lines) - Hang diagnostics and cooling analysis

**Core Scripts Modified (3 total):**
1. `docs/arcgis/run_publish_call_data.py` - Heartbeat updates + marker detection + batch mode
2. `docs/arcgis/Invoke-CADBackfillPublish.ps1` - Watchdog monitoring loop + adaptive cooling + staged processing
3. `docs/arcgis/config.json` - Added `staged_backfill` configuration section

**Git Commit:** `5765607` - feat: implement 15-batch staged backfill system (2,930 lines added)

**Solution Architecture (Five Strategies):**
1. **Pre-Geocoding Cache** - Geocode ~100-200K unique addresses offline, eliminate network timeout
2. **Batch Processing** - 15 batches × 50K records with SHA256 integrity verification
3. **Heartbeat/Watchdog** - 5-minute timeout detection, auto-kill silent hangs
4. **Adaptive Cooling** - 60-120s delays based on network lag detection
5. **Post-Watchdog Recovery** - Automatic cleanup, marker restoration, resume capability

**Problem Being Solved:**
- **Issue**: Monolithic 754K record upload hangs at feature 564,916 after 75 minutes
- **Root Cause**: Network session exhaustion during live geocoding (Esri World Geocoder timeout)
- **Current Success Rate**: 0% (consistent hang, requires manual kill)
- **Proposed Success Rate**: 100% with automatic recovery

**Recent Completed Work:**
- ✅ Column name mismatch identified and fixed (v1.5.1) - Spaces → underscores
- ✅ Corrected baseline file generated (754K records, ready for staged backfill)
- ✅ Server configuration validated (geodatabase path, pre-flight checks)
- ✅ Dashboard safety verified (561,740 records intact after failed attempt)
- ✅ Comprehensive data quality validation system (v1.4.0) - 98.3% quality score
- ✅ Phone/911 dashboard fix verified (v1.3.3)
- ✅ February 2026 data inclusion (v1.3.2)
- ✅ ArcGIS automation workflow (v1.3.0)
- ✅ Backfill investigation documented (v1.3.4)

**Implementation Timeline:**
- **Feb 6 (2h 45m)**: Foundation work - geocoding, batching, testing (v1.5.0 released)
- **Feb 8 (4.5h)**: Backfill attempt, column name issue identified, corrected baseline created (v1.5.1 prep)
- **Weekend**: Data at rest, hash-verified, ready for Monday
- **Monday Feb 9 (1.5h)**: Execute full 15-batch staged backfill, validate, document (v1.5.1 release)

**Documentation Created:**
- `STAGED_BACKFILL_PLAN_FINAL.md` - Complete implementation guide
- `.cursor/plans/staged_backfill_implementation_99742877.plan.md` - Technical plan
- `BACKFILL_INVESTIGATION_20260205.md` - Root cause analysis
- `BACKFILL_PERFORMANCE_OPTIMIZATION_PLAN.md` - Strategic optimization goals
- `SESSION_SUMMARY_20260208_BACKFILL_ATTEMPT.md` - Column name fix session (4.5h)
- `MONDAY_MORNING_QUICK_START.md` - Step-by-step execution guide for Monday

**Key Innovation - Heartbeat/Watchdog System:**
```
Python Runner                    PowerShell Watchdog
-------------                    -------------------
update_heartbeat()         -->   Monitor every 30s
  (timestamp written)            
                                 if (age > 5 min):
Run ArcGIS Tool                    Kill process
  (may hang at 564916)             Clean staging
                                   Preserve batch
update_heartbeat()                 Enable resume
  (unreached if hung)
```

**Expected Results:**
- Completion Time: 30-45 minutes (vs 75-minute hang)
- Success Rate: 100% (vs 0%)
- Recovery Time: 5 minutes automatic (vs manual intervention)
- Batch Granularity: 50K records (vs 754K all-or-nothing)

---
