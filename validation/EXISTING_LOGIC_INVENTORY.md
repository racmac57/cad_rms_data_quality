# Existing Data Quality Logic Inventory

**Created:** 2026-02-04  
**Author:** Opus (AI Agent)  
**Purpose:** Document all existing validation, normalization, and mapping logic across projects  
**Phase:** 1.1 - Discovery & Consolidation

---

## Executive Summary

### Projects Analyzed
1. **CAD_Data_Cleaning_Engine** - Production ESRI normalization
2. **cad_rms_data_quality** - Monthly validation framework
3. **dv_doj** - Domestic Violence backfill and validation

### Key Findings
- **Normalization Logic:** Comprehensive HOW_REPORTED (280+ mappings) and DISPOSITION (30+ mappings) in production normalizer
- **Validation Framework:** Existing CAD/RMS monthly validators with quality scoring
- **Configuration:** Centralized validation rules in YAML config
- **Reference Data:** Significant consolidation needed (28+ CallType files, duplicate Personnel files)

### Recommendations
1. **Reuse:** Production normalizer (`enhanced_esri_output_generator.py`) mappings
2. **Extend:** Monthly validators to support comprehensive field coverage
3. **Consolidate:** Reference data files (CallTypes, Personnel)
4. **Create:** Drift detectors for new/changed reference values

---

## 1. Normalization Logic Found

### 1.1 enhanced_esri_output_generator.py (PRODUCTION - AUTHORITATIVE)

**Location:** `CAD_Data_Cleaning_Engine/scripts/enhanced_esri_output_generator.py`  
**Status:** ✅ Production, actively used  
**Version:** 3.1 (Updated 2026-02-04)  
**Lines of Code:** ~1,500

**HOW_REPORTED_MAPPING (Lines 137-297)**
- **280+ normalization mappings**
- Covers: typos, abbreviations, concatenations, special characters
- Valid output values:
  - `9-1-1`, `Phone`, `Walk-In`, `Self-Initiated`, `Radio`
  - `eMail`, `Mail`, `Other - See Notes`, `Fax`, `Teletype`
  - `Virtual Patrol`, `Canceled Call`
- Recent additions (2026-02-04): `HACKENSACK`, `PHONE/911`

**DISPOSITION_MAPPING (Lines 64-134)**
- **30+ normalization mappings**
- Handles: abbreviations (GOA, UTL), concatenations, typos
- Valid output values:
  - `Complete`, `Advised`, `Arrest`, `Assisted`, `Canceled`
  - `Unfounded`, `G.O.A.`, `Unable to Locate`, `Checked OK`
  - `Curbside Warning`, `Dispersed`, `Field Contact`, `Issued`
  - `Other - See Notes`, `Record Only`, `See Report`, `See Supplement`
  - `TOT - See Notes`, `Temp. Settled`, `Transported`

**Advanced Normalization Functions:**
- `_normalize_how_reported_advanced()` (Lines 492-629)
  - Pattern matching for unmapped values
  - Handles concatenated values (e.g., "PhoneRadio" → "Phone")
  - Case-insensitive matching
  - Default: `Phone` for unmapped values
  
- `_normalize_disposition_advanced()` (Lines 361-489)
  - Keyword extraction from concatenated values
  - Handles "Other -G.O.A. See Notes" → "Other - See Notes"
  - Default: `Complete` for unmapped values

**Reusability:** ⭐⭐⭐⭐⭐
- Extract mappings for validators
- Reference for domain validation rules

---

### 1.2 call_type_normalizer.py

**Location:** `cad_rms_data_quality/shared/utils/call_type_normalizer.py`  
**Status:** ✅ Production, used by validators  
**Purpose:** Normalize call type names for validation

**Key Functions:**
- `normalize_call_type(value, remove_statute=False)` - Normalizes call type names
  - Trims whitespace, collapses internal spaces
  - Replaces em/en dashes with hyphens
  - Standardizes statute suffix format (e.g., " - 2C:12-1b")
  
- `validate_call_type_format(value)` - Returns (is_valid, error_message)
  - Checks for excessive whitespace
  - Detects em/en dashes
  - Validates statute suffix format

- `validate_call_types(series)` - Bulk validation for pandas Series
  - Returns DataFrame with: index, value, is_valid, error_message

**Pattern:** `STATUTE_SUFFIX_RE = r"\s*-\s*((?:2C|39):[0-9A-Za-z.\-\s]+)\s*$"`

**Reusability:** ⭐⭐⭐⭐⭐
- Already integrated into monthly validators
- Handles NJ statute format normalization

---

### 1.3 standardize_cads.py (LEGACY - DO NOT USE)

**Location:** `unified_data_dictionary/src/standardize_cads.py`  
**Status:** ❌ DEPRECATED - Being archived  
**Replaced By:** `enhanced_esri_output_generator.py`

**Note:** This file has outdated mappings. All new development should use the production normalizer.

---

## 2. Validation Logic Found

### 2.1 validate_cad.py (Monthly CAD Validator)

**Location:** `cad_rms_data_quality/monthly_validation/scripts/validate_cad.py`  
**Status:** ✅ Production, actively used  
**Version:** 1.0.0 (2026-02-02)

**Validation Functions:**

| Function | Purpose | Priority |
|----------|---------|----------|
| `validate_case_numbers()` | Validates YY-NNNNNN format | P1 |
| `validate_required_fields()` | Checks for null/empty required fields | P1 |
| `validate_domain_values()` | Checks field values against valid domains | P2 |
| `validate_call_type_format()` | Uses call_type_normalizer for Incident | P3 |

**Required CAD Fields (from config):**
- `ReportNumberNew`, `Incident`, `TimeOfCall`, `FullAddress2`
- `PDZone`, `Disposition`, `HowReported`

**Quality Scoring (0-100):**
- Required fields: 30 points
- Valid formats: 25 points
- Address quality: 20 points
- Domain compliance: 15 points
- Consistency checks: 10 points

**Output Reports:**
- `action_items.xlsx` - Issues organized by priority
- `validation_summary.html` - SCRPA-styled HTML report
- `metrics.json` - Metrics for trend analysis
- `validation.log` - Detailed log

**Reusability:** ⭐⭐⭐⭐⭐
- Excellent framework for field validators
- Extend with additional domain validators

---

### 2.2 validate_rms.py (Monthly RMS Validator)

**Location:** `cad_rms_data_quality/monthly_validation/scripts/validate_rms.py`  
**Status:** ✅ Production, actively used  
**Version:** 1.0.0 (2026-02-02)

**Validation Functions:**

| Function | Purpose | Priority |
|----------|---------|----------|
| `validate_case_numbers()` | Validates YY-NNNNNN format | P1 |
| `validate_required_fields()` | Checks for null/empty required fields | P1 |
| `validate_date_fields()` | Checks date format and logic | P2 |
| `validate_time_fields()` | Detects known "1" artifact issue | P2 |
| `validate_offense_codes()` | Checks offense code format | P3 |

**Required RMS Fields (from config):**
- `CaseNumber`, `IncidentDate`, `IncidentTime`, `FullAddress`, `Zone`

**Unique Features:**
- Future date detection
- Very old date detection (< 2000)
- Known "1" time artifact detection

**Reusability:** ⭐⭐⭐⭐⭐
- Mirror structure of CAD validator
- Extend with additional RMS-specific checks

---

### 2.3 backfill_dv.py (DV Backfill & Validation)

**Location:** `dv_doj/etl_scripts/backfill_dv.py`  
**Status:** ✅ Production for DV project  
**Purpose:** Backfill and validate Domestic Violence data

**ValidationConfig Class:**
- `valid_municipalities`: `{"Hackensack"}`
- `valid_races`: `{"W", "B", "A", "I", "P", "U"}`
- `valid_ethnicities`: `{"H", "NH"}`
- `case_number_pattern`: `r"^\d{2}-\d{6}$"`
- `date_start`: `"2023-01-01"`, `date_end`: `"2025-12-31"`

**Key Functions:**
- `standardise_case_number()` - Normalizes case numbers
- `backfill_from_rms()` - Backfills missing fields from RMS
- `backfill_from_cad()` - Backfills missing fields from CAD
- `validate_data()` - Comprehensive validation

**Validation Checks:**
- Case number format (YY-NNNNNN)
- Municipality validation
- Race/Ethnicity validation
- VictimAge range (0-120)
- OffenseDate range validation
- Duplicate detection

**Police HQ Pattern:** `HQ_PATTERN = re.compile(r"225\s+State\s+Street", re.IGNORECASE)`
- Used to flag/exclude police HQ addresses

**Reusability:** ⭐⭐⭐⭐
- Excellent patterns for backfill logic
- Validation patterns for new validators
- Police HQ exclusion logic

---

## 3. Configuration Files Found

### 3.1 validation_rules.yaml

**Location:** `cad_rms_data_quality/config/validation_rules.yaml`  
**Status:** ✅ Active configuration  
**Purpose:** Centralized validation rules for CAD/RMS

**Contents:**

```yaml
case_number:
  pattern: '^\d{2}-\d{6}([A-Z])?$'
  required: true

required_fields:
  cad: [ReportNumberNew, Incident, TimeOfCall, FullAddress2, PDZone, Disposition, HowReported]
  rms: [CaseNumber, IncidentDate, IncidentTime, FullAddress, Zone]

domain_validation:
  HowReported:
    valid_values: [9-1-1, Phone, Walk-In, Self-Initiated, Radio, Online, Referral, Alarm, Other]
    normalize_patterns:
      "R": "Radio"
      "P": "Phone"
      "W": "Walk-In"
      "S": "Self-Initiated"
      "911": "9-1-1"

quality_scoring:
  weights:
    required_fields: 30
    valid_formats: 25
    address_quality: 20
    domain_compliance: 15
    consistency_checks: 10

response_time_exclusions:
  how_reported: [Self-Initiated]
  categories: [Regulatory and Ordinance, Administrative and Support, ...]
```

**Note:** HowReported valid_values here differs from production normalizer. Production normalizer (280+ mappings) is more comprehensive.

**Action Needed:** Update config to match production normalizer valid values:
- Add: `eMail`, `Mail`, `Fax`, `Teletype`, `Virtual Patrol`, `Canceled Call`
- Remove: `Online`, `Referral`, `Alarm` (not in production normalizer)

---

## 4. Reference Data Found

### 4.1 Call Types (NEEDS CONSOLIDATION)

**Location:** `09_Reference/Classifications/CallTypes/`

**Root Files (Active):**
- `CallType_Categories.csv` - Likely canonical
- `CallType_Categories.xlsx` - Excel version
- `CAD_CALL_TYPE.xlsx` - Alternative format?
- `clean_calltypes.py` - Cleaning script

**Archive (28+ files):**
- `2019_2025_10_Call_Types_Incidents.csv`
- `2025_08_26_15_05_59_call_types.csv`
- `2025_11_13_CallType_Categories.csv`
- `2026_01_08_CallType_Categories.csv`
- Multiple dated backups
- Multiple manifest.json files (from exports)

**Issues:**
- ❌ Unclear which is canonical
- ❌ Multiple dated versions with unknown differences
- ❌ No schema documentation

**Action Needed:**
1. Compare recent files to identify differences
2. Create `CallTypes_Master.csv` (single source of truth)
3. Create `CallTypes_Master_SCHEMA.md`
4. Move all other versions to archive

---

### 4.2 Personnel/Assignment (NEEDS CLEANUP)

**Location:** `09_Reference/Personnel/`

**Root Files (Active):**
- `Assignment_Master_V2.csv` - Canonical
- `Assignment_Master_V2.xlsx` - Excel version
- `Assignment_Master_V2 (1).csv` - **DUPLICATE - DELETE**
- `2025_12_29_assigned_shift.csv` - Supplementary?

**Archive (99_Archive/):**
- 25+ historical files
- Multiple backups with timestamps
- Old formats (EmployeeListingByWorkGroup, etc.)

**Issues:**
- ❌ `Assignment_Master_V2 (1).csv` is duplicate (filename artifact)
- ⚠️ Potential excess columns (need trimming)
- ⚠️ No schema documentation

**Action Needed:**
1. Delete `Assignment_Master_V2 (1).csv` (move to archive)
2. Audit `Assignment_Master_V2.csv` columns
3. Trim unnecessary columns
4. Create `Assignment_Master_SCHEMA.md`

---

## 5. Mapping Files Found

### 5.1 HOW_REPORTED_MAPPING (Production)

**Location:** `enhanced_esri_output_generator.py` lines 137-297  
**Format:** Python dictionary  
**Entries:** 280+

**Sample Mappings:**
```python
'911': '9-1-1',
'9-1-1': '9-1-1',
'PHONE': 'Phone',
'WALK-IN': 'Walk-In',
'SELF-INITIATED': 'Self-Initiated',
'R': 'Radio',
'P': 'Phone',
'PPP': 'Phone',  # Typo
'HACKENSACK': 'Phone',  # Location reference
'PHONE/911': 'Phone',  # Mixed value
```

### 5.2 DISPOSITION_MAPPING (Production)

**Location:** `enhanced_esri_output_generator.py` lines 64-134  
**Format:** Python dictionary  
**Entries:** 30+

**Sample Mappings:**
```python
'COMPLETE': 'Complete',
'GOA': 'G.O.A.',
'UTL': 'Unable to Locate',
'CLEARED': 'Complete',
'UNFOUNDED/ GOA': 'Unfounded',
```

### 5.3 Domain Validation (Config)

**Location:** `validation_rules.yaml`  
**Status:** Needs update to match production mappings

---

## 6. Data Flow & Pipeline

### Current Production Pipeline

```
Raw CAD Exports (Excel)
    ↓
consolidate_cad_2019_2026.py (Merge yearly + monthly)
    ↓
2019_to_2026_01_30_CAD.csv (714K+ records, raw data)
    ↓
enhanced_esri_output_generator.py (Normalize: HowReported, Disposition, Incident)
    ↓
CAD_ESRI_POLISHED_[timestamp].xlsx (724K records, normalized)
    ↓
copy_polished_to_processed_and_update_manifest.py (Deploy)
    ↓
13_PROCESSED_DATA/ESRI_Polished/base/CAD_ESRI_Polished_Baseline.xlsx
    ↓
ArcGIS Pro Dashboard
```

### Monthly Validation Pipeline

```
Monthly CAD/RMS Export (Excel)
    ↓
validate_cad.py / validate_rms.py
    ↓
Reports:
  - action_items.xlsx (issues by priority)
  - validation_summary.html (SCRPA-styled)
  - metrics.json (for trends)
  - latest.json (pointer to current)
```

---

## 7. Gaps Identified

### 7.1 Missing Validators

| Field | Status | Priority |
|-------|--------|----------|
| HowReported | ⚠️ Partial (config has subset) | HIGH |
| Disposition | ❌ Not in validators | HIGH |
| Incident | ✅ Basic format check | MEDIUM |
| Case Numbers | ✅ In validators | COMPLETE |
| Dates/Times | ✅ In RMS validator | COMPLETE |
| Geography (PDZone) | ❌ Not validated | MEDIUM |
| Personnel | ❌ Not validated | LOW |

### 7.2 Missing Automation

| Feature | Status | Priority |
|---------|--------|----------|
| Drift Detection (CallTypes) | ❌ Not implemented | HIGH |
| Drift Detection (Personnel) | ❌ Not implemented | MEDIUM |
| Reference Data Sync | ❌ Manual process | HIGH |
| Dashboard Pre-Deploy Validation | ❌ Not automated | HIGH |

### 7.3 Documentation Gaps

| Document | Status |
|----------|--------|
| CallTypes_Master_SCHEMA.md | ❌ Missing |
| Assignment_Master_SCHEMA.md | ❌ Missing |
| CFS_Data_Dictionary.md | ❌ Missing |
| Validation Runbook | ❌ Missing |

---

## 8. Recommendations

### Phase 1 Immediate Actions

1. **Consolidate CallTypes** (2-3 hours)
   - Compare `CallType_Categories.csv`, `CAD_CALL_TYPE.xlsx`, recent archive files
   - Create single `CallTypes_Master.csv`
   - Document schema
   - Archive other versions

2. **Clean Personnel Data** (30 minutes)
   - Delete/archive `Assignment_Master_V2 (1).csv`
   - Audit columns in `Assignment_Master_V2.csv`
   - Document schema

3. **Update validation_rules.yaml** (15 minutes)
   - Sync HowReported valid_values with production normalizer

### Phase 2 Build Validators

1. **Extract mappings from normalizer** → Reusable validation dictionaries
2. **Create domain validators** for HowReported, Disposition using existing patterns
3. **Extend monthly validators** with new field checks

### Phase 3 Build Drift Detectors

1. **sync_call_types.py** - Compare CFS data against CallTypes_Master
2. **sync_personnel.py** - Compare CFS data against Assignment_Master

### Phase 4 Integration

1. **run_all_validations.py** - Master orchestrator
2. **Pre-deploy validation** - Automatic check before dashboard update

---

## 9. File Locations Summary

### Production Scripts (USE THESE)

```
CAD_Data_Cleaning_Engine/scripts/
├── enhanced_esri_output_generator.py  ← Authoritative normalizer

cad_rms_data_quality/
├── consolidate_cad_2019_2026.py       ← Consolidation script
├── monthly_validation/scripts/
│   ├── validate_cad.py                ← CAD monthly validator
│   └── validate_rms.py                ← RMS monthly validator
├── shared/utils/
│   ├── call_type_normalizer.py        ← Call type normalization
│   └── report_builder.py              ← HTML report generation
├── config/
│   ├── validation_rules.yaml          ← Validation config
│   └── consolidation_sources.yaml     ← Source file registry
```

### Reference Data (CONSOLIDATE)

```
09_Reference/Classifications/CallTypes/
├── CallType_Categories.csv            ← Identify as canonical
├── CAD_CALL_TYPE.xlsx                 ← Compare and consolidate
└── archive/                           ← 28+ files to consolidate

09_Reference/Personnel/
├── Assignment_Master_V2.csv           ← Canonical
├── Assignment_Master_V2 (1).csv       ← DELETE (duplicate)
└── 99_Archive/                        ← 25+ historical files
```

### New Files to Create

```
cad_rms_data_quality/validation/
├── validators/
│   ├── validate_howreported.py        ← NEW
│   ├── validate_disposition.py        ← NEW
│   ├── validate_incident.py           ← NEW
│   ├── validate_case_numbers.py       ← NEW (extract from monthly)
│   ├── validate_dates_times.py        ← NEW (extract from monthly)
│   ├── validate_geography.py          ← NEW
│   └── validate_personnel.py          ← NEW
├── sync/
│   ├── sync_call_types.py             ← NEW
│   └── sync_personnel.py              ← NEW
├── reports/
│   └── (generated reports)
└── EXISTING_LOGIC_INVENTORY.md        ← This file

09_Reference/Classifications/CallTypes/
├── CallTypes_Master.csv               ← NEW (consolidated)
└── CallTypes_Master_SCHEMA.md         ← NEW

09_Reference/Personnel/
└── Assignment_Master_SCHEMA.md        ← NEW
```

---

## 10. Version History

| Date | Author | Changes |
|------|--------|---------|
| 2026-02-04 | Opus | Initial inventory created |

---

**Next Steps:** Proceed to Phase 1.2 - Consolidate CallTypes reference data
