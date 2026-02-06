# CAD ESRI Polished Baseline - Data Dictionary

**Source File:** `CAD_ESRI_Polished_Baseline.xlsx`  
**Location:** `13_PROCESSED_DATA/ESRI_Polished/base/`  
**Total Records:** 754,409  
**Date Range:** 2019-01-01 to 2026-01-30  
**Columns:** 20  
**Generated:** 2026-02-04

---

## Overview

This data dictionary documents all fields in the production CAD ESRI Polished Baseline file, which feeds the ArcGIS Pro "Calls for Service" dashboard. This file is the **single source of truth** for dashboard data.

### Data Pipeline
```
Raw CAD Exports (Excel) → consolidate_cad_2019_2026.py → enhanced_esri_output_generator.py → CAD_ESRI_Polished_Baseline.xlsx → Dashboard
```

---

## Field Definitions

### 1. ReportNumberNew (Case Number)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | `YY-NNNNNN` |
| **Example** | `19-000001`, `26-012345` |
| **Completeness** | 100% |
| **Unique** | ~559,202 (some duplicates expected for multi-officer calls) |
| **Validation** | Regex: `^\d{2}-\d{6}$` |
| **Notes** | Leading zeros must be preserved. Year prefix (YY) should match Time of Call year. |

### 2. Incident (Call Type)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | Free text with optional NJ statute suffix |
| **Example** | `Motor Vehicle Stop`, `Aggravated Assault - 2C:12-1b` |
| **Completeness** | 100% |
| **Unique** | ~557 distinct values |
| **Reference** | `09_Reference/Classifications/CallTypes/CallTypes_Master.csv` |
| **Notes** | Some values have trailing spaces. Statute format: `- 2C:XX-X` or `- 39:X-X` |

**Top 10 Incident Types:**
| Rank | Incident | Count (sample) |
|------|----------|----------------|
| 1 | Assist Own Agency (Backup) | 1,823 |
| 2 | Task Assignment | 1,673 |
| 3 | Meal Break | 651 |
| 4 | Motor Vehicle Stop | 594 |
| 5 | Traffic Detail | 303 |
| 6 | Medical Call | 292 |
| 7 | Alarm - Burglar | 285 |
| 8 | Relief / Personal | 267 |
| 9 | Targeted Area Patrol | 261 |
| 10 | Administrative Assignment | 231 |

### 3. How Reported (Call Source)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | Controlled vocabulary |
| **Completeness** | 100% |
| **Unique** | 8 values (after normalization) |
| **Reference** | `enhanced_esri_output_generator.py` HOW_REPORTED_MAPPING |

**Valid Values:**
| Value | Description | Frequency (sample) |
|-------|-------------|-------------------|
| `Radio` | Officer-initiated via radio | 53% |
| `Phone` | Non-emergency phone call | 26% |
| `9-1-1` | Emergency 911 call | 13% |
| `Walk-In` | In-person report at station | 4% |
| `Other - See Notes` | Catchall for unusual sources | 4% |
| `Fax` | Fax transmission | <1% |
| `Mail` | Postal mail | <1% |
| `Teletype` | Teletype/digital message | <1% |

**Additional Valid Values (per production normalizer):**
- `Self-Initiated`
- `eMail`
- `Virtual Patrol`
- `Canceled Call`

### 4. FullAddress2 (Location)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | `{Street}, {City}, {State}, {Zip}` |
| **Example** | `198 Central Avenue, Hackensack, NJ, 07601` |
| **Completeness** | 100% |
| **Unique** | ~10,000+ addresses |
| **Notes** | All addresses should be in Hackensack, NJ. City = "Hackensack", State = "NJ" |

### 5. Grid (Patrol Grid)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | Alphanumeric grid code |
| **Completeness** | ~1% (sparse field) |
| **Notes** | May be deprecated or optional |

### 6. ZoneCalc (Patrol Zone)
| Attribute | Value |
|-----------|-------|
| **Type** | FLOAT |
| **Completeness** | 0% (empty in sample) |
| **Notes** | Appears unused; may need RMS backfill or recalculation |

### 7. Time of Call (Call Timestamp)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | `YYYY-MM-DD HH:MM:SS` (ISO 8601) |
| **Example** | `2019-01-01 00:04:21` |
| **Completeness** | 100% |
| **Validation** | Must be within data range (2019-01-01 to 2026-01-30) |

### 8. cYear (Call Year)
| Attribute | Value |
|-----------|-------|
| **Type** | INTEGER |
| **Format** | 4-digit year |
| **Example** | `2019`, `2026` |
| **Completeness** | 100% |
| **Valid Range** | 2019-2026 |
| **Validation** | Must match year in Time of Call |

### 9. cMonth (Call Month)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | Full month name |
| **Example** | `January`, `December` |
| **Completeness** | 100% |
| **Valid Values** | January, February, March, April, May, June, July, August, September, October, November, December |

### 10. Hour_Calc (Call Hour)
| Attribute | Value |
|-----------|-------|
| **Type** | INTEGER |
| **Format** | 24-hour format (0-23) |
| **Example** | `0`, `12`, `23` |
| **Completeness** | 100% |
| **Valid Range** | 0-23 |

### 11. DayofWeek (Day of Week)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | Full day name |
| **Example** | `Monday`, `Friday` |
| **Completeness** | 100% |
| **Valid Values** | Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday |

### 12. Time Dispatched
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | `YYYY-MM-DD HH:MM:SS` |
| **Example** | `2019-01-01 01:15:47` |
| **Completeness** | 100% |
| **Validation** | Should be ≥ Time of Call |

### 13. Time Out (Officer Arrival)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | `YYYY-MM-DD HH:MM:SS` |
| **Example** | `2019-01-01 00:25:00` |
| **Completeness** | 100% |
| **Validation** | Should be ≥ Time Dispatched |

### 14. Time In (Call Cleared)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | `YYYY-MM-DD HH:MM:SS` |
| **Example** | `2019-01-01 00:41:05` |
| **Completeness** | 100% |
| **Validation** | Should be ≥ Time Out |

### 15. Time Spent (Duration)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | `H:MM:SS` or `HH:MM:SS` |
| **Example** | `0:10:51`, `1:25:30` |
| **Completeness** | 100% |
| **Calculation** | Time In - Time Out |

### 16. Time Response (Response Time)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | `H:MM:SS` or `HH:MM:SS` |
| **Example** | `0:06:09`, `0:24:42` |
| **Completeness** | 100% |
| **Calculation** | Time Out - Time of Call |
| **Notes** | Used for response time analytics; exclude administrative calls |

### 17. Officer (Responding Unit/Officer)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | Unit ID or Officer name |
| **Example** | `Unit 101`, `Smith, John` |
| **Completeness** | 99.8% |
| **Unique** | ~102 values (in sample) |
| **Reference** | `09_Reference/Personnel/Assignment_Master_V2.csv` |

### 18. Disposition (Call Outcome)
| Attribute | Value |
|-----------|-------|
| **Type** | TEXT (string) |
| **Format** | Controlled vocabulary |
| **Completeness** | 100% |
| **Unique** | 15 values (after normalization) |
| **Reference** | `enhanced_esri_output_generator.py` DISPOSITION_MAPPING |

**Valid Values:**
| Value | Description | Frequency (sample) |
|-------|-------------|-------------------|
| `Complete` | Call completed successfully | 53% |
| `Assisted` | Assistance provided | 20% |
| `Other - See Notes` | See narrative for details | 7% |
| `Advised` | Information/advice given | 4% |
| `Issued` | Citation/summons issued | 4% |
| `Record Only` | Report taken, no action | 3% |
| `Checked OK` | Situation verified safe | 3% |
| `Canceled` | Call canceled | 1% |
| `G.O.A.` | Gone on Arrival | 1% |
| `TOT - See Notes` | Turned Over To (another agency) | 1% |
| `Dispersed` | Crowd/situation dispersed | 1% |
| `Temp. Settled` | Temporarily resolved | 1% |
| `Unable to Locate` | Subject not found | <1% |
| `Unfounded` | Report found to be false | <1% |
| `Transported` | Person transported | <1% |

### 19. latitude (GPS Latitude)
| Attribute | Value |
|-----------|-------|
| **Type** | FLOAT |
| **Format** | Decimal degrees |
| **Expected Range** | 40.8-40.9 (Hackensack area) |
| **Completeness** | 0% in sample (requires geocoding) |
| **Notes** | May need RMS backfill or geocoding from FullAddress2 |

### 20. longitude (GPS Longitude)
| Attribute | Value |
|-----------|-------|
| **Type** | FLOAT |
| **Format** | Decimal degrees |
| **Expected Range** | -74.0 to -74.1 (Hackensack area) |
| **Completeness** | 0% in sample (requires geocoding) |
| **Notes** | May need RMS backfill or geocoding from FullAddress2 |

---

## Data Quality Observations

### High Completeness (100%)
- ReportNumberNew, Incident, How Reported, FullAddress2
- Time of Call, cYear, cMonth, Hour_Calc, DayofWeek
- Time Dispatched, Time Out, Time In, Time Spent, Time Response
- Disposition

### Low/Zero Completeness
| Field | Completeness | Issue |
|-------|--------------|-------|
| Grid | ~1% | Sparsely populated |
| ZoneCalc | 0% | Appears unused |
| latitude | 0% | Requires geocoding |
| longitude | 0% | Requires geocoding |

### Data Quality Issues to Investigate
1. **Character Encoding:** Some Incident values show `�` instead of special characters
2. **Trailing Spaces:** Some Incident types have trailing spaces
3. **Duplicate Case Numbers:** Multiple rows per case (expected for multi-officer calls, but should verify)
4. **Missing Coordinates:** latitude/longitude empty (geocoding needed for mapping)

---

## Field Relationships

### Primary Key
- `ReportNumberNew` + `Officer` (composite key for unique rows)
- `ReportNumberNew` alone is NOT unique (multi-officer calls)

### Temporal Dependencies
```
Time of Call ≤ Time Dispatched ≤ Time Out ≤ Time In
```

### Derived Fields
| Field | Derived From |
|-------|--------------|
| cYear | Time of Call (YEAR) |
| cMonth | Time of Call (MONTH name) |
| Hour_Calc | Time of Call (HOUR) |
| DayofWeek | Time of Call (DAY name) |
| Time Spent | Time In - Time Out |
| Time Response | Time Out - Time of Call |

### Cross-Reference Tables
| Field | Reference File |
|-------|----------------|
| Incident | CallTypes_Master.csv |
| Officer | Assignment_Master_V2.csv |
| How Reported | HOW_REPORTED_MAPPING (in code) |
| Disposition | DISPOSITION_MAPPING (in code) |

---

## Validation Rules Summary

### Critical Validations (Must Pass)
1. ReportNumberNew matches pattern `^\d{2}-\d{6}$`
2. How Reported in valid domain (12 values)
3. Disposition in valid domain (15+ values)
4. Time of Call is valid datetime and within range
5. cYear matches Time of Call year

### Warning Validations (Should Investigate)
1. Incident exists in CallTypes_Master.csv
2. Officer exists in Assignment_Master_V2.csv
3. FullAddress2 contains "Hackensack, NJ"
4. Time sequence is logical (Call ≤ Dispatch ≤ Out ≤ In)

### Data Drift Monitors
1. New Incident types not in master
2. New Officers not in personnel file
3. Unusual How Reported distribution shifts
4. Response time outliers (> 2 hours)

---

## Usage Notes

### Loading the File
```python
import pandas as pd

# Force ReportNumberNew to string (preserve leading zeros)
df = pd.read_excel(
    'CAD_ESRI_Polished_Baseline.xlsx',
    dtype={'ReportNumberNew': str}
)
```

### Quick Quality Check
```python
# Check domain values
valid_how_reported = ['9-1-1', 'Phone', 'Walk-In', 'Self-Initiated', 
                       'Radio', 'eMail', 'Mail', 'Other - See Notes', 
                       'Fax', 'Teletype', 'Virtual Patrol', 'Canceled Call']

invalid = df[~df['How Reported'].isin(valid_how_reported)]
print(f"Invalid How Reported values: {len(invalid)}")
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-04 | 1.0.0 | Initial data dictionary created |

---

**Document Owner:** Opus (AI Agent)  
**System:** Hackensack Police Department CAD/RMS Data Quality System  
**Contact:** R. A. Carucci
