# CAD Data Quality & Validation System - Project Briefing for Opus
## Emergency Session Follow-Up & Comprehensive Validation Plan

**Date:** 2026-02-04  
**Session Duration:** ~4 hours  
**Priority:** HIGH - Production Dashboard Data Quality  
**Status:** ✅ Phone/911 issue FIXED locally | ⏳ ArcGIS Online upload pending | 🚀 CSV export ready for validation

---

## 🎯 Executive Summary

### What We Accomplished (Session Date: Feb 3, 2026, 9:48 PM - 11:04 PM):

**✅ 1. FIXED Root Cause of Dashboard Issue**
- **Problem:** 174,949 records (31% of data) showing "Phone/911" instead of separate Phone/9-1-1 values
- **Root Cause:** ArcGIS Model Builder "Publish Call Data" tool's Calculate Field (2) expression was combining values
- **Location:** Model Builder → Calculate Field (2) → Field: "How_Reported"
- **Bad Expression:** `iif($feature.How_Reported=='9-1-1'||$feature.How_Reported=='Phone','Phone/911',$feature.How_Reported)`
- **Fix Applied:** Changed to `$feature.How_Reported` (pass-through, no transformation)
- **Local Results:** ✅ 565,870 records processed | ✅ Zero "Phone/911" values | ✅ Phone: 109,569 | ✅ 9-1-1: 61,916

**⏳ 2. ArcGIS Online Upload INCOMPLETE**
- **Status:** Local geodatabase (CFStable) is clean and correct with fix applied
- **Issue:** Upload to ArcGIS Online feature service FAILED after 56 minutes (network timeout)
- **Current State:** Online dashboards still show OLD "Phone/911" combined values (561,739 records)
- **Next Step:** Re-upload during off-peak hours (2-6 AM) or use batch strategy

**✅ 3. Exported Full 7-Year Dataset**
- **File:** `CFSTable_2019_2026_FULL_20260203_231437.csv`
- **Records:** 565,870 (2019-2026)
- **Size:** 167.53 MB (175,662,945 bytes)
- **Status:** ✅ Quality verified and production-ready
- **Location:** `cad_rms_data_quality\consolidation\output\`
- **Export Process:** Exported from RDP server geodatabase to C:\Temp, then transferred via RDP clipboard
- **Quality Verification** (via `verify_csv_export.py`):
  - ✅ All 41 expected columns present
  - ✅ Zero "Phone/911" combined values
  - ✅ Phone: 109,569 records (19.36%) | 9-1-1: 61,916 records (10.94%)
  - ✅ Date range: 2019-01-01 to 2026-02-03 (2,590 days)
  - ✅ Only 16 null Call IDs (0.003%) | Zero nulls in critical fields

**📊 4. Discovered Additional Data Quality Issues**
- 2,000+ records with NULL/EMPTY geometry (failed geocoding)
- Date conversion warnings (Time_Dispatched, Time_Out, Time_In)
- Record count increased by 4,131 (need to analyze why)
- Reference data (call types, personnel) has drift and needs sync

---

## 📋 Mission Statement

**Create a comprehensive, automated data quality system that:**

1. **Validates** all CAD data fields against standards
2. **Syncs** reference data (call types, personnel) with operational reality
3. **Detects drift** automatically (new call types, personnel changes)
4. **Generates reports** for data stewards to review and act on
5. **Maintains** single sources of truth for all reference data

---

## 🗂️ Current State Analysis

### **A. Data Sources**

#### **Primary CAD Data (✅ EXPORTED & READY)**
```
Local Geodatabase (CLEAN):
  Path: C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb
  Table: CFStable (lowercase 't')
  Records: 565,870 (2019-2026)
  Status: Phone/911 fix applied and verified

CSV Export (✅ VERIFIED - READY FOR VALIDATION):
  Path: C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\consolidation\output\CFSTable_2019_2026_FULL_20260203_231437.csv
  Records: 565,870
  Size: 167.53 MB (175,662,945 bytes)
  Status: Quality verified via verify_csv_export.py
  Date Range: 2019-01-01 to 2026-02-03 (2,590 days)
  Phone/911 Fix: Confirmed - Zero combined values, 171,485 records properly separated
  Use this file for all validation scripts

ArcGIS Online (PENDING UPDATE):
  - CallsForService: 561,739 records (OLD DATA - still has Phone/911)
  - CallsForService_dashboard: 51,545 records (OLD DATA)
  - CallsForService_public: 561,739 records (OLD DATA)
  Status: Upload failed, needs retry during off-peak hours
  - finalcalltable (processed version)
  
Key Fields for Validation:
  - callsource (How Reported) - 12 valid values
  - disposition (Call Outcome) - ~30 valid values  
  - calltype/Incident - 637+ valid types
  - callid (Case Number) - Format: YY-NNNNNN
  - Dates: calldate, dispatchdate, enroutedate, arrivaldate, cleardate
  - Times: dispatchtime, queuetime, traveltime, cleartime, responsetime
  - Geography: beat, district, division, fulladdr, city, state, zip
  - Personnel: agency, firstunit, unittotal
```

#### **Reference Data - Call Types (NEEDS CONSOLIDATION)**
```
Primary Location: C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\

Current Files:
  ✅ KEEP (Active):
    - CallType_Categories.csv (or .xlsx) - IDENTIFY WHICH IS CANONICAL
    - CAD_CALL_TYPE.xlsx
    
  📦 MOVE TO ARCHIVE:
    - CallType_Categories.xlsx (parent directory - duplicate?)
    - CallTypes\archive\* (28+ old versions!)
      - 2019_2025_10_Call_Types_Incidents.csv
      - 2025_08_26_15_05_59_call_types.csv
      - 2025_11_13_CallType_Categories.csv
      - 2026_01_08_CallType_Categories.csv
      - Multiple dated backups
      
  📊 Contains:
    - Call Type (incident type from CAD)
    - Response Type (how call was handled)
    - Call Category (custom classification)
    
  ⚠️ Issues:
    - Multiple versions with different dates
    - Unclear which is "current"
    - Need to consolidate and establish ONE master file
```

#### **Reference Data - Personnel/Assignment (NEEDS CLEANUP)**
```
Primary Location: C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Personnel\

Current Files:
  ✅ KEEP (Active):
    - Assignment_Master_V2.csv (root - most recent?)
    
  ❌ DUPLICATES TO REMOVE:
    - Assignment_Master_V2 (1).csv (root - duplicate with "(1)" suffix)
    
  📦 MOVE TO ARCHIVE (if not already):
    - 99_Archive\Assignment_Master_V2_backup_*.csv (7 files already in archive)
    
  📊 Contains:
    - Badge numbers
    - Officer names
    - Ranks (Patrolman, Sergeant, Lieutenant, etc.)
    - Status (Active, Retired, Transferred)
    - Unit assignments
    - Hire dates
    
  ⚠️ Issues:
    - One duplicate in root directory
    - Need to trim columns (reduce "fluff")
    - Need sync with CAD active personnel
```

### **B. Existing Data Quality Logic (LOCATE & CONSOLIDATE)**

#### **In CAD_Data_Cleaning_Engine**
```
Location: C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\scripts\

Key File:
  - enhanced_esri_output_generator.py
    - HOW_REPORTED_MAPPING (lines 137-299) - 280+ mappings
    - DISPOSITION_MAPPING - ~30 mappings
    - INCIDENT_MAPPING - 637 types from reference
    - normalize_chunk() function (lines 303-361)
    - _normalize_how_reported_advanced() (lines 495+)
    - _normalize_disposition_advanced() (lines 364+)
    
Data:
  - data/01_raw/2019_to_2026_01_30_CAD.csv (754K records)
  - data/03_final/CAD_ESRI_POLISHED_*.xlsx (normalized outputs)
  - normalization_report_*.md (validation reports)
```

#### **In dv_doj Project (SEARCH FOR ADDITIONAL LOGIC)**
```
Location: C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\dv_doj\

TO INVESTIGATE:
  - etl_scripts\* (13 Python files)
  - docs\mappings\* (4 CSV mapping files)
  - scripts\* (60+ Python files)
  
LOOK FOR:
  - Call type mappings/logic (especially for 2019 historical data)
  - HowReported normalization
  - FullAddress vs FullAddress2 logic
  - Incident backfilling
  - Response type calculation
  - Response time calculation
  - Date/time validation logic
  
PRIORITY FILES TO CHECK:
  - etl.py (main ETL orchestrator)
  - etl_scripts/*.py (all 13 files)
  - scripts/dv_analysis_core.py (may have field logic)
  - scripts/dv_time_enrichment.py (time calculations)
  - scripts/*backfill*.py (backfilling logic)
```

---

## 🎯 Your Mission (Opus)

### **Phase 1: Discovery & Consolidation** (2-3 hours)

#### **Task 1.1: Locate All Existing Data Quality Logic**

**Search these locations for:**
- Call type mappings/translations
- HowReported normalization rules
- Address field handling (FullAddress vs FullAddress2)
- Incident backfilling logic
- Response type calculation
- Response time calculation formulas
- Date/time validation rules

**Locations to search:**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\
C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\dv_doj\
C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\
```

**Deliverable:** Create `EXISTING_LOGIC_INVENTORY.md` documenting:
- What logic exists
- Where it's located
- What fields it validates
- What it does (normalization, validation, calculation)
- Whether it should be reused or consolidated

---

#### **Task 1.2: Consolidate Call Types Reference Data**

**Current State:** 28+ files in Classifications/CallTypes, unclear which is current

**Actions:**
1. **Identify the canonical file:**
   - Open the 3-5 most recent files
   - Compare schemas and record counts
   - Determine which is the "active" version
   
2. **Create single master file:**
   ```
   C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\
   ├── CallTypes_Master.csv          ← NEW: Single source of truth
   ├── CallTypes_Master_SCHEMA.md    ← NEW: Document columns
   └── archive\
       └── [Move all other versions here]
   ```

3. **Trim columns (remove fluff):**
   - Keep only essential columns:
     - CallType (from CAD)
     - ResponseType (how handled)
     - CallCategory (custom classification)
     - EffectiveDate (when this mapping became active)
     - Notes (brief explanation if needed)
   - Remove: Timestamps, user IDs, temporary columns, duplicates

4. **Document schema:**
   ```markdown
   # CallTypes_Master.csv Schema
   
   | Column | Type | Required | Description | Example |
   |--------|------|----------|-------------|---------|
   | CallType | TEXT | YES | Incident type from CAD | "Domestic Violence" |
   | ResponseType | TEXT | YES | How call was handled | "Arrest", "Report" |
   | CallCategory | TEXT | YES | Custom classification | "Crime Against Person" |
   | EffectiveDate | DATE | NO | When mapping became active | "2019-01-01" |
   | Notes | TEXT | NO | Brief explanation | "Changed category in 2020" |
   ```

**Deliverable:** 
- `CallTypes_Master.csv` (single file, trimmed columns)
- `CallTypes_Master_SCHEMA.md` (documentation)
- All old versions moved to archive

---

#### **Task 1.3: Consolidate Personnel/Assignment Reference Data**

**Current State:** 2 active files (one is duplicate), 7 archived

**Actions:**
1. **Remove duplicate:**
   ```powershell
   # Move to archive
   Move-Item "C:\...\Personnel\Assignment_Master_V2 (1).csv" `
             "C:\...\Personnel\99_Archive\Assignment_Master_V2_duplicate_$(Get-Date -F 'yyyyMMdd').csv"
   ```

2. **Trim columns (reduce fluff):**
   - Keep only essential:
     - Badge (badge number)
     - Name (full name)
     - Rank (Patrolman, Sergeant, etc.)
     - Status (Active, Retired, Transferred, Leave)
     - Unit (assigned unit)
     - HireDate (hire date)
   - Remove: Temporary flags, calc fields, notes columns, etc.

3. **Verify schema matches CAD usage:**
   - Check what fields CAD actually references
   - Ensure Badge/Unit codes match CAD assignments

**Deliverable:**
- `Assignment_Master_V2.csv` (cleaned, single file)
- `Assignment_Master_SCHEMA.md` (documentation)
- Duplicate moved to archive

---

### **Phase 2: Export & Baseline** (1 hour)

#### **Task 2.1: Export CFS Table from ArcGIS Geodatabase**

**Script to create:**
```python
# export_cfs_complete.py

import arcpy
import pandas as pd
from datetime import datetime

# Geodatabase path
gdb = r"C:\HPD.ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb"

# Find CFS table (might be CFS, CFStable, or finalcalltable)
arcpy.env.workspace = gdb
tables = arcpy.ListTables()
fc = arcpy.ListFeatureClasses()

print("Available tables:", tables)
print("Available feature classes:", fc)

# Export to CSV and Excel
cfs_table = "CFStable"  # UPDATE based on what you find
output_csv = f"CFS_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
output_xlsx = output_csv.replace('.csv', '.xlsx')

# Export using pandas for better control
fields = [f.name for f in arcpy.ListFields(cfs_table)]
data = []
with arcpy.da.SearchCursor(cfs_table, fields) as cursor:
    for row in cursor:
        data.append(row)

df = pd.DataFrame(data, columns=fields)

# Save
df.to_csv(output_csv, index=False)
df.to_excel(output_xlsx, index=False, sheet_name='CFS_Data')

print(f"✅ Exported {len(df):,} records")
print(f"   CSV: {output_csv}")
print(f"   Excel: {output_xlsx}")
```

**Deliverable:**
- `CFS_Export_YYYYMMDD_HHMMSS.csv` (full dataset)
- `CFS_Export_YYYYMMDD_HHMMSS.xlsx` (for manual review)
- `CFS_Data_Dictionary.md` (all fields documented)

---

### **Phase 3: Build Field-by-Field Validators** (3-4 hours)

#### **Task 3.1: Domain Field Validators**

Create validators for fields with known valid values:

**1. HowReported Validator**
```python
# validate_howreported.py

VALID_VALUES = [
    '9-1-1', 'Phone', 'Walk-In', 'Self-Initiated', 'Radio',
    'eMail', 'Mail', 'Other - See Notes', 'Fax', 'Teletype',
    'Virtual Patrol', 'Canceled Call'
]

# Check for:
# - Invalid values
# - NULL/empty values
# - Case variations
# - Phone/911 combinations (should be GONE after today's fix)
```

**2. Disposition Validator**
```python
# validate_disposition.py

VALID_VALUES = [
    'Complete', 'Arrest', 'Report', 'Gone on Arrival',
    'Unfounded', 'Cancelled', 'Other - See Notes',
    # ... add all 30 valid dispositions
]

# Check for:
# - Concatenated values (e.g., "CompleteReport")
# - Typos
# - NULL values
```

**3. Incident/CallType Validator**
```python
# validate_incident.py

# Load from CallTypes_Master.csv
VALID_CALL_TYPES = load_from_master_file()

# Check for:
# - Call types not in master list
# - Historical call types (pre-2020) that changed
# - Misspellings
# - Unmapped codes
```

---

#### **Task 3.2: Format Field Validators**

**1. Case Number Validator**
```python
# validate_case_numbers.py

# Format: YY-NNNNNN (e.g., 24-012345)
# Check for:
# - Missing leading zeros (e.g., "24-1234" should be "24-001234")
# - Wrong format (missing dash, wrong year)
# - Duplicates
# - Gaps in sequence
```

**2. Date/Time Validator**
```python
# validate_dates_times.py

# Check:
# - Date sequence: CallDate < DispatchDate < ArrivalDate < ClearDate
# - No future dates
# - No dates before 2019
# - Response time calculations match date differences
# - No negative time values
```

---

#### **Task 3.3: Reference Data Validators**

**1. Geography Validator**
```python
# validate_geography.py

# Check:
# - Beat, District, Division against known valid codes
# - City = "Hackensack" (or valid mutual aid cities)
# - State = "NJ"
# - Zip codes valid for Hackensack
# - FullAddress vs FullAddress2 logic (document which is used when)
```

**2. Personnel Validator**
```python
# validate_personnel.py

# Check:
# - FirstUnit against Assignment_Master_V2.csv
# - Agency codes valid
# - Unit assignments match active personnel
```

---

### **Phase 4: Build Automated Drift Detection** (2-3 hours)

#### **Task 4.1: Call Types Drift Detector**

```python
# sync_call_types.py

# Compare CFS export vs CallTypes_Master.csv

# Detect:
# 1. NEW call types in CFS not in master list
#    → Generate report for review
#    → Suggest category/response type based on patterns
# 
# 2. UNUSED call types in master not seen in 90+ days
#    → Flag for potential retirement
#
# 3. FREQUENCY changes (call type usage spike/drop)
#    → Statistical anomaly detection

# Output:
# - new_call_types_YYYYMMDD.xlsx
# - unused_call_types_YYYYMMDD.xlsx  
# - call_type_drift_summary.json
# - suggested_updates.yaml (for review)
```

#### **Task 4.2: Personnel Drift Detector**

```python
# sync_personnel.py

# Compare CFS export vs Assignment_Master_V2.csv

# Detect:
# 1. NEW personnel in CFS not in roster
#    → Possible new hires or missed adds
#
# 2. INACTIVE personnel in roster not in CFS (90+ days)
#    → Possible retirements, transfers, extended leave
#
# 3. NAME VARIATIONS (e.g., "J. Smith" vs "John Smith")
#    → Alias detection and consolidation

# Output:
# - new_personnel_in_cad_YYYYMMDD.xlsx
# - inactive_personnel_YYYYMMDD.xlsx
# - personnel_activity_summary.xlsx
# - roster_sync_suggestions.csv
```

---

### **Phase 5: Master Validation Runner** (1 hour)

#### **Task 5.1: Orchestration Script**

```python
# run_all_validations.py

# Workflow:
# 1. Export CFS data from geodatabase
# 2. Run all field validators
# 3. Run drift detectors
# 4. Generate master report
# 5. Create action items prioritized by severity

# Output:
# validation_reports/
# ├── YYYYMMDD_HHMMSS/
# │   ├── master_validation_report.xlsx
# │   ├── howreported/
# │   │   ├── issues.xlsx
# │   │   ├── summary.json
# │   │   └── edge_cases.txt
# │   ├── disposition/
# │   ├── incident/
# │   ├── case_numbers/
# │   ├── dates_times/
# │   ├── geography/
# │   ├── personnel/
# │   ├── call_types_drift/
# │   └── personnel_drift/
# └── latest/ (symlink to most recent)
```

---

## 📊 Deliverables Summary

### **Phase 1 Deliverables:**
- [ ] `EXISTING_LOGIC_INVENTORY.md` - All existing validation logic documented
- [ ] `CallTypes_Master.csv` - Single source of truth for call types
- [ ] `CallTypes_Master_SCHEMA.md` - Schema documentation
- [ ] `Assignment_Master_V2.csv` - Cleaned personnel roster
- [ ] `Assignment_Master_SCHEMA.md` - Schema documentation
- [ ] All old versions moved to archives

### **Phase 2 Deliverables:**
- [ ] `export_cfs_complete.py` - Export script
- [ ] `CFS_Export_YYYYMMDD.csv` - Full dataset export
- [ ] `CFS_Data_Dictionary.md` - Field documentation

### **Phase 3 Deliverables:**
- [ ] `validate_howreported.py` - Domain validator
- [ ] `validate_disposition.py` - Domain validator
- [ ] `validate_incident.py` - Domain validator
- [ ] `validate_case_numbers.py` - Format validator
- [ ] `validate_dates_times.py` - Logic validator
- [ ] `validate_geography.py` - Reference validator
- [ ] `validate_personnel.py` - Reference validator

### **Phase 4 Deliverables:**
- [ ] `sync_call_types.py` - Drift detector
- [ ] `sync_personnel.py` - Drift detector
- [ ] `apply_call_type_updates.py` - Update applier
- [ ] `apply_personnel_updates.py` - Update applier

### **Phase 5 Deliverables:**
- [ ] `run_all_validations.py` - Master orchestrator
- [ ] `master_validation_report.xlsx` - Combined report
- [ ] Field-specific reports (7+ files)
- [ ] Drift detection reports (2+ files)

---

## 🎯 Success Criteria

### **Data Quality Metrics:**
- [ ] HowReported: 100% domain compliance (only 12 valid values, NO Phone/911)
- [ ] Disposition: 100% domain compliance
- [ ] Incident: 100% mapped to CallTypes_Master.csv
- [ ] Case Numbers: 100% proper format (YY-NNNNNN)
- [ ] Dates: 100% logical sequences (Call < Dispatch < Arrival < Clear)
- [ ] Geography: 95%+ valid (some NULL addresses acceptable)
- [ ] Personnel: 95%+ match to roster

### **Reference Data Metrics:**
- [ ] Single source of truth for call types (1 file, not 28)
- [ ] Single source of truth for personnel (1 file, not 2)
- [ ] All schemas documented
- [ ] Drift detection running automatically
- [ ] New call types flagged within 24 hours of first use
- [ ] Personnel changes flagged within 7 days

---

## 🔧 Tools & Environment

**Required:**
- Python 3.8+
- pandas, openpyxl (for Excel)
- arcpy (for geodatabase access)
- Git (for version control)

**Working Directories:**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\
  ├── validation\               ← NEW: Validation scripts go here
  │   ├── validators\
  │   ├── sync\
  │   └── reports\
  └── reference_data\           ← NEW: Local copies of reference files
```

---

## ⚠️ Critical Notes

1. **Today's Phone/911 Fix:**
   - Model Builder Calculate Field expression changed
   - Tool currently re-running (ETA 10:35 PM)
   - Verify fix with dashboard after completion
   - Document in `LESSONS_LEARNED_20260204.md`

2. **Historical Data (2019):**
   - Call types may be different in 2019 vs 2025
   - Need to check dv_doj project for historical mappings
   - May need separate validation rules for pre-2020 data

3. **FullAddress vs FullAddress2:**
   - Logic exists somewhere for which field to use
   - Find and document this logic
   - May be in dv_doj ETL scripts

4. **Response Time Calculations:**
   - Multiple fields: dispatchtime, queuetime, traveltime, cleartime, responsetime
   - Need to verify calculations match date differences
   - May need to recalculate if inconsistent

---

## 📞 Escalation

**If you discover:**
- Conflicting logic in multiple places → Document all, recommend consolidation
- Missing reference data → Flag for manual creation
- Irreconcilable data quality issues → Recommend data correction strategy
- Performance issues with 560k records → Recommend chunking/sampling strategy

---

## ✅ Getting Started

### **Immediate Actions (First 30 Minutes):**

1. **Read this entire briefing**
2. **Run the CFS table finder script** (provided earlier)
3. **Start Task 1.1:** Search for existing validation logic
4. **Create working directory structure:**
   ```powershell
   cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
   mkdir validation, validation\validators, validation\sync, validation\reports, reference_data
   ```

### **First Deliverable (Hour 1):**
`EXISTING_LOGIC_INVENTORY.md` with initial findings from code search

---

**Good luck, Opus! This is a comprehensive mission but you have all the context you need. Take it one phase at a time.** 🚀

---

**Last Updated:** 2026-02-04 22:20:00  
**Status:** Phone/911 fix in progress, ready for comprehensive validation  
**Next Step:** Begin Phase 1 Task 1.1 (locate existing logic)
