# Claude.md - CAD/RMS Data Quality System Context

This file provides context and rules for any Claude instance working in this repository. It lives at the repo root and complements any `.claude/` settings directory if present.

---

## Project Purpose

This repository contains a unified data quality system for CAD (Computer-Aided Dispatch) and RMS (Records Management System) exports. It consolidates best practices from multiple legacy projects and provides:

1. **Historical Consolidation** (Component 1): Merge 2019-2026 CAD data into single validated dataset for ArcGIS Pro dashboards (754K records through Feb 3, 2026)
2. **Monthly Validation** (Component 2): Reusable validation scripts for ongoing CAD and RMS exports with detailed quality reporting
3. **Single Source of Truth**: Unified system replacing fragmented legacy projects
4. **Historical Backfill** (Component 3): ✅ COMPLETE - 565,470 records loaded to ArcGIS Online dashboard with full attribute data

---

## Project Status (v1.7.0 — 2026-04-10)

### Standards Audit — All Phases Complete

The three-phase Standards Audit (Phase 1: inventory, Phase 2: gap resolution, Phase 3: validation & close) is **complete**. All 9 gaps identified in Phase 1 have been resolved. See `09_Reference/Standards/docs/ai_handoff/Phase1_Standards_Audit.md` for the full record.

**Key changes affecting this repo:**
- `shared/utils/schemas_loader.py` — `load_schemas()` resolves `${standards_root}` in `config/schemas.yaml`
- `shared/utils/version_check.py` — `check_standards_version()` warns if `schemas.yaml` version diverges from `Standards/VERSION`
- `CAD_Data_Cleaning_Engine/scripts/enhanced_esri_output_generator.py` now loads normalization mappings from `Standards/CAD_RMS/mappings/*.json` at runtime (not hardcoded dicts)
  - `how_reported_normalization_map.json`: 140 entries → 12 canonical targets
  - `disposition_normalization_map.json`: 55 entries → 20 canonical targets
- `CAD_Data_Cleaning_Engine/data/` archived to `02_ETL_Scripts/archive/CAD_Data_Cleaning_Engine_data_20260409/` (1.4 GB freed)

### ✅ v1.6.1 - Gap Backfill Date Fix (Feb 16, 2026)

- Gap records (Feb 3-15, 2026) had wrong `calldate` values — surgical ArcGIS API update fixed 2,680 records
- **571,282 records** total with valid geometry and correct dates
- Baseline: `C:\HPD ESRI\03_Data\CAD\Backfill\Baseline_v1_6_1.gdb\CallsForService_Baseline_20190101_20260215`
- Production scripts: `probe_gap_record.py`, `fix_gap_calldate_local.py`, `fix_gap_calldate_online.py`

---

### ✅ v1.6.0 - Historical Backfill SUCCESS (Feb 9, 2026)

**The Challenge:**
- **Problem 1:** Live geocoding via ModelBuilder hung indefinitely at feature 564,897 (network timeout)
- **Problem 2:** Field schema mismatch (ReportNumberNew vs callid) caused NULL attributes
- **Problem 3:** FieldMappings API failed silently with no error messages

**The Solution (Field Copying Strategy):**
1. **Bypass Live Geocoding:** Used existing `latitude`/`longitude` fields with `XYTableToPoint`
2. **Field Copying Instead of Mapping:** Created duplicate fields with target names, copied values directly
3. **Two-Stage Append:** Temp FC → Local CFStable → Online Service

**Results:**
- ✅ **565,470 records** loaded with complete attribute data
- ✅ **Dashboard fully operational** (Call ID, Call Type, Call Source, Full Address all visible)
- ✅ **Total duration:** 13.8 minutes (vs hours of hanging)
- ✅ **Success rate:** 99.93%
- ✅ **Zero NULL values** in attribute fields

**Winning Script:** `complete_backfill_simplified.py`

---

## Critical Architecture Insights

### What Works ✅

1. **XYTableToPoint is Reliable**
   - Handles bulk geometry creation (565K+ records) without timeout
   - Uses existing coordinate fields from CAD exports
   - No network dependency or geocoding service calls
   - Spatial reference: WGS84 (EPSG:4326)

2. **Field Copying Beats Field Mapping**
```python
   # WINNING APPROACH: Create duplicate fields, copy values
   arcpy.management.AddField(temp_fc, "callid", "TEXT", field_length=50)
   arcpy.management.CalculateField(temp_fc, "callid", "!ReportNumberNew!", "PYTHON3")
   
   # FAILED APPROACH: FieldMappings API
   field_mappings = arcpy.FieldMappings()
   # ... complex mapping logic that silently fails
```

3. **Two-Stage Append Provides Stability**
   - Stage 1: Append temp FC → local geodatabase (CFStable)
   - Stage 2: Push CFStable → ArcGIS Online service
   - Allows intermediate verification and troubleshooting

4. **Complete ModelBuilder Transformations Required**
   - DateTime conversions (Text → DATE fields)
   - Response time calculations (dispatchtime, queuetime, cleartime, responsetime)
   - Date attribute extraction (calldow, calldownum, callhour, callmonth, callyear)
   - Address cleaning (remove leading `,` or `&`)
   - Cannot skip these steps—online service expects transformed data

### What Doesn't Work ❌

1. **Live Geocoding at Scale**
   - Esri World Geocoding Service timeouts on 100K+ records
   - Network session exhaustion after ~564K features
   - Silent hang with 0% CPU activity
   - No error logs generated

2. **FieldMappings API for Schema Translation**
   - Silent failures (no error messages)
   - Field names mismatch results in NULL attributes
   - Unpredictable behavior with complex schemas
   - Better to create duplicate fields and copy values

3. **Direct Append with Mismatched Schemas**
   - Source: `ReportNumberNew`, Target: `callid` → NULL values
   - Must match field names exactly before append
   - `schema_type="NO_TEST"` only works when names align

4. **Monolithic Upload Strategy**
   - 754K records in single batch consistently hangs
   - Staged batching (15 × 50K) was planned but not needed after coordinate discovery

---

## Key Scripts & Tools

### Production Scripts (Proven, v1.6.0)

**`complete_backfill_simplified.py`** (450 lines) ✅
- **Purpose:** Historical CAD backfill using field copying strategy
- **Method:** XYTableToPoint + field duplication + two-stage append
- **Transformations:** All ModelBuilder operations (datetime, response time, date attributes)
- **Performance:** 565,470 records in 13.8 minutes
- **Status:** Production-ready, proven successful Feb 9, 2026

**Field Mapping Reference:**
```python
# Source Excel → Target Online Service
'ReportNumberNew' → 'callid'         # Call ID
'Incident' → 'calltype'              # Call Type
'How_Reported' → 'callsource'        # Call Source
'FullAddress2' → 'fulladdr'          # Full Address
'Time_Of_Call' → 'calldate'          # DateTime conversion required
'Time_Dispatched' → 'dispatchdate'   # DateTime conversion required
'Time_Out' → 'enroutedate'           # DateTime conversion required
'Time_In' → 'cleardate'              # DateTime conversion required
'longitude' → 'x'                    # Coordinate (numeric)
'latitude' → 'y'                     # Coordinate (numeric)
```

### Diagnostic Scripts

**`check_cfstable_schema.py`** (20 lines)
- **Purpose:** Display CFStable field schema and record count
- **Usage:** Quick verification of geodatabase structure
- **Output:** Field names, types, aliases, total record count

**`field_mapping_reference.py`** (60 lines)
- **Purpose:** Document complete source → target field mapping
- **Key Finding:** ModelBuilder performs extensive transformations, not just field rename
- **Use Case:** Reference when building new backfill scripts

**`cad_fulladdress2_qc.py`** (250 lines)
- **Purpose:** Comprehensive address quality analysis
- **Outputs:**
  - `address_qc_error_groups.csv` - Error type counts
  - `address_qc_top_values_by_error.csv` - Ranked problematic addresses
  - `temporal_qc_daily_counts.csv` - Daily record volume
  - `temporal_qc_missing_days.csv` - Gaps in data coverage
  - `temporal_qc_low_volume_days.csv` - Days with suspiciously low counts

**Error Classifications:**
- `NULL_OR_BLANK` - Missing addresses
- `PO_BOX` - P.O. Box addresses (cannot geocode to point)
- `SUPPRESSED_HOME_PROXY_HQ` - Home address suppression (225 State St proxy)
- `INTERSECTION_MISSING_STATE` - Intersection without City/State/ZIP
- `OK_INTERSECTION` - Valid intersection format
- `MISSING_HOUSENUM` - No street number
- `MISSING_CITY_STATE` - No city/state suffix
- `MISSING_ZIP` - No ZIP code
- `OK_STANDARD` - Clean, geocoding-ready

### Backup & Restore Operations (v1.6.0)

**`scripts/backup_current_layer.py`** (170 lines)
- Export online layer to local FGDB
- Triple confirmation required
- SHA256 hash verification
- Successfully backed up 561,740 records

**`scripts/truncate_online_layer.py`** (150 lines)
- Delete all records from online feature layer
- Triple confirmation: "TRUNCATE" + username + "DELETE ALL RECORDS"
- Used successfully 3 times during testing

**`scripts/restore_from_backup.py`** (180 lines)
- Emergency rollback operation
- Truncate + restore from local backup
- Successfully restored 561,740 records once

---

## Data Sources & Coverage

### CAD Exports (FileMaker Server)

**Export Location:** `C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\`

**Structure:**
```
05_EXPORTS\_CAD\
├── yearly\
│   ├── 2019\2019_CAD_ALL.xlsx
│   ├── 2020\2020_CAD_ALL.xlsx
│   ├── ...
│   └── 2025\2025_CAD_ALL.xlsx
└── monthly\
    ├── 2025\
    │   ├── 2025_10_CAD.xlsx
    │   ├── 2025_11_CAD.xlsx
    │   └── 2025_12_CAD.xlsx
    └── 2026\
        ├── 2026_01_CAD.xlsx
        └── 2026_02_CAD.xlsx
```

**Critical Fields (Always Present):**
- `ReportNumberNew` (TEXT) - Primary key (YY-NNNNNN or YY-NNNNNNA)
- `Incident` (TEXT) - Call type
- `How_Reported` (TEXT) - Call source (Phone, 9-1-1, Radio, etc.)
- `FullAddress2` (TEXT) - Full address (may have leading `,` or `&`)
- `Time_Of_Call` (TEXT) - Datetime string "YYYY-MM-DD HH:MM:SS"
- `Time_Dispatched` (TEXT) - Datetime string
- `Time_Out` (TEXT) - Datetime string
- `Time_In` (TEXT) - Datetime string
- **`latitude` (TEXT or DOUBLE) - Y coordinate** ⚠️ CRITICAL
- **`longitude` (TEXT or DOUBLE) - X coordinate** ⚠️ CRITICAL

**Data Volume:**
- **Historical (2019-2025):** 714,689 records (7 years)
- **Full Archive (2012-2025):** 1,401,462 records (14 years)
- **Current Baseline:** 754,409 records (2019-01-01 to 2026-02-03)
- **v1.6.0 Backfill:** 565,470 records loaded to dashboard

### Coordinate Field Reality Check

**CRITICAL DISCOVERY (v1.6.0):** CAD exports **already contain** latitude/longitude fields!
```python
# Verify in source Excel:
df = pd.read_excel(source_file)
print("latitude" in df.columns)  # True
print("longitude" in df.columns)  # True

# Sample values:
# latitude: "40.8856" or 40.8856
# longitude: "-74.0435" or -74.0435
```

**Implication:** Live geocoding is **NOT required** for historical data if coordinates are populated.

**Quality Check:**
```python
# Check for NULL coordinates
null_coords = df['latitude'].isnull() | df['longitude'].isnull()
print(f"Records needing geocoding: {null_coords.sum()}")
```

**If coordinates are NULL:** Use NJ State Plane Composite Locator to geocode addresses.

---

## Server Environment (RDP)

### Confirmed Capabilities

**Server:** HPD2022LAWSOFT (Remote Desktop)

**Software:**
- ✅ ArcGIS Pro installed (version 3.6.1)
- ✅ Python environment: `C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat`
- ✅ ArcPy module available
- ✅ Scheduled task capability (Windows Task Scheduler)

**Paths:**
```
C:\HPD ESRI\
├── LawEnforcementDataManagement_New\
│   ├── LawEnforcementDataManagement.aprx          # ArcGIS Pro project
│   ├── LawEnforcementDataManagement.atbx          # Toolbox
│   └── LawEnforcementDataManagement.gdb\
│       └── CFStable                                # Local geodatabase table
├── 03_Data\CAD\Backfill\
│   ├── _STAGING\
│   │   ├── ESRI_CADExport.xlsx                    # Staging file (model reads this)
│   │   └── _LOCK.txt                               # Collision prevention
│   └── CAD_ESRI_Polished_Baseline_*.xlsx          # Source backfill files
├── 04_Scripts\
│   ├── complete_backfill_simplified.py            # v1.6.0 winner
│   ├── backup_current_layer.py
│   ├── truncate_online_layer.py
│   ├── restore_from_backup.py
│   ├── check_cfstable_schema.py
│   ├── field_mapping_reference.py
│   └── cad_fulladdress2_qc.py
└── 05_Reports\
    └── backfill_logs\
```

**ArcGIS Online Service:**
- URL: `https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0`
- Feature class: `CallsForService`
- Current records: 565,470 (as of Feb 9, 2026)
- Dashboard: `https://hpd0223.maps.arcgis.com/apps/dashboards/d9315ff773484ca999ae3e16758cbec1`

---

## Critical Lessons Learned (v1.6.0)

### 1. Field Copying Strategy is More Reliable Than FieldMappings

**The Problem:**
```python
# This approach FAILED (silent NULL attributes):
field_mappings = arcpy.FieldMappings()
field_map = arcpy.FieldMap()
field_map.addInputField(temp_fc, "ReportNumberNew")
output_field = field_map.outputField
output_field.name = "callid"
field_map.outputField = output_field
field_mappings.addFieldMap(field_map)
# ... append with field_mappings (results in NULL data)
```

**The Solution:**
```python
# This approach SUCCEEDED (100% data transfer):
arcpy.management.AddField(temp_fc, "callid", "TEXT", field_length=50)
arcpy.management.CalculateField(temp_fc, "callid", "!ReportNumberNew!", "PYTHON3")
# ... append without field mapping (names already match!)
```

**Why It Works:**
- FieldMappings API has unpredictable behavior with complex schemas
- Direct field copying is explicit and verifiable
- Names match exactly → `schema_type="NO_TEST"` works reliably

### 2. Source Data Already Contains Coordinates

**Don't Assume Geocoding is Needed:**
- CAD exports from FileMaker include `latitude` and `longitude` fields
- Most records (>99%) have populated coordinates from original dispatch system
- Use `XYTableToPoint` to create geometry from existing fields
- Only geocode records with NULL coordinates (edge cases)

**Verification Pattern:**
```python
# Always check coordinate fields first
df = pd.read_excel(source_file)
has_coords = 'latitude' in df.columns and 'longitude' in df.columns

if has_coords:
    null_count = df[['latitude', 'longitude']].isnull().any(axis=1).sum()
    print(f"Records with NULL coords: {null_count}")
    
    if null_count == 0:
        print("✅ No geocoding needed - use XYTableToPoint")
    else:
        print(f"⚠️ Geocode {null_count} records with NULL coordinates")
else:
    print("❌ No coordinate fields - geocoding required for all records")
```

### 3. Two-Stage Append Enables Troubleshooting

**Single-Stage Append (Risky):**
```python
# Direct append: temp_fc → online_service
arcpy.management.Append(temp_fc, online_service, schema_type="NO_TEST")
# If this fails, hard to diagnose (remote service, no local copy)
```

**Two-Stage Append (Safer):**
```python
# Stage 1: temp_fc → local geodatabase
arcpy.management.Append(temp_fc, cfstable, schema_type="NO_TEST")
# Verify locally before pushing to online

# Check data in CFStable
with arcpy.da.SearchCursor(cfstable, ['callid', 'calltype']) as cursor:
    row = next(cursor)
    print(f"Sample: {row[0]}, {row[1]}")  # Verify NOT NULL

# Stage 2: local geodatabase → online service (only if verified)
arcpy.management.Append(cfstable, online_service, schema_type="NO_TEST")
```

**Benefits:**
- Local verification before committing to online service
- Troubleshoot attribute issues in local geodatabase first
- Emergency rollback: restore local geodatabase from backup

### 4. ModelBuilder Transformations Cannot Be Skipped

**What the Model Does (Beyond Simple Append):**

1. **DateTime Conversions:**
```python
   # Text "2026-02-09 14:32:00" → DATE field
   convert_text_to_datetime(table, "Time_Of_Call", "calldate")
```

2. **Response Time Calculations:**
```python
   # Minutes between events
   dispatchtime = (dispatchdate - calldate) / 60
   queuetime = (enroutedate - dispatchdate) / 60
   cleartime = (cleardate - enroutedate) / 60
   responsetime = dispatchtime + queuetime
```

3. **Date Attribute Extraction:**
```python
   arcpy.ca.AddDateAttributes(
       table, "calldate",
       date_attributes=[
           ["DAY_FULL_NAME", "calldow"],      # "Monday"
           ["DAY_OF_WEEK", "calldownum"],     # 1
           ["HOUR", "callhour"],              # 14
           ["MONTH", "callmonth"],            # 2
           ["YEAR", "callyear"]               # 2026
       ]
   )
```

4. **Address Cleaning:**
```python
   # Remove leading "," or "&"
   # ", 198 Central Ave" → "198 Central Ave"
```

**If You Skip These:** Online service receives raw Excel data with:
- ❌ Text datetime strings (not DATE fields)
- ❌ No response time calculations
- ❌ No date attributes for temporal analysis
- ❌ Dirty addresses (leading commas, etc.)

**Dashboard Impact:** Filters, temporal widgets, and analytics break.

### 5. Address Quality Determines Geocoding Success

**Common FullAddress2 Issues:**

| Issue | Example | Impact | Fix |
|-------|---------|--------|-----|
| Leading comma | `, 198 Central Ave` | Parse error | Strip leading punctuation |
| Leading ampersand | `& Central Avenue` | Parse error | Strip leading punctuation |
| Intersection style | `Grand Ave & Clinton Pl` | Geocodes to centroid | Document limitation |
| Missing City/State | `198 Central Ave` | Low match score | Append ", Hackensack, NJ 07601" |
| No street number | `Central Avenue` | Unmatched | Flag for review |
| Vague descriptor | `Area of Main St` | Unmatched | Flag for review |
| PO Box | `PO Box 123` | Cannot geocode to point | Flag, exclude from map |

**QC Script Usage:**
```bash
# Run comprehensive QC before geocoding
python cad_fulladdress2_qc.py

# Review outputs:
# - address_qc_error_groups.csv (prioritize fixes)
# - address_qc_top_values_by_error.csv (batch corrections)
```

**Expected Match Rates (After Cleaning):**
- ✅ Standard addresses: 95-98%
- ⚠️ Intersections: 85-90% (geocode to centroid)
- ❌ Vague descriptors: 60-75% (manual review required)

---

## Workflow Architectures

### Historical Backfill Workflow (v1.6.0)

The successful v1.6.0 backfill follows these steps with proven results.

**Key Achievement:** 565,470 records loaded in 13.8 minutes with 100% attribute completeness.

---

## Field Schema Reference

Source → Target mappings with transformations applied during backfill.

---

## Testing & Verification

**Pre-Flight:** VPN, ArcGIS Pro, latitude/longitude fields, disk space  
**Post-Backfill:** Record count, geometry, attributes, date range

---

## Data Limitations

1. Intersection geocoding to street centroid (±100-500m)
2. Suppressed addresses to 225 State Street (HQ proxy)
3. ~0.3% missing coordinates (NULL lat/lon)
4. WGS84 coordinate system standard

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 1.7.0 | 2026-04-10 | ✅ Standards audit Phases 1-3 complete; schemas_loader + version_check added; data/ archived |
| 1.6.1 | 2026-02-16 | ✅ Gap backfill date fix (2,680 records) |
| 1.6.0 | 2026-02-09 | ✅ Historical backfill SUCCESS (565,470 records) |
| 1.5.0 | 2026-02-06 | ✅ Staged planning |
| 1.4.0 | 2026-02-04 | ✅ Validation |

---

**Current Version:** 1.7.0 ✅  
**Last Updated:** 2026-04-10  
**Status:** Standards audit complete | Pipeline ready for next consolidation run

## Path Resolution

OneDrive root resolves via two junctions (created 2026-03-22):
1. Profile junction:
     C:\Users\carucci_r  →  C:\Users\RobertCarucci
2. OneDrive junction (laptop only — must be replicated on desktop):
     C:\Users\RobertCarucci\OneDrive
     →  C:\Users\RobertCarucci\OneDrive - City of Hackensack

Active root returned by path_config.get_onedrive_root():
  C:\Users\carucci_r\OneDrive - City of Hackensack

### Rules for AI agents
- DO NOT change carucci_r to RobertCarucci in scripts or configs
- Do not rename PowerBI_Data back to the old misspelled folder name; the canonical folder is PowerBI_Data.
- scripts.json uses carucci_r paths — this is correct and intentional
- path_config.py resolves the correct root at runtime via get_onedrive_root()
- If a path appears broken, check junction status before editing any file
