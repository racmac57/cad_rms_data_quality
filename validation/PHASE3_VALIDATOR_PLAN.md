# Phase 3 Validator Plan

**Created:** 2026-02-04  
**Purpose:** Planning document for field validators based on data dictionary analysis

---

## Validators to Build

Based on the data dictionary analysis, the following validators are required:

### Priority 1: Domain Value Validators (Critical)

#### 1. HowReportedValidator
- **Field:** How Reported
- **Type:** Domain validation
- **Valid Values:** 12 values (9-1-1, Phone, Walk-In, Self-Initiated, Radio, eMail, Mail, Other - See Notes, Fax, Teletype, Virtual Patrol, Canceled Call)
- **Existing Logic:** `enhanced_esri_output_generator.py` HOW_REPORTED_MAPPING
- **Test:** All values in valid set
- **Priority:** HIGH (dashboard filter depends on this)

#### 2. DispositionValidator
- **Field:** Disposition
- **Type:** Domain validation
- **Valid Values:** 15+ normalized values
- **Existing Logic:** `enhanced_esri_output_generator.py` DISPOSITION_MAPPING
- **Test:** All values in valid set
- **Priority:** HIGH (reporting depends on this)

#### 3. IncidentValidator
- **Field:** Incident
- **Type:** Reference validation + format
- **Reference:** CallTypes_Master.csv (649 types)
- **Existing Logic:** `call_type_normalizer.py`
- **Tests:**
  - Value exists in master OR is valid variant
  - Statute suffix format correct (if present)
  - No unexpected trailing spaces
- **Priority:** HIGH (analytics categorization)

### Priority 2: Format Validators

#### 4. CaseNumberValidator
- **Field:** ReportNumberNew
- **Type:** Format validation
- **Pattern:** `^\d{2}-\d{6}$`
- **Existing Logic:** `validate_cad.py` and `validate_rms.py`
- **Tests:**
  - Matches YY-NNNNNN format
  - Year prefix is valid (19-26)
  - Year matches Time of Call year
- **Priority:** HIGH (primary identifier)

#### 5. DateTimeValidator
- **Fields:** Time of Call, Time Dispatched, Time Out, Time In
- **Type:** Format + logic validation
- **Tests:**
  - Valid datetime format (YYYY-MM-DD HH:MM:SS)
  - Within valid date range (2019-01-01 to current)
  - Temporal sequence: Call ≤ Dispatch ≤ Out ≤ In
  - No future dates
- **Priority:** MEDIUM

#### 6. DurationValidator
- **Fields:** Time Spent, Time Response
- **Type:** Format + reasonableness
- **Tests:**
  - Valid duration format (H:MM:SS)
  - Response time < 2 hours (flag outliers)
  - Time Spent < 12 hours (flag outliers)
- **Priority:** MEDIUM

### Priority 3: Reference Validators

#### 7. OfficerValidator
- **Field:** Officer
- **Type:** Reference validation
- **Reference:** Assignment_Master_V2.csv
- **Tests:**
  - Officer exists in personnel master OR is valid unit ID
  - Flag inactive officers still appearing
- **Priority:** MEDIUM (drift detection)

#### 8. GeographyValidator
- **Field:** FullAddress2
- **Type:** Format + domain
- **Tests:**
  - Contains "Hackensack, NJ"
  - Not Police HQ address (for response time exclusions)
  - State = "NJ"
  - ZIP in Hackensack range (07601, 07602, 07606)
- **Priority:** LOW (addresses already normalized)

### Priority 4: Derived Field Validators

#### 9. DerivedFieldValidator
- **Fields:** cYear, cMonth, Hour_Calc, DayofWeek
- **Type:** Consistency validation
- **Tests:**
  - cYear matches YEAR(Time of Call)
  - cMonth matches MONTHNAME(Time of Call)
  - Hour_Calc matches HOUR(Time of Call)
  - DayofWeek matches DAYNAME(Time of Call)
- **Priority:** LOW (should be auto-calculated)

---

## Implementation Order

### Sprint 1: Core Validators (2-3 hours)
1. ✅ HowReportedValidator
2. ✅ DispositionValidator
3. ✅ CaseNumberValidator

### Sprint 2: Incident & DateTime (2 hours)
4. ✅ IncidentValidator
5. ✅ DateTimeValidator

### Sprint 3: Reference & Geography (2 hours)
6. ✅ OfficerValidator
7. ✅ GeographyValidator
8. ✅ DurationValidator

### Sprint 4: Derived & Cleanup (1 hour)
9. ✅ DerivedFieldValidator
10. ✅ Integration testing

---

## Validator Template

Each validator should follow this structure:

```python
# validation/validators/{field}_validator.py

import pandas as pd
from typing import Tuple, List, Dict, Any

class FieldValidator:
    \"\"\"Validator for {field} field.\"\"\"
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.valid_values = [...]  # Load from reference
        
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        \"\"\"
        Validate field in dataframe.
        
        Returns:
            Tuple of (issues_df, summary_dict)
        \"\"\"
        issues = []
        
        # Validation logic here
        
        issues_df = pd.DataFrame(issues)
        summary = {
            'field': '{field}',
            'total_records': len(df),
            'valid_records': len(df) - len(issues),
            'invalid_records': len(issues),
            'pass_rate': (len(df) - len(issues)) / len(df) * 100
        }
        
        return issues_df, summary
        
    def get_invalid_values(self, df: pd.DataFrame) -> List[str]:
        \"\"\"Return list of invalid values found.\"\"\"
        pass
```

---

## Quality Scoring Integration

Each validator will contribute to the overall quality score:

| Validator | Weight | Rationale |
|-----------|--------|-----------|
| HowReportedValidator | 15% | Dashboard filter critical |
| DispositionValidator | 15% | Reporting critical |
| CaseNumberValidator | 20% | Primary identifier |
| IncidentValidator | 15% | Analytics categorization |
| DateTimeValidator | 15% | Temporal integrity |
| OfficerValidator | 10% | Reference data |
| GeographyValidator | 5% | Location data |
| DerivedFieldValidator | 5% | Calculated fields |

**Quality Score Formula:**
```
Score = Σ(ValidatorPassRate × Weight) / Σ(Weights)
```

---

## Dependencies

### External References Needed
1. `CallTypes_Master.csv` → IncidentValidator
2. `Assignment_Master_V2.csv` → OfficerValidator
3. `validation_rules.yaml` → Configuration for all validators

### Existing Code to Reuse
1. `validate_cad.py` → CaseNumberValidator pattern, quality scoring
2. `validate_rms.py` → DateTime validation logic
3. `call_type_normalizer.py` → Incident normalization
4. `enhanced_esri_output_generator.py` → Domain value mappings

---

## Deliverables

After Phase 3 completion:

```
validation/
├── validators/
│   ├── __init__.py
│   ├── base_validator.py
│   ├── how_reported_validator.py
│   ├── disposition_validator.py
│   ├── case_number_validator.py
│   ├── incident_validator.py
│   ├── datetime_validator.py
│   ├── duration_validator.py
│   ├── officer_validator.py
│   ├── geography_validator.py
│   └── derived_field_validator.py
├── config/
│   └── validator_config.yaml
└── tests/
    └── test_validators.py
```

---

**Ready for Phase 3 implementation.**
