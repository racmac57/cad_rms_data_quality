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

### 🚧 Expansion Plan Milestones 4-6 (In Progress)

| Milestone | Description | Status |
|-----------|-------------|--------|
| 1. Paths & Baseline | 13_PROCESSED_DATA, baseline file, config sections | ✅ Complete |
| 2. Reports Reorganization | consolidation/reports/YYYY_MM_DD_* structure | ✅ Complete |
| 3. Server Copy + ArcPy | Update PowerShell to use manifest, add arcpy script | ✅ Complete |
| 4. Speed Optimizations | Parallel loading, chunked reads, incremental mode | 🔜 Next |
| 5. Monthly Processing | validate_cad.py, validate_rms.py, action items | 🔜 Pending |
| 6. Legacy Archive | Move legacy projects to _Archive | 🔜 Pending |

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
| `docs/arcgis/` | ArcGIS import scripts and documentation | Python scripts, README |

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
# Historical consolidation (2019-2026)
python consolidation/scripts/consolidate_cad.py

# Prepare ArcGIS-ready dataset
python consolidation/scripts/prepare_arcgis.py
```

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

These projects were analyzed and valuable components migrated to this unified system:

- **CAD_Data_Cleaning_Engine** - Validation framework, normalization rules (retained as reference)
- **RMS_Data_ETL** - Address standardization (archived after migration)
- **RMS_Data_Processing** - Time artifact fixes (archived after migration)
- **RMS_CAD_Combined_ETL** - Empty skeleton (deleted)

See `docs/MIGRATION_NOTES.md` for complete migration details.

---

## Version Information

**Current Version:** 1.2.2 (Expansion Plan - Milestone 3 Complete)
**Created:** 2026-01-29
**Last Updated:** 2026-02-01
**Author:** R. A. Carucci
**Status:** Server Copy + ArcPy Complete - 724,794 Records in Production

**Current Phase:** Expansion Plan Implementation (6 Milestones)
- ✅ Milestone 1: Paths & Baseline (Complete)
- ✅ Milestone 2: Reports Reorganization (Complete)
- ✅ Milestone 3: Server Copy + ArcPy (Complete)
- 🔜 Milestone 4: Speed Optimizations (Next)
- See `docs/Plan_Review_Package_For_Claude/CAD_RMS_Data_Quality_Expansion_Plan_ENHANCED.md`
