# CAD/RMS Data Quality System

**Version:** 1.0.1 (Phase 1 Configuration Complete)  
**Created:** 2026-01-29  
**Updated:** 2026-01-30  
**Author:** R. A. Carucci  
**Status:** 🚧 In Development - Phase 1 Complete, Phase 2 Ready

---

## Project Overview

Unified data quality system for CAD (Computer-Aided Dispatch) and RMS (Records Management System) exports. This project consolidates best practices from multiple legacy systems and references authoritative schemas from `09_Reference/Standards`.

### Purpose

1. **Historical Consolidation** (Component 1): Merge 2019-2025 CAD data (714K+ records) into single validated dataset for ArcGIS Pro dashboards
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
├── requirements.txt            # Python dependencies ✅
├── pyproject.toml              # Project configuration ✅
├── Makefile                    # Automation commands (TO DO - in chunk_00010.txt)
├── .gitignore                  # Git ignore rules ✅
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

**Monthly Source Files (2025 Q4):**
- `monthly\2025\2025_10_CAD.xlsx`
- `monthly\2025\2025_11_CAD.xlsx`
- `monthly\2025\2025_12_CAD.xlsx`

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

### ✅ Phase 1: Configuration Complete (2026-01-30)
- [x] Project directory structure created
- [x] README.md, CHANGELOG.md, PLAN.md, NEXT_STEPS.md, Claude.md
- [x] **config/schemas.yaml** - Paths to 09_Reference/Standards
- [x] **config/validation_rules.yaml** - Validation patterns and quality scoring
- [x] **config/consolidation_sources.yaml** - 2019-2025 CAD source files (actual: 714K records)  
- [x] **requirements.txt** - Python dependencies (pandas, pyyaml, usaddress, etc.)
- [x] **pyproject.toml** - Project metadata and build configuration
- [x] **.gitignore** - Git exclusion rules

### 🚧 Phase 2: Python Module Extraction (Next - See EXTRACTION_REPORT.txt)
- [ ] Extract schema_loader.py (~500 lines) from chunk_00001.txt
- [ ] Extract field_normalizer.py (~1200 lines) from chunk_00003.txt
- [ ] Extract validation_engine.py (~1100 lines) from chunk_00006.txt
- [ ] Extract quality_scorer.py (~1000 lines) from chunks 00008/00009
- [ ] Extract consolidate_cad.py (~800 lines) from chunk_00009.txt
- [ ] Extract run_consolidation.py (~400 lines) from chunk_00010.txt
- [ ] Extract Makefile (~200 lines) from chunk_00010.txt
- [ ] Update Claude.md from chunk_00011.txt

### 🔜 Phases 3-7 (After Module Extraction)
- [ ] Run verification tests (imports, schema validation, dry-run)
- [ ] Build ArcGIS preparation script
- [ ] Build monthly validation scripts
- [ ] Create test suite
- [ ] Write user documentation
- [ ] Archive legacy projects

---

## Quick Start (Phase 2 - After Python Module Extraction)

### Installation
```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
pip install -r requirements.txt
```

### Verify Configuration
```powershell
# Test schema paths (after extracting schema_loader.py)
python -m shared.utils.schema_loader
```

### Run Historical Consolidation
```powershell
# Dry run first
python run_consolidation.py --dry-run --verbose

# Full run
python run_consolidation.py --quality-threshold 95
```

### Run Monthly Validation
```powershell
python monthly_validation/scripts/validate_cad.py --input "path/to/monthly_export.xlsx"
```

**Note:** Python module extraction must be completed first (see EXTRACTION_REPORT.txt)

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
