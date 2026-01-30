# Next Steps - CAD/RMS Data Quality System

**Project Status:** 🚧 Scaffolding Complete (2026-01-29)  
**Phase:** Ready for Implementation  
**Estimated Time to Complete:** 10-15 hours

---

## Quick Reference

### What's Done ✅
- [x] Project directory structure created
- [x] README.md with complete project overview
- [x] CHANGELOG.md with version history
- [x] PLAN.md (complete implementation plan)
- [x] NEXT_STEPS.md (this file)
- [x] Authoritative sources identified and documented
- [x] Legacy projects analyzed for migration

### What's Next 🚧
- [ ] 10 implementation tasks (see Phase Checklist below)
- [ ] Estimated 10-15 hours total development time

---

## Resume Development - Start Here

When you're ready to continue, follow this order:

### 1. Review Context (5 minutes)
Read these files in order:
1. `README.md` - Project overview and structure
2. `PLAN.md` - Complete implementation strategy
3. `CHANGELOG.md` - Current version and status

### 2. Set Up Environment (15 minutes)
```bash
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"

# Review authoritative sources (confirm paths exist)
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Standards"
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine"
```

### 3. Begin Phase 1 Implementation
Start with: **"Create config files and schema loader"** (see Phase 1 below)

---

## Implementation Phases

### Phase 1: Configuration & Schema Integration (2-3 hours)

**Goal:** Set up configuration files and schema loading infrastructure

#### Task 1.1: Create Configuration Files
**File:** `config/schemas.yaml`

```yaml
# Schema paths pointing to 09_Reference/Standards
standards_root: "C:/Users/carucci_r/OneDrive - City of Hackensack/09_Reference/Standards"

schemas:
  canonical: "${standards_root}/unified_data_dictionary/schemas/canonical_schema.json"
  cad: "${standards_root}/unified_data_dictionary/schemas/cad_fields_schema_latest.json"
  rms: "${standards_root}/unified_data_dictionary/schemas/rms_fields_schema_latest.json"
  transformation: "${standards_root}/unified_data_dictionary/schemas/transformation_spec.json"

mappings:
  cad_to_rms: "${standards_root}/CAD_RMS/DataDictionary/current/schema/cad_to_rms_field_map.json"
  rms_to_cad: "${standards_root}/CAD_RMS/DataDictionary/current/schema/rms_to_cad_field_map.json"
  field_mappings: "${standards_root}/mappings/field_mappings/mapping_rules.md"
  call_types: "${standards_root}/mappings/call_types_*.csv"

config:
  response_time_filters: "${standards_root}/config/response_time_filters.json"
```

**File:** `config/validation_rules.yaml`

```yaml
# Validation rules adapted from CAD_Data_Cleaning_Engine
case_number:
  pattern: '^\d{2}-\d{6}([A-Z])?$'
  required: true
  examples:
    - "25-000001"
    - "25-000001A"

address:
  required_fields: ["FullAddress2"]
  usps_validation: true
  reverse_geocoding: true
  fuzzy_match_threshold: 0.90
  exclude: ["225 State Street"]  # Police HQ

quality_scoring:
  thresholds:
    high: 95
    medium: 80
    low: 60
  weights:
    required_fields: 30
    valid_formats: 25
    address_quality: 20
    domain_compliance: 15
    consistency: 10
```

**File:** `config/consolidation_sources.yaml`

```yaml
# CAD data sources for 2019-2026 consolidation
base_directory: "C:/Users/carucci_r/OneDrive - City of Hackensack/05_EXPORTS/_CAD/full_year"

sources:
  - year: 2019
    path: "${base_directory}/2019/raw/2019_ALL_CAD.xlsx"
    expected_records: 26000
  - year: 2020
    path: "${base_directory}/2020/raw/2020_ALL_CAD.xlsx"
    expected_records: 25000
  - year: 2021
    path: "${base_directory}/2021/raw/2021_ALL_CAD.xlsx"
    expected_records: 26000
  - year: 2022
    path: "${base_directory}/2022/raw/2022_CAD_ALL.xlsx"
    expected_records: 30000
  - year: 2023
    path: "${base_directory}/2023/raw/2023_CAD_ALL.xlsx"
    expected_records: 32000
  - year: 2024
    path: "${base_directory}/2024/raw/2024_CAD_ALL.xlsx"
    expected_records: 32000
  - year: 2025
    path: "${base_directory}/2025/raw/2025_Yearly_CAD.xlsx"
    expected_records: 34000
  - year: 2026
    path: "C:/Users/carucci_r/OneDrive - City of Hackensack/05_EXPORTS/_CAD/monthly_export/2026/2026_01_01_to_2026_01_28_CAD.xlsx"
    expected_records: 2500

output:
  consolidated: "consolidation/output/2019_2026_CAD_Consolidated.csv"
  arcgis: "consolidation/output/2019_2026_CAD_ArcGIS_Ready.csv"
```

#### Task 1.2: Create Schema Loader Utility
**File:** `shared/utils/schema_loader.py`

**Purpose:** Load schemas from 09_Reference/Standards (referenced, not duplicated)

**Key Functions:**
- `load_config(config_name)` - Load YAML config files
- `load_schema(schema_name)` - Load JSON schema from Standards
- `load_mapping(mapping_name)` - Load field mapping files
- `validate_schema_paths()` - Verify all referenced files exist

**Reference:** Use `09_Reference/Standards/unified_data_dictionary/src/` as template

#### Task 1.3: Create Python Package Files
**File:** `requirements.txt`

```txt
# Core dependencies
pandas>=2.0.0
numpy>=1.24.0
pyyaml>=6.0

# Address validation (from RMS_Data_ETL)
usaddress>=0.5.10

# Fuzzy matching (from multi_column_matching_strategy)
rapidfuzz>=3.0.0

# Excel support
openpyxl>=3.1.0
xlrd>=2.0.1

# Reporting
jinja2>=3.1.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0

# Optional: ArcGIS (if available)
# arcpy (comes with ArcGIS Pro)
```

**File:** `pyproject.toml`

```toml
[project]
name = "cad-rms-data-quality"
version = "1.0.0"
description = "Unified CAD/RMS data quality system"
authors = [
    {name = "R. A. Carucci", email = "carucci_r@hackensack.org"}
]
requires-python = ">=3.9"
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "pyyaml>=6.0",
    "usaddress>=0.5.10",
    "rapidfuzz>=3.0.0",
    "openpyxl>=3.1.0",
    "jinja2>=3.1.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0"
]
```

**File:** `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/

# Data outputs
consolidation/output/*.csv
consolidation/reports/*
consolidation/logs/*
monthly_validation/reports/*
monthly_validation/logs/*

# Test outputs
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Keep directory structure
!consolidation/output/.gitkeep
!consolidation/reports/.gitkeep
!consolidation/logs/.gitkeep
!monthly_validation/reports/.gitkeep
!monthly_validation/logs/.gitkeep
```

**File:** `Makefile`

```makefile
.PHONY: help setup test consolidate validate-cad validate-rms

help:
	@echo "CAD/RMS Data Quality System"
	@echo "Available commands:"
	@echo "  make setup           - Install dependencies"
	@echo "  make test            - Run test suite"
	@echo "  make consolidate     - Run historical consolidation (2019-2026)"
	@echo "  make validate-cad    - Validate monthly CAD export"
	@echo "  make validate-rms    - Validate monthly RMS export"

setup:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=shared --cov-report=html

consolidate:
	python consolidation/scripts/consolidate_cad.py
	python consolidation/scripts/prepare_arcgis.py

validate-cad:
	@echo "Usage: make validate-cad INPUT=path/to/file.xlsx"
	python monthly_validation/scripts/validate_cad.py --input $(INPUT)

validate-rms:
	@echo "Usage: make validate-rms INPUT=path/to/file.xlsx"
	python monthly_validation/scripts/validate_rms.py --input $(INPUT)
```

---

### Phase 2: Refactor Validation Framework (2-3 hours)

**Goal:** Extract and adapt validation logic from CAD_Data_Cleaning_Engine

#### Task 2.1: Create Pre-Run Validation
**Source:** `CAD_Data_Cleaning_Engine/validators/validation_harness.py`  
**Target:** `shared/validators/pre_run_checks.py`

**Extract:**
- Environment checks (Python version, OS, dependencies)
- File existence validation
- Schema validation
- Disk space and memory checks

#### Task 2.2: Create Post-Run Validation
**Source:** `CAD_Data_Cleaning_Engine/validators/validate_full_pipeline.py`  
**Target:** `shared/validators/post_run_checks.py`

**Extract:**
- Record count preservation
- Quality score validation (0-100)
- Audit trail completeness
- Output file validation

#### Task 2.3: Create Parallel Validation Engine
**Source:** `CAD_Data_Cleaning_Engine/validate_cad_export_parallel.py`  
**Target:** `shared/validators/validation_engine.py`

**Extract:**
- Vectorized operations (26.7x performance gain)
- Bulk error logging
- Domain value validation
- Pattern matching

#### Task 2.4: Create Quality Scorer
**Source:** `CAD_Data_Cleaning_Engine/cad_data_processor.py`  
**Target:** `shared/validators/quality_scorer.py`

**Extract:**
- 0-100 quality scoring system
- Component scores (required fields, formats, address, domain, consistency)

---

### Phase 3: Extract Normalization & Processing (2-3 hours)

#### Task 3.1: Field Normalizer
**Source:** `CAD_Data_Cleaning_Engine/enhanced_esri_output_generator.py`  
**Target:** `shared/processors/field_normalizer.py`

**Extract Advanced Normalization Rules v3.2:**
- Concatenated value handling ("DispersedComplete" → "Dispersed")
- Pattern-based normalization (HowReported: "R" → "Radio")
- Default assignment for 100% domain compliance

#### Task 3.2: Address Standardizer
**Source:** `RMS_Data_ETL/rms_core_cleaner.py`  
**Target:** `shared/processors/address_standardizer.py`

**Extract:**
- `usaddress` library integration
- USPS pattern validation
- Reverse geocoding (if ArcGIS available)
- Fuzzy matching (90% threshold)

#### Task 3.3: DateTime Processor
**Source:** `RMS_Data_Processing/enhanced_rms_processor_v3_clean.py`  
**Target:** `shared/processors/datetime_processor.py`

**Extract:**
- Time artifact fixes (handles "1" values)
- Datetime mixing resolution
- Cascading null checks

---

### Phase 4: Build Consolidation Scripts (2-3 hours)

#### Task 4.1: CAD Consolidation Script
**File:** `consolidation/scripts/consolidate_cad.py`

**Functionality:**
1. Load config from `consolidation_sources.yaml`
2. Load each year's CAD file
3. Normalize column names using field_normalizer
4. Validate using validation_engine
5. Deduplicate based on `ReportNumberNew`
6. Gap detection (missing days)
7. Quality scoring
8. Generate consolidation report
9. Export consolidated CSV

**Expected Output:** `2019_2026_CAD_Consolidated.csv` (~230K-240K records)

#### Task 4.2: ArcGIS Preparation Script
**File:** `consolidation/scripts/prepare_arcgis.py`

**Functionality:**
1. Load consolidated CSV
2. Apply canonical_schema field definitions
3. Standardize addresses for geocoding
4. Format datetime for time-enabled features
5. Add derived fields (Year, Month, DayOfWeek, TimeOfDay)
6. Export as `2019_2026_CAD_ArcGIS_Ready.csv`

---

### Phase 5: Build Monthly Validation Scripts (2-3 hours)

#### Task 5.1: CAD Monthly Validator
**File:** `monthly_validation/scripts/validate_cad.py`

**CLI:**
```bash
python validate_cad.py --input "path/to/export.xlsx" --output "reports/2026_02/"
```

**Workflow:**
1. Pre-run checks
2. Load CAD file with schema validation
3. Run validation_engine
4. Compare against historical averages
5. Generate HTML/Excel/JSON reports
6. Post-run checks

**Reference:** `09_Reference/Standards/scripts/validation/validate_rms_export.py` as template

#### Task 5.2: RMS Monthly Validator
**File:** `monthly_validation/scripts/validate_rms.py`

**Similar to CAD validator, using:**
- `rms_fields_schema_latest.json`
- Multi-column matching for CAD↔RMS cross-validation

---

### Phase 6: Testing (1-2 hours)

#### Task 6.1: Unit Tests
**Files:**
- `tests/test_validators.py`
- `tests/test_processors.py`
- `tests/test_schema_loader.py`

#### Task 6.2: Integration Tests
**File:** `tests/test_consolidation.py`

**Test with sample data:**
- Load 2-3 years of sample data
- Run full consolidation pipeline
- Verify output quality

---

### Phase 7: Documentation (1-2 hours)

#### Task 7.1: Technical Documentation
**Files to create:**
- `docs/ARCHITECTURE.md` - System design, data flow diagrams
- `docs/MIGRATION_NOTES.md` - What came from which legacy project
- `docs/STANDARDS_REFERENCE.md` - How to use 09_Reference/Standards

#### Task 7.2: User Guides
**Files to create:**
- `docs/CONSOLIDATION_GUIDE.md` - Step-by-step for running consolidation
- `docs/MONTHLY_VALIDATION_GUIDE.md` - How to validate monthly exports

---

### Phase 8: Archive Legacy Projects (30 minutes)

#### Task 8.1: Create Archive
```bash
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts"
mkdir "_ARCHIVED_2026_01_30"
move "RMS_CAD_Combined_ETL" "_ARCHIVED_2026_01_30\"
move "RMS_Data_ETL" "_ARCHIVED_2026_01_30\"
move "RMS_Data_Processing" "_ARCHIVED_2026_01_30\"
```

#### Task 8.2: Document Migration
Add to `_ARCHIVED_2026_01_30\README.md`:
- What was extracted from each project
- Where functionality moved to
- Why projects were archived

---

## Suggested Work Sessions

### Session 1 (2-3 hours): Foundation
- Phase 1: Configuration & Schema Integration
- Create all config files
- Implement schema_loader.py
- Test schema loading

### Session 2 (2-3 hours): Validation Framework
- Phase 2: Refactor Validation Framework
- Extract validators from CAD_Data_Cleaning_Engine
- Create quality scorer
- Write unit tests

### Session 3 (2-3 hours): Processing Logic
- Phase 3: Extract Normalization & Processing
- Implement field_normalizer
- Implement address_standardizer
- Implement datetime_processor

### Session 4 (2-3 hours): Consolidation
- Phase 4: Build Consolidation Scripts
- Implement consolidate_cad.py
- Implement prepare_arcgis.py
- Test with sample data

### Session 5 (2-3 hours): Monthly Validation
- Phase 5: Build Monthly Validation Scripts
- Implement validate_cad.py
- Implement validate_rms.py
- Generate sample reports

### Session 6 (1-2 hours): Testing & Documentation
- Phase 6: Testing
- Phase 7: Documentation
- Phase 8: Archive Legacy Projects

---

## Checkpoints

After each phase, verify:

1. **Phase 1:** Can load all schemas from 09_Reference/Standards
2. **Phase 2:** Validation framework runs without errors
3. **Phase 3:** Normalization rules process sample data correctly
4. **Phase 4:** Consolidation produces expected record count
5. **Phase 5:** Monthly validation generates HTML/Excel reports
6. **Phase 6:** All tests pass
7. **Phase 7:** Documentation complete and accurate
8. **Phase 8:** Legacy projects archived, migration documented

---

## Quick Commands for Next Session

```bash
# Navigate to project
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"

# Check Standards directory
dir "C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Standards\unified_data_dictionary\schemas"

# Check CAD_Data_Cleaning_Engine
dir "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\validators"

# Review this file
type NEXT_STEPS.md

# Start implementation
# (Pick Phase 1, Task 1.1 from above)
```

---

## Success Metrics

### Component 1: Historical Consolidation
- [ ] Single CSV with 230K-240K records
- [ ] Quality score ≥95/100
- [ ] Gap analysis report generated
- [ ] ArcGIS-ready dataset created
- [ ] Runtime <10 minutes

### Component 2: Monthly Validation
- [ ] CLI tools functional for CAD and RMS
- [ ] Reports generated in <5 minutes
- [ ] Pass/fail criteria implemented
- [ ] Anomaly detection working

### Architecture
- [ ] All schemas referenced (not duplicated)
- [ ] CAD_Data_Cleaning_Engine logic refactored
- [ ] Legacy projects archived with notes

---

## Contact & Notes

**Created:** 2026-01-29  
**Author:** R. A. Carucci (with Claude AI assistance)  
**Status:** Ready for Phase 1 Implementation

**Notes:**
- User had limited time during scaffolding session
- All authoritative sources confirmed and documented
- Directory structure complete and ready
- Next session should start with Phase 1, Task 1.1

**Files to Review Before Starting:**
1. `README.md` - Project overview
2. `PLAN.md` - Complete implementation plan
3. `CHANGELOG.md` - Version history
4. This file (`NEXT_STEPS.md`) - Implementation roadmap

---

**Ready to resume? Start with Phase 1, Task 1.1: Create `config/schemas.yaml`**
