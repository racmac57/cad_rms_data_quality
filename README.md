# CAD/RMS Data Quality System

**Version:** 1.0.0 (Initial Scaffolding)  
**Created:** 2026-01-29  
**Author:** R. A. Carucci  
**Status:** 🚧 In Development - Scaffolding Complete

---

## Project Overview

Unified data quality system for CAD (Computer-Aided Dispatch) and RMS (Records Management System) exports. This project consolidates best practices from multiple legacy systems and references authoritative schemas from `09_Reference/Standards`.

### Purpose

1. **Historical Consolidation** (Component 1): Merge 2019-2026 CAD data into single validated dataset for ArcGIS Pro dashboards
2. **Monthly Validation** (Component 2): Provide reusable validation scripts for ongoing CAD and RMS exports
3. **Single Source of Truth**: Replace fragmented legacy projects with unified, maintainable system

---

## Project Structure

```
cad_rms_data_quality/
├── README.md                    # This file
├── CHANGELOG.md                 # Version history
├── PLAN.md                      # Detailed implementation plan
├── NEXT_STEPS.md               # Roadmap for next session
├── requirements.txt            # Python dependencies (TO DO)
├── pyproject.toml              # Project configuration (TO DO)
├── Makefile                    # Automation commands (TO DO)
├── .gitignore                  # Git ignore rules (TO DO)
│
├── config/                     # Configuration files
│   ├── schemas.yaml            # Paths to 09_Reference/Standards schemas (TO DO)
│   ├── validation_rules.yaml  # Validation configuration (TO DO)
│   └── consolidation_sources.yaml  # 2019-2026 CAD file paths (TO DO)
│
├── consolidation/              # Component 1: Historical data consolidation
│   ├── scripts/
│   │   ├── consolidate_cad.py         # Merge 2019-2026 CAD files (TO DO)
│   │   └── prepare_arcgis.py          # Create ArcGIS-ready output (TO DO)
│   ├── output/                        # Consolidated datasets (empty)
│   ├── reports/                       # Validation reports (empty)
│   └── logs/                          # Processing logs (empty)
│
├── monthly_validation/         # Component 2: Ongoing validation
│   ├── scripts/
│   │   ├── validate_cad.py            # Monthly CAD validator (TO DO)
│   │   └── validate_rms.py            # Monthly RMS validator (TO DO)
│   ├── templates/
│   │   └── validation_report_template.html  # Report template (TO DO)
│   ├── reports/                       # Monthly reports (empty)
│   └── logs/                          # Validation logs (empty)
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

### CAD Files (2019-2026)
Base Directory: `C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\full_year\`

1. **2019**: `2019\raw\2019_ALL_CAD.xlsx`
2. **2020**: `2020\raw\2020_ALL_CAD.xlsx`
3. **2021**: `2021\raw\2021_ALL_CAD.xlsx`
4. **2022**: `2022\raw\2022_CAD_ALL.xlsx`
5. **2023**: `2023\raw\2023_CAD_ALL.xlsx`
6. **2024**: `2024\raw\2024_CAD_ALL.xlsx`
7. **2025**: `2025\raw\2025_Yearly_CAD.xlsx`
8. **2026 (partial)**: `..\monthly_export\2026\2026_01_01_to_2026_01_28_CAD.xlsx`

**Expected Output:** ~230,000-240,000 records consolidated

---

## Key Validation Rules (from Standards)

### Case Number Format
- Pattern: `^\d{2}-\d{6}([A-Z])?$`
- Examples: `25-000001`, `25-000001A` (supplemental)
- Must be preserved as text (not numeric)

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

## Development Status

### ✅ Completed (2026-01-29)
- [x] Project directory structure created
- [x] README.md (this file)
- [x] CHANGELOG.md
- [x] PLAN.md (complete implementation plan)
- [x] NEXT_STEPS.md (roadmap for continuation)

### 🚧 Next Phase (See NEXT_STEPS.md)
- [ ] Create configuration files (schemas.yaml, validation_rules.yaml)
- [ ] Implement schema_loader utility
- [ ] Refactor validation framework from CAD_Data_Cleaning_Engine
- [ ] Extract normalization logic (Advanced Rules v3.2)
- [ ] Build consolidation scripts
- [ ] Build monthly validation scripts
- [ ] Create test suite
- [ ] Write documentation
- [ ] Archive legacy projects

---

## Quick Start (TO DO - Not Yet Implemented)

### Installation
```bash
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
pip install -r requirements.txt
```

### Run Historical Consolidation
```bash
python consolidation/scripts/consolidate_cad.py
```

### Run Monthly Validation
```bash
python monthly_validation/scripts/validate_cad.py --input "path/to/monthly_export.xlsx"
```

---

## Architecture Principles

1. **Reference, Don't Duplicate**: Schemas loaded from `09_Reference/Standards` (not copied)
2. **Single Source of Truth**: One authoritative location for validation rules and field definitions
3. **Modular Design**: Shared utilities reusable across consolidation and monthly validation
4. **Production-Ready**: Pre-run/post-run checks, audit trails, comprehensive logging
5. **Performance-Optimized**: Vectorized operations, parallel processing, quality scoring

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
