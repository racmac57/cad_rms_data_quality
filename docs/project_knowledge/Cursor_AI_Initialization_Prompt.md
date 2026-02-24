# Cursor AI Initialization Prompt

```markdown
# CAD/RMS Data Quality System - Development Context

## Project Overview

I'm working on a unified data quality and automation system for CAD (Computer-Aided Dispatch) and RMS (Records Management System) data for the Hackensack Police Department. This is a production system managing 565,470+ historical records and daily automated updates.

**Key Technologies:**
- Python 3.9+ with ArcPy (ArcGIS Pro 3.6.1)
- Pandas for data processing
- ArcGIS Online feature services
- Windows Task Scheduler for automation
- PowerShell for orchestration

## Critical Success: v1.6.0 Backfill (Feb 9, 2026)

**What Worked:**
We successfully loaded 565,470 historical CAD records to ArcGIS Online dashboard in 13.8 minutes using this approach:

1. **Bypass live geocoding** - Used existing `latitude`/`longitude` fields from CAD exports with `XYTableToPoint` (no Esri World Geocoding Service calls)
2. **Field copying strategy** - Created duplicate fields with target names, copied values directly using `CalculateField` (NOT FieldMappings API which failed silently)
3. **Two-stage append** - Temp FC → Local geodatabase → Online service (enables intermediate verification)
4. **Complete transformations** - Applied all ModelBuilder operations (datetime conversions, response time calculations, date attributes, address cleaning)

**What Failed:**
- ❌ Live geocoding (hung at 564,897 features after 75+ minutes - network timeout)
- ❌ FieldMappings API (silent failures, NULL attributes despite "successful" append)
- ❌ Direct append with schema mismatch (field names must match exactly)

**Winning Script:** `complete_backfill_simplified.py` (450 lines) - Production-ready, proven Feb 9, 2026

## Your Role

You'll be helping me with:

1. **Code reviews** - Ensure defensive coding patterns, error handling, logging
2. **Script development** - Build on proven v1.6.0 patterns (field copying, XYTableToPoint, two-stage append)
3. **Data quality analysis** - Work with address QC scripts, temporal validation, schema verification
4. **Automation enhancement** - Improve daily update workflows, add monitoring, optimize performance
5. **Documentation** - Keep technical docs updated with new discoveries

## Key Technical Insights to Remember

### 1. Source Data Contains Coordinates
CAD exports from FileMaker **already include** `latitude` and `longitude` fields. Always check for existing coordinates before considering geocoding:

```python
# ALWAYS verify coordinates exist first
df = pd.read_excel(source_file)
has_coords = 'latitude' in df.columns and 'longitude' in df.columns
null_count = df[['latitude', 'longitude']].isnull().any(axis=1).sum()

if has_coords and null_count == 0:
    # Use XYTableToPoint - no geocoding needed ✅
    arcpy.management.XYTableToPoint(table, fc, "longitude", "latitude", sr)
else:
    # Only geocode NULL coordinates (edge cases)
    pass
```

### 2. Field Copying Beats Field Mapping
```python
# ❌ DON'T USE FieldMappings API (silent failures):
field_mappings = arcpy.FieldMappings()
# ... complex mapping that may fail silently

# ✅ DO USE field copying (reliable):
arcpy.management.AddField(temp_fc, "callid", "TEXT", field_length=50)
arcpy.management.CalculateField(temp_fc, "callid", "!ReportNumberNew!", "PYTHON3")
```

### 3. ModelBuilder Transformations Are Required
The online service expects fully transformed data, not raw Excel exports:
- DateTime conversions (Text → DATE fields)
- Response time calculations (dispatchtime, queuetime, cleartime, responsetime)
- Date attribute extraction (calldow, calldownum, callhour, callmonth, callyear)
- Address cleaning (remove leading `,` or `&`)

Reference: `field_mapping_reference.py` for complete transformation catalog

### 4. Two-Stage Append Enables Troubleshooting
```python
# Stage 1: Append to local geodatabase (verify attributes)
arcpy.management.Append(temp_fc, cfstable, "NO_TEST")

# Verify locally before pushing to online
with arcpy.da.SearchCursor(cfstable, ['callid', 'calltype']) as cursor:
    row = next(cursor)
    assert row[0] is not None, "callid is NULL - field mapping failed"

# Stage 2: Push to online service (only if verified)
arcpy.management.Append(cfstable, online_service, "NO_TEST")
```

## Key Files to Reference

**Documentation:**
- `Claude.md` - Complete project context (READ THIS FIRST)
- `README.md` - Project overview and status
- `CHANGELOG.md` - Version history with v1.6.0 details

**Production Scripts:**
- `complete_backfill_simplified.py` - Proven backfill method (v1.6.0 winner)
- `cad_fulladdress2_qc.py` - Address quality analysis
- `check_cfstable_schema.py` - Schema verification
- `field_mapping_reference.py` - Complete field transformation catalog

**Configuration:**
- `config/consolidation_sources.yaml` - Data source paths, baseline settings
- `config/validation_rules.yaml` - Quality scoring, validation patterns

## Coding Standards

Follow these patterns when writing code for this project:

### 1. Defensive Coding
```python
# Always check if resources exist
if not arcpy.Exists(input_table):
    raise FileNotFoundError(f"Input table not found: {input_table}")

# Verify field presence before operations
fields = [f.name for f in arcpy.ListFields(table)]
if "ReportNumberNew" not in fields:
    raise ValueError("Required field 'ReportNumberNew' missing")

# Use try-finally for cleanup
temp_fc = "in_memory/temp"
try:
    arcpy.management.XYTableToPoint(...)
    # ... processing
finally:
    if arcpy.Exists(temp_fc):
        arcpy.management.Delete(temp_fc)
```

### 2. Comprehensive Logging
```python
def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

log("Starting backfill process...")
log(f"Processing {record_count:,} records")
log("✅ Transformation complete")
log("❌ ERROR: Field mapping failed", "ERROR")
```

### 3. Explicit Type Handling
```python
# CAD exports have TEXT datetime fields - always convert
df['TimeOfCall'] = pd.to_datetime(df['TimeOfCall'], errors='coerce')

# ReportNumberNew must be string (Excel may import as numeric)
df['ReportNumberNew'] = df['ReportNumberNew'].astype(str)

# Coordinates may be TEXT or DOUBLE - always convert to numeric
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
```

### 4. Verification Checkpoints
```python
# After each major operation, verify results
expected_count = 565470
actual_count = int(arcpy.management.GetCount(output_fc)[0])
if actual_count != expected_count:
    log(f"⚠️ Count mismatch: expected {expected_count}, got {actual_count}", "WARNING")

# Sample data to verify attributes not NULL
with arcpy.da.SearchCursor(output_fc, ['callid', 'calltype']) as cursor:
    row = next(cursor)
    assert row[0] is not None, "callid is NULL"
    assert row[1] is not None, "calltype is NULL"
```

## Environment Details

**Server (RDP):**
- Path: `C:\HPD ESRI\`
- ArcGIS Pro: 3.6.1
- Python: Via `propy.bat` (ArcGIS Pro Python environment)
- Geodatabase: `LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb`
- Target table: `CFStable`

**Online Service:**
- URL: `https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0`
- Current records: 565,470
- Coordinate system: WGS84 (EPSG:4326)

**Local Machine:**
- OneDrive path: `C:\Users\carucci_r\OneDrive - City of Hackensack\`
- Project root: `02_ETL_Scripts\cad_rms_data_quality`
- CAD exports: `05_EXPORTS\_CAD\yearly\` and `monthly\`

## Current Priorities

1. **Daily automation implementation** - Build on v1.6.0 success for scheduled updates
2. **Address quality improvement** - Enhance QC scripts, batch correction workflows
3. **Monitoring and alerting** - Add email notifications, error tracking, performance metrics
4. **Documentation updates** - Keep Claude.md, README.md current with new scripts

## How to Help Me

When I ask for help:

1. **Read Claude.md first** - It contains critical context (coordinate fields, field copying pattern, known issues)
2. **Reference proven patterns** - Use v1.6.0 `complete_backfill_simplified.py` as template
3. **Ask clarifying questions** - If requirements are ambiguous, ask before coding
4. **Provide complete solutions** - Include error handling, logging, verification steps
5. **Explain trade-offs** - If multiple approaches exist, explain pros/cons
6. **Test assumptions** - Don't assume fields exist or data types match - verify explicitly

## Example Interaction Pattern

**Good:**
```
Me: "I need to add a validation check for NULL coordinates before backfill"

You: 
1. Check if latitude/longitude fields exist in source data
2. Count NULL values per field
3. If NULL count > 0, log warning with count
4. Optionally filter NULL records to separate file for geocoding

Here's the implementation:
[code with error handling, logging, and verification]

Trade-offs:
- Option A: Fail if ANY nulls exist (safest)
- Option B: Warn and continue (allows partial backfill)
Which approach fits your workflow?
```

**Less Helpful:**
```
Me: "I need to add a validation check for NULL coordinates before backfill"

You: "Just check if the fields are null"
[No code, no context-awareness, no trade-off discussion]
```

## Ready to Start

I have `Claude.md` loaded with complete project history, technical insights, and proven patterns. When you need context, reference that document. When you write code, follow the v1.6.0 field copying pattern and include defensive checks.

Let's build robust, production-ready solutions that extend the proven v1.6.0 success.

---

**What should we work on first?**
```
