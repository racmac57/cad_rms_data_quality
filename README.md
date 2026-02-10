# CAD/RMS Data Quality System

**Version:** 1.6.0-dev (Historical Backfill XY Coordinate Strategy)
**Created:** 2026-01-29
**Updated:** 2026-02-09
**Author:** R. A. Carucci
**Status:** 🟡 v1.6.0 In Progress | Field mapping issue identified, simplified solution ready to test

---

## Project Overview

Unified data quality system for CAD (Computer-Aided Dispatch) and RMS (Records Management System) exports. This project consolidates best practices from multiple legacy systems and references authoritative schemas from `09_Reference/Standards`.

### Purpose

1. **Historical Consolidation** (Component 1): Merge 2019-2026 CAD data (754,409 records through Feb 3, 2026) into single validated dataset for ArcGIS Pro dashboards
2. **Monthly Validation** (Component 2): Provide reusable validation scripts for ongoing CAD and RMS exports
3. **Single Source of Truth**: Replace fragmented legacy projects with unified, maintainable system
4. **Historical Backfill** (Component 3): Load 565,870 records to ArcGIS Online dashboard using XY coordinates (bypassing live geocoding)

---

## Current Initiative: Historical Backfill XY Coordinate Strategy (v1.6.0-dev)

### The Challenge

**Problem 1: Live Geocoding Timeouts**
- ModelBuilder's "Geocode Addresses" tool hung indefinitely at feature 564,897
- Network session timeout during bulk geocoding (>100K records)
- Process stuck for >5 minutes with no progress

**Problem 2: Field Schema Mismatch**
- Source Excel fields (ReportNumberNew, Incident) don't match online service fields (callid, calltype)
- ArcPy FieldMappings API failed to transfer attributes
- Result: 565,870 records with geometry but all attributes NULL

### The Solution

**Two-Part Strategy:**

1. **Bypass Live Geocoding** - Use existing latitude/longitude fields with XYTableToPoint instead of geocoding service
2. **Field Copying Instead of Mapping** - Create duplicate fields with target names, copy values directly (avoid FieldMappings API)

### Implementation Status

**✅ COMPLETED:**
- ✅ Backup/restore system (561,740 records backed up successfully)
- ✅ XYTableToPoint geometry creation (565,870 points created)
- ✅ DateTime transformations (Time_Of_Call → calldate working)
- ✅ Response time calculations (dispatchtime, queuetime, cleartime, responsetime)
- ✅ Date attribute extraction (day of week, hour, month, year)
- ✅ Root cause identified (FieldMappings API failure)

**🟡 PENDING:**
- 🟡 Test simplified field copying approach (`complete_backfill_simplified.py`)
- 🟡 Validate dashboard attribute data after final run
- 🟡 Investigate date range discrepancy (2019-2026 source vs 2023-2026 online)

### Scripts Created (Feb 9, 2026 Session)

**Backup & Restore (Working):**
1. `scripts/backup_current_layer.py` - Export online layer to local FGDB
2. `scripts/truncate_online_layer.py` - Delete all records (triple confirmation)
3. `scripts/restore_from_backup.py` - Emergency rollback operation

**Backfill Workflow Evolution:**
4. `scripts/publish_with_xy_coordinates.py` ❌ - Basic XY approach (NULL attributes)
5. `scripts/complete_backfill_with_xy.py` ❌ - Added transformations (partial success)
6. `scripts/complete_backfill_fixed.py` ❌ - FieldMappings attempt (failed)
7. `scripts/complete_backfill_simplified.py` 🟡 - Field copying approach (ready to test)

**Diagnostics (Working):**
8. `scripts/diagnose_missing_data.py` - Check for NULL attributes
9. `scripts/check_cfstable_schema.py` - Display CFStable field schema
10. `scripts/check_temp_fc_fields.py` - Verify temp FC fields after XYTableToPoint
11. `scripts/verify_data_exists.py` - Sample record values

### Documentation

- `docs/HANDOFF_20260209.md` (620 lines) - Complete technical handoff with timeline, root causes, script evolution
- `CHANGELOG.md` - Updated with v1.6.0 changes

---

## Previous Initiative: Staged Backfill System (v1.5.0)

### The Challenge

**Problem:** Monolithic 754K record upload to ArcGIS Online consistently hangs at feature 564,916
- Duration: 75+ minutes before hang
- CPU Activity: Drops to 0% (silent hang)
- Error Logs: None (network session timeout)
- Success Rate: 0%

### The Solution

**Five-Strategy Staged Backfill** developed with Gemini AI:

1. **Pre-Geocoding Cache** - Geocode ~100-200K unique addresses offline once, eliminating live geocoding network timeout risk
2. **Batch Processing** - Split 754K into 15 batches of 50K records with SHA256 hash verification
3. **Heartbeat/Watchdog** - Python updates timestamp, PowerShell monitors, auto-kills after 5 min freeze
4. **Adaptive Cooling** - 60s default, extends to 120s if network lag detected
5. **Post-Watchdog Recovery** - Automatic cleanup of stale files, marker restoration, immediate resume

### Implementation Status

**✅ IMPLEMENTATION COMPLETE (Feb 6, 2026)**
- ✅ All 8 auxiliary scripts created (2,930 lines)
- ✅ Core scripts modified with watchdog monitoring
- ✅ Local integrity verified: 754,409 records, 16 batches, 100% pass
- ✅ SHA256 hashes confirmed, manifest synchronized
- ✅ Geocoding cache: 97.6% address deduplication
- ✅ Quality gates passed: <5% geocoding failure
- ✅ Git commit `5765607` completed
- 🚀 System ready for Monday deployment

**Monday (Feb 9, 1 hour):**
- 2-batch proof of concept (15 min)
- Full 15-batch backfill (45 min)
- Validation and audit (15 min)

### Scripts Created (Commit 5765607)

**Phase 0 - Local Preparation:**
1. `scripts/create_geocoding_cache.py` (302 lines) - Offline geocoding with quality gates
2. `scripts/split_baseline_into_batches.py` (309 lines) - Chronological batch splitter with SHA256
3. `scripts/Verify-BatchIntegrity.py` (334 lines) - Pre-weekend lockdown verification

**Phase 1 - Server Execution:**
4. `docs/arcgis/Resume-CADBackfill.ps1` (305 lines) - Post-watchdog recovery with cleanup
5. `docs/arcgis/Validate-CADBackfillCount.py` (304 lines) - ArcGIS Online record count verification
6. `docs/arcgis/Rollback-CADBackfill.py` (324 lines) - Emergency truncation with WIPE confirmation
7. `docs/arcgis/Generate-BackfillReport.ps1` (284 lines) - Batch audit log generator
8. `docs/arcgis/Analyze-WatchdogHangs.ps1` (351 lines) - Hang diagnostics and cooling analysis

**Modified Core Scripts:**
1. `docs/arcgis/run_publish_call_data.py` - Heartbeat updates + marker detection + batch mode
2. `docs/arcgis/Invoke-CADBackfillPublish.ps1` - Watchdog monitoring + adaptive cooling + staged processing
3. `docs/arcgis/config.json` - Added `staged_backfill` configuration section

### Documentation

- `STAGED_BACKFILL_PLAN_FINAL.md` - Complete implementation guide
- `.cursor/plans/staged_backfill_implementation_99742877.plan.md` - Technical details

---

## What Changed in v1.5.0

Released **2026-02-06** - [View full changelog](CHANGELOG.md#150---2026-02-06)

**Major Feature:** Staged Backfill System with Heartbeat/Watchdog Monitoring

This release resolves the critical 564,916 record hang issue that prevented successful upload of 754K historical CAD records to ArcGIS Online. The solution implements:

- **8 new auxiliary scripts** (2,930 lines) for batch processing, monitoring, recovery, and diagnostics
- **Pre-geocoding cache** that eliminates live geocoding network timeouts (97.6% address deduplication)
- **Heartbeat/watchdog system** that automatically detects and kills hung processes after 5 minutes
- **Batch processing** splits 754K records into 15 manageable chunks with SHA256 verification
- **Adaptive cooling** extends delays from 60s to 120s when network lag detected
- **Automatic recovery** with checkpoint tracking and stale file cleanup

**Performance:** Expected 30-45 minute completion (vs 75+ minute hang), 100% success rate with automatic recovery (vs 0% success rate).

**Configuration fixes:** Corrected PowerShell paths, removed hardcoded commit messages, added `.claude/` to gitignore.

---

## Project Structure

```
cad_rms_data_quality/
├── README.md                    # This file
├── CHANGELOG.md                 # Version history
├── INCREMENTAL_RUN_GUIDE.md    # Incremental CAD run + copy to 13_PROCESSED_DATA ✅
├── PLAN.md                      # Detailed implementation plan
├── NEXT_STEPS.md               # Roadmap for next session
├── requirements.txt            # Python dependencies ✅
├── pyproject.toml              # Project configuration ✅
├── Makefile                    # Automation commands (TO DO - in chunk_00010.txt)
├── .gitignore                  # Git ignore rules ✅
├── consolidate_cad_2019_2026.py # Production consolidation (baseline + incremental) ✅
├── scripts/                    # Post-consolidation utilities ✅
│   └── copy_polished_to_processed_and_update_manifest.py  # Copy to 13_PROCESSED_DATA, update manifest
│
├── config/                     # Configuration files ✅
│   ├── schemas.yaml            # Paths to 09_Reference/Standards schemas ✅
│   ├── validation_rules.yaml  # Validation configuration ✅
│   └── consolidation_sources.yaml  # 2019-2025 CAD file paths (actual: 714K records) ✅
│
├── consolidation/              # Component 1: Historical data consolidation
│   ├── scripts/
│   │   ├── consolidate_cad.py         # Merge 2019-2025 CAD files (714K records) (TO DO)
│   │   └── prepare_arcgis.py          # Create ArcGIS-ready output (TO DO)
│   ├── output/                        # Consolidated datasets (empty)
│   ├── reports/                       # Validation reports (empty)
│   └── logs/                          # Processing logs (empty)
│
├── monthly_validation/         # Component 2: Ongoing validation ✅
│   ├── scripts/
│   │   ├── validate_cad.py            # Monthly CAD validator ✅
│   │   └── validate_rms.py            # Monthly RMS validator ✅
│   ├── templates/
│   │   └── validation_report_template.html  # Report template (TO DO)
│   ├── processed/                     # Processed monthly outputs ✅
│   ├── reports/                       # Monthly reports (YYYY_MM_cad/, YYYY_MM_rms/) ✅
│   └── logs/                          # Validation logs
│
├── shared/                     # Shared utilities (refactored from legacy projects)
│   ├── validators/
│   │   ├── validation_engine.py       # Core validation framework (TO DO)
│   │   ├── pre_run_checks.py          # Pre-run environment checks (TO DO)
│   │   ├── post_run_checks.py         # Post-run quality checks (TO DO)
│   │   ├── address_validator.py       # Address validation (TO DO)
│   │   ├── case_number_validator.py   # Case number validation (TO DO)
│   │   └── quality_scorer.py          # 0-100 quality scoring (TO DO)
│   ├── processors/
│   │   ├── field_normalizer.py        # Advanced Normalization v3.2 (TO DO)
│   │   ├── datetime_processor.py      # Time artifact fixes (TO DO)
│   │   └── address_standardizer.py    # USPS standardization (TO DO)
│   ├── reporting/
│   │   ├── html_generator.py          # HTML report generation (TO DO)
│   │   ├── excel_generator.py         # Excel report generation (TO DO)
│   │   └── json_generator.py          # JSON metrics export (TO DO)
│   └── utils/
│       ├── schema_loader.py           # Load schemas from Standards (TO DO)
│       ├── hash_utils.py              # File integrity checks (TO DO)
│       └── audit_trail.py             # Change tracking (TO DO)
│
├── tests/                      # Test suite
│   ├── test_validators.py             # Validator tests (TO DO)
│   ├── test_processors.py             # Processor tests (TO DO)
│   ├── test_consolidation.py          # Consolidation tests (TO DO)
│   └── fixtures/                      # Test data (empty)
│
└── docs/                       # Documentation
    ├── arcgis/                        # ArcGIS import and automation ✅
    │   ├── README.md                  # Workflow guide for geodatabase import ✅
    │   ├── README_Backfill_Process.md # User guide for backfill automation ✅
    │   ├── config.json                # Central configuration for backfill workflow ✅
    │   ├── discover_tool_info.py      # Tool discovery script ✅
    │   ├── run_publish_call_data.py   # Python runner for ArcGIS Pro tool ✅
    │   ├── Test-PublishReadiness.ps1  # Pre-flight checks ✅
    │   ├── Invoke-CADBackfillPublish.ps1  # Main orchestrator ✅
    │   ├── Copy-PolishedToServer.ps1  # Robust file copy script ✅
    │   └── import_cad_polished_to_geodatabase.py  # Legacy arcpy import script
    ├── ARCHITECTURE.md                # System design (TO DO)
    ├── MIGRATION_NOTES.md             # What came from legacy projects (TO DO)
    ├── CONSOLIDATION_GUIDE.md         # How to run consolidation (TO DO)
    ├── MONTHLY_VALIDATION_GUIDE.md    # How to run monthly validation (TO DO)
    └── STANDARDS_REFERENCE.md         # How to use 09_Reference/Standards (TO DO)
```

---

## Authoritative Sources

### Primary Schema Source: 09_Reference/Standards
**Location:** `C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Standards`  
**Version:** v2.3.0 (Updated: 2026-01-17)

**Key Files:**
- `unified_data_dictionary/schemas/canonical_schema.json` - Master field definitions
- `unified_data_dictionary/schemas/cad_fields_schema_latest.json` - CAD field validation
- `unified_data_dictionary/schemas/rms_fields_schema_latest.json` - RMS field validation
- `CAD_RMS/DataDictionary/current/schema/cad_to_rms_field_map.json` - Field mappings
- `CAD_RMS/DataDictionary/current/schema/multi_column_matching_strategy.md` - Matching logic
- `mappings/field_mappings/mapping_rules.md` - ETL transformation rules
- `config/response_time_filters.json` - Response time calculation filters

### Primary Logic Source: CAD_Data_Cleaning_Engine
**Location:** `C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine`  
**Status:** Active (Last updated: Dec 2025)

**Key Components to Migrate:**
- Validation framework (pre-run/post-run checks)
- Advanced Normalization Rules v3.2
- Parallel validation (26.7x performance improvement)
- RMS backfill logic with intelligent deduplication
- Audit trail and file integrity checking

### Secondary Sources (Specific Features)
- `RMS_Data_ETL`: Address standardization with `usaddress` library
- `RMS_Data_Processing`: Time artifact fixes
- `dv_doj`: Reporting templates and patterns

---

## Data Sources for Consolidation

### CAD Files (2012-2025)
**Base Directory:** `C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\yearly\`  
**Structure:** Canonical v2.0.0 (Updated: 2026-01-30)

**Yearly Source Files:**
1. **2012**: `yearly\2012\2012_CAD_ALL.xlsx` (~30,000 records)
2. **2013**: `yearly\2013\2013_CAD_ALL.xlsx` (~32,000 records)
3. **2014**: `yearly\2014\2014_CAD_ALL.xlsx` (~35,000 records)
4. **2015**: `yearly\2015\2015_CAD_ALL.xlsx` (~35,000 records)
5. **2016**: `yearly\2016\2016_CAD_ALL.xlsx` (~35,000 records)
6. **2017**: `yearly\2017\2017_CAD_ALL.xlsx` (~38,000 records)
7. **2018**: `yearly\2018\2018_CAD_ALL.xlsx` (~35,000 records)
8. **2019**: `yearly\2019\2019_CAD_ALL.xlsx` (~33,000 records)
9. **2020**: `yearly\2020\2020_CAD_ALL.xlsx` (~32,000 records)
10. **2021**: `yearly\2021\2021_CAD_ALL.xlsx` (~33,000 records)
11. **2022**: `yearly\2022\2022_CAD_ALL.xlsx` (~38,000 records)
12. **2023**: `yearly\2023\2023_CAD_ALL.xlsx` (~40,000 records)
13. **2024**: `yearly\2024\2024_CAD_ALL.xlsx` (~40,000 records)
14. **2025**: `yearly\2025\2025_CAD_ALL.xlsx` (~42,000 records)

**Monthly Source Files (2025 Q4 & 2026):**
- `monthly\2025\2025_10_CAD.xlsx`, `2025_11_CAD.xlsx`, `2025_12_CAD.xlsx`
- `monthly\2026\2026_01_CAD.xlsx`, `2026_02_CAD.xlsx` (incremental: Jan filtered by baseline IDs, Feb from 2026-02-01)

**Actual Records (Verified 2026-01-30):** 714,689 records (2019-2025, 7 years)  
**Unique Cases:** ~540,000 estimated after deduplication  
**Full History:** 1,401,462 total records (2012-2025, 14 years)

**Note:** Configuration updated to canonical structure (2026-01-30).  
**Important:** Actual records are ~3.3x higher than initial estimates due to inclusion of supplemental reports, unit records, and status updates (not just incidents).

### CAD Data Coverage by Year

| Year | Total Records | Unique Cases | Coverage |
|------|---------------|--------------|----------|
| 2012 | 85,234 | ~65,000 | Historical |
| 2013 | 92,643 | ~70,000 | Historical |
| 2014 | 103,840 | ~79,000 | Historical |
| 2015 | 98,962 | ~75,000 | Historical |
| 2016 | 98,795 | ~75,000 | Historical |
| 2017 | 108,543 | ~83,000 | Historical |
| 2018 | 98,756 | ~75,000 | Historical |
| **2019** | **91,217** | **~69,000** | **Consolidation Target** |
| **2020** | **89,400** | **~68,000** | **Consolidation Target** |
| **2021** | **91,477** | **~70,000** | **Consolidation Target** |
| **2022** | **105,038** | **~80,000** | **Consolidation Target** |
| **2023** | **113,179** | **~86,000** | **Consolidation Target** |
| **2024** | **110,313** | **~84,000** | **Consolidation Target** |
| **2025** | **114,065** | **~87,000** | **Consolidation Target** |
| | | | |
| **2019-2025 Total** | **714,689** | **~543,000** | **Primary Target** |
| **2012-2025 Total** | **1,401,462** | **~1,071,000** | **Full History** |

**Data Source Files:**
- `yearly/2012/2012_CAD_ALL.xlsx` through `yearly/2025/2025_CAD_ALL.xlsx`
- `monthly/2025/2025_10_CAD.xlsx`, `2025_11_CAD.xlsx`, `2025_12_CAD.xlsx`

---

## Key Validation Rules (from Standards)

### Case Number Format
- Pattern: `^\d{2}-\d{6}([A-Z])?$`
- Examples: `25-000001`, `25-000001A` (supplemental)
- Must be preserved as text (not numeric). Monthly validation (`validate_cad.py`) forces ReportNumberNew to string on load and normalizes Excel artifacts (e.g. `26000001.0` → `26-000001`) before validation; see CHANGELOG v1.2.6.

### Address Validation
- USPS standardization using `usaddress` library
- Reverse geocoding validation (if ArcGIS available)
- Fuzzy matching ≥90% threshold
- Exclude Police HQ: "225 State Street"

### Call Type Classification
- 649 call types mapped to 11 ESRI categories
- Source: `09_Reference/Standards/mappings/call_types_*.csv`
- Categories: Criminal Incidents, Emergency Response, Traffic, etc.

### Quality Scoring (0-100)
- Required fields present: 30 points
- Valid formats: 25 points
- Address quality: 20 points
- Domain compliance: 15 points
- Consistency checks: 10 points

---

## What changed in v1.3.1

- **Fixed 2026 monthly data inclusion**: Full consolidation now loads all monthly files from config (was only loading yearly files)
- **Extended date range**: Changed `END_DATE` from `2026-01-30` to `2026-02-28` to include February data
- **Updated totals**: 753,903 records (was 714,689), date range now 2019-01-01 to 2026-02-01 (was 2025-12-31)
- **Monthly files loaded**: Now includes 5 monthly files (2025 Q4 + 2026 Jan/Feb) in addition to 7 yearly files
- **Processing time**: ~2 minutes for full consolidation with 12 files using parallel loading

See [CHANGELOG.md](CHANGELOG.md#131---2026-02-02) for full details.

---

## What changed in v1.3.0

- **ArcGIS Pro backfill automation**: Complete workflow automation reducing manual steps from 5+ hours to 30 minutes
- **Staging pattern implemented**: Model reads from fixed path; only file content swaps (no more model editing)
- **Collision control**: Lock files, scheduled task checks, stale lock detection prevent concurrent publishes
- **Tool discovery**: Created discovery script, confirmed callable `arcpy.TransformCallData_tbx1()` 
- **Orchestration scripts**: Main orchestrator with atomic swaps, SHA256 verification, auto-restore on error
- **Pre-flight checks**: Lock files, task status, process check, geodatabase lock, Excel sheet validation
- **Documentation**: Complete user guide with setup, workflow, troubleshooting, configuration reference

See [CHANGELOG.md](CHANGELOG.md#130---2026-02-02) for full details.

---

## What changed in v1.2.6

- **Incremental 2026 run**: Config uses 2026_01/02 CAD and RMS monthly paths; copy script updates 13_PROCESSED_DATA and manifest.
- **ReportNumberNew and CaseNumber fix**: CAD and RMS validators force case-number column to string and normalize Excel artifacts; quality scores improved.
- **SCRPA-style quality reports**: Shared report builder; context-aware text (CAD or RMS only); data-driven "In this run" causes; report folders YYYY_MM_cad/rms.
- **RMS export alignment**: Required fields and mappings use Case Number, FullAddress, Zone (not Location, PDZone, OffenseCode); Standards updated.
- **QUALITY_REPORTS_REFERENCE.md**: Field names CAD vs RMS; score categories and consistency checks explained.

See [CHANGELOG.md](CHANGELOG.md#126---2026-02-02) for full details.

---

## What changed in v1.2.5

- **Expansion Plan complete**: All 6 milestones done (paths and baseline, reports, server copy and ArcPy, speed optimizations, monthly processing, legacy archive).
- **Legacy projects archived**: Five projects moved to `02_ETL_Scripts/_Archive/` with README; cad_rms_data_quality is the single active project.
- **Version sync**: pyproject.toml version aligned to 1.2.5.

See [CHANGELOG.md](CHANGELOG.md#125---2026-02-02) for full details.

---

## What Changed in v1.1.0

### Consolidation Implementation Complete
- **Production Script**: `consolidate_cad_2019_2026.py` operational, successfully processed 716,420 records (2019-2026)
- **ESRI Output**: Automated pipeline with RMS backfill (41,137 PDZone values) and Advanced Normalization v3.2
- **Quality Metrics**: 99.9% field completeness, 100% domain compliance
- **Validation Analysis**: Comprehensive gap analysis with solutions mapped to 09_Reference/Standards
- **Call Type Normalizer**: Created `shared/utils/call_type_normalizer.py` for runtime validation
- **Backup System**: Implemented `backups/YYYY_MM_DD/` structure with tracking logs

See [CHANGELOG.md](CHANGELOG.md#110---2026-01-31) for complete details.

---

## Development Status

### ✅ Phase 1: Consolidation Operational (2026-01-31)
- [x] Project directory structure created
- [x] README.md, CHANGELOG.md, PLAN.md, NEXT_STEPS.md, Claude.md, SUMMARY.md
- [x] **config/schemas.yaml** - Paths to 09_Reference/Standards
- [x] **config/validation_rules.yaml** - Validation patterns and quality scoring
- [x] **config/consolidation_sources.yaml** - 2019-2025 CAD source files (actual: 714K records)
- [x] **config/rms_sources.yaml** - RMS source files
- [x] **requirements.txt** - Python dependencies (pandas, pyyaml, usaddress, etc.)
- [x] **pyproject.toml** - Project metadata and build configuration
- [x] **.gitignore** - Git exclusion rules
- [x] **consolidate_cad_2019_2026.py** - Production consolidation script
- [x] **shared/utils/call_type_normalizer.py** - Runtime normalization utility
- [x] Integrated with CAD_Data_Cleaning_Engine for ESRI output generation
- [x] Validation framework analysis complete
- [x] Record count verification complete (716,420 records)

### ✅ Phase 2: Comprehensive Validation System (COMPLETE - 2026-02-04)
- [x] Built 9 field validators covering all critical CAD fields
- [x] Built 2 drift detectors for reference data monitoring
- [x] Created master orchestrator for single-command validation
- [x] First production run: 98.3% quality score on 754,409 records
- [x] Fixed disposition field validation (eliminated 87,896 false positives)
- [x] Synced reference data (823 call types, 387 personnel)
- [x] Created automated drift sync tools

**See:** `validation/` directory for complete documentation and tools.

---

## Quick Start

### Installation
```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
pip install -r requirements.txt
```

### Run Historical Consolidation (Operational)
```powershell
# Consolidate 2019-2026 CAD data
python consolidate_cad_2019_2026.py

# Generate ESRI output (run in CAD_Data_Cleaning_Engine)
cd ../CAD_Data_Cleaning_Engine
python scripts/enhanced_esri_output_generator.py \
  --input "data/01_raw/2019_to_2026_01_30_CAD.csv" \
  --output-dir "data/03_final" \
  --format excel

# Validate output
python scripts/validation/validate_esri_polished_dataset.py \
  --input "data/03_final/CAD_ESRI_POLISHED_[timestamp].xlsx"

# Copy polished file to 13_PROCESSED_DATA and update manifest (from cad_rms_data_quality repo)
cd ../cad_rms_data_quality
python scripts/copy_polished_to_processed_and_update_manifest.py
```

For incremental runs (baseline + new monthly only), see **INCREMENTAL_RUN_GUIDE.md**.

### Run Monthly Validation
```powershell
# CAD monthly export
python monthly_validation/scripts/validate_cad.py --input "path/to/monthly_export.xlsx" --output "monthly_validation/reports/YYYY_MM_cad"

# RMS monthly export
python monthly_validation/scripts/validate_rms.py --input "path/to/monthly_export.xlsx" --output "monthly_validation/reports/YYYY_MM_rms"
```

See `outputs/consolidation/CAD_CONSOLIDATION_EXECUTION_GUIDE.txt` and `INCREMENTAL_RUN_GUIDE.md` for detailed instructions.

---

## Architecture Principles

1. **Reference, Don't Duplicate**: Schemas loaded from `09_Reference/Standards` (not copied)
2. **Single Source of Truth**: One authoritative location for validation rules and field definitions
3. **Modular Design**: Shared utilities reusable across consolidation and monthly validation
4. **Production-Ready**: Pre-run/post-run checks, audit trails, comprehensive logging
5. **Performance-Optimized**: Vectorized operations, parallel processing, quality scoring
6. **Baseline + Incremental**: Load baseline once, append new monthly data only (skip re-reading 7 years)

---

## Processed Data Location (13_PROCESSED_DATA)

**Location:** `C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\`

Production-ready ESRI polished datasets are stored here:

```
13_PROCESSED_DATA/
├── manifest.json                    # Latest file registry (read this first!)
├── README.md                        # Usage documentation
└── ESRI_Polished/
    ├── base/                        # Immutable baseline (724,794 records)
    │   └── CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx
    ├── incremental/                 # Incremental run outputs
    │   └── YYYY_MM_DD_append/
    └── full_rebuild/                # Full consolidation outputs
```

### Finding the Latest File
```powershell
# PowerShell: Read manifest.json
$manifest = Get-Content "C:\...\13_PROCESSED_DATA\manifest.json" | ConvertFrom-Json
$latestPath = $manifest.latest.full_path
Write-Host "Latest: $latestPath ($($manifest.latest.record_count) records)"
```

### Baseline Dataset
- **File:** `CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx`
- **Records:** 724,794 | **Unique cases:** 559,202
- **Date range:** 2019-01-01 to 2026-01-30
- **Created:** 2026-01-31

Incremental runs load this baseline and append only new monthly data, avoiding re-processing 7 years of records

---

## Related Projects

- **dv_doj**: Domestic violence analysis project (active)
- **CAD_Data_Cleaning_Engine**: Source of validation framework (active, retained as reference)
- **09_Reference/Standards**: Authoritative schemas and mappings (active)
- **_ARCHIVED_2026_01_30/**: Legacy projects (to be archived after migration)

---

## License

Internal use - City of Hackensack Police Department

---

## Contact

**Author:** R. A. Carucci  
**Department:** City of Hackensack Police Department  
**Created:** January 29, 2026

---

## Change Log

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## Next Steps

See [NEXT_STEPS.md](NEXT_STEPS.md) for detailed roadmap and implementation checklist.
