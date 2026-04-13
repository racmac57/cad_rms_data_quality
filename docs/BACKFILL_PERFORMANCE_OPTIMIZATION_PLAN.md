# CAD Backfill Performance Optimization Plan

**Date:** 2026-02-04  
**Author:** R. A. Carucci  
**Status:** Planning Document for AI Collaboration  
**Purpose:** Optimize backfill process for future runs and design daily automation workflow

---

## Executive Summary

**Current Process Time:** 60+ minutes for full historical backfill (754,409 records, 2019-2026)

**Proposed Solution:** Hybrid architecture with static baseline + daily incremental processing to reduce dashboard publishing time from 60+ minutes to **5-10 minutes** for routine daily updates.

---

## Current State Analysis

### What Happened Today (2026-02-04)

#### Process Executed
```
File: CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx
Records: 754,409
Date Range: 2019-01-01 to 2026-02-03
Size: 76.1 MB (79,795,801 bytes)
Quality Score: 99.97%
```

#### Workflow Steps
1. **File Copy** (Local → Server): ~2 minutes ✅
2. **Pre-flight Checks**: ~1 minute ✅
3. **Dry Run Test**: ~1 minute ✅
4. **Actual Backfill Publish**: 60+ minutes ⏳ (still running)
   - File swap to staging
   - ArcGIS Pro Model Builder execution
   - Geocoding 754,409 addresses
   - Field calculations (Phone/911 fix, call type normalization)
   - Upload to ArcGIS Online
   - Indexing

#### Time Breakdown (Estimated)

| Phase | Time | % of Total | Bottleneck? |
|-------|------|-----------|-------------|
| Data Load | 5 min | 8% | ❌ No |
| **Geocoding** | **30-40 min** | **50-67%** | ✅ **YES** |
| Field Calculations | 10 min | 17% | ⚠️ Moderate |
| **Upload to ArcGIS Online** | **10-20 min** | **17-33%** | ✅ **YES** |
| Indexing | 5 min | 8% | ❌ No |
| **TOTAL** | **60-80 min** | **100%** | - |

---

## Performance Bottlenecks Identified

### 1. Geocoding (CRITICAL - 50-67% of time)

**Current Behavior:**
- ArcGIS Pro geocodes all 754,409 addresses in real-time
- Single-threaded process
- Uses Esri World Geocoding Service with rate limits
- Cannot be parallelized within Model Builder

**Why It's Slow:**
- Network latency for each geocoding request
- API rate limiting (requests per second)
- No caching of previously geocoded addresses
- Re-geocodes the same addresses every time

**Impact:** 30-40 minutes per run

### 2. ArcGIS Online Upload (CRITICAL - 17-33% of time)

**Current Behavior:**
- Replaces entire feature layer with 754,409 new records
- 76 MB Excel file upload over network
- Server-side processing and indexing
- No incremental update capability in Model Builder

**Why It's Slow:**
- Network bandwidth constraints
- Full dataset replacement (not append/update)
- ArcGIS Online must re-index entire dataset
- No delta/change detection

**Impact:** 10-20 minutes per run

### 3. Model Builder Single-Threading (MODERATE)

**Current Behavior:**
- ArcGIS Pro Model Builder is mostly single-threaded
- Sequential processing of tools
- Cannot leverage multiple CPU cores effectively

**Impact:** 10 minutes per run (field calculations)

---

## User's Proposed Architecture

### Concept: Static Baseline + Daily Incremental Processing

#### Core Idea
1. **Static Historical Baseline**: 2019-01-01 through end of previous month
   - Pre-geocoded, pre-validated, immutable
   - Only updated monthly (not daily)
   - Always 99%+ quality

2. **Dynamic Recent Window**: Last 7-30 days of data
   - Re-processed daily before dashboard publish
   - Cleaned, normalized, geocoded fresh each day
   - Ensures dashboard always shows highest quality recent data

3. **Daily Automation**: Run before scheduled FileMaker export publishes
   - Consolidate recent data (7-30 days)
   - Apply full cleaning/validation pipeline
   - Geocode only new/changed addresses
   - Append to baseline for dashboard publish

#### Key Benefits
✅ **No 7-day lag** with dirty data on dashboard  
✅ **Faster daily runs** (5-10 min vs 60+ min)  
✅ **Always highest quality** for recent data  
✅ **Minimal geocoding** (only recent addresses)

---

## Proposed Solution: Three-Tier Architecture

### Tier 1: Immutable Historical Baseline

**What:** Pre-processed, pre-geocoded historical data  
**Date Range:** 2019-01-01 to end of previous month  
**Update Frequency:** Monthly (1st of each month)  
**Location:** `13_PROCESSED_DATA/ESRI_Polished/base/`

**File Structure:**
```
base/
├── CAD_Baseline_201901_202601.xlsx  # 2019-01 through 2026-01 (immutable)
├── metadata.json                     # Record counts, date ranges, quality scores
└── geocoding_cache.pkl               # Pre-geocoded coordinates for all addresses
```

**Processing Time:** One-time (or monthly refresh): 60 minutes  
**Benefit:** Never re-geocode historical addresses again

### Tier 2: Rolling Recent Window

**What:** Last 7-30 days of data, re-processed daily  
**Date Range:** Dynamic (e.g., 2026-01-28 to today)  
**Update Frequency:** Daily  
**Location:** `13_PROCESSED_DATA/ESRI_Polished/recent/`

**File Structure:**
```
recent/
├── CAD_Recent_YYYYMMDD.xlsx  # Today's cleaned recent data
├── geocoding_cache_recent.pkl # Recent geocoded addresses
└── processing_log_YYYYMMDD.txt
```

**Processing Time:** Daily: 5-10 minutes  
**Benefit:** Fresh, high-quality data without full re-geocoding

### Tier 3: Dashboard Publishing Layer

**What:** Merged baseline + recent window for ArcGIS publish  
**Update Frequency:** Daily (after Tier 2 processing)  
**Location:** `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\`

**Workflow:**
```
1. Load immutable baseline (fast - already processed)
2. Append cleaned recent window (fast - small dataset)
3. Check for duplicate Call IDs (dedup if needed)
4. Publish to ArcGIS Online (faster - incremental update)
```

**Processing Time:** Daily: 5-10 minutes  
**Benefit:** Dashboard shows clean data with minimal delay

---

## Optimization Strategies

### Strategy 1: Pre-Geocode Historical Data (HIGHEST IMPACT)

**Problem:** Re-geocoding 754K addresses takes 30-40 minutes every time

**Solution:**
1. One-time geocoding of all historical addresses
2. Cache geocoded coordinates in Python dict/pickle
3. Daily runs only geocode NEW addresses (last 7-30 days)

**Implementation:**
```python
# Pre-geocode script (run once, then monthly)
def build_geocoding_cache(df):
    """
    Geocode all unique addresses once.
    Save to geocoding_cache.pkl
    """
    unique_addresses = df['Address'].unique()
    
    # Batch geocode (1000 at a time)
    geocoded = batch_geocode_addresses(unique_addresses)
    
    # Save cache
    cache = {addr: coords for addr, coords in geocoded}
    pickle.dump(cache, open('geocoding_cache.pkl', 'wb'))
    
    return cache

# Daily processing script
def geocode_with_cache(df, cache):
    """
    Use cached coordinates for known addresses.
    Only geocode new addresses.
    """
    def lookup_or_geocode(address):
        if address in cache:
            return cache[address]  # Instant lookup
        else:
            coords = geocode_single(address)  # Only for new addresses
            cache[address] = coords
            return coords
    
    df['Coordinates'] = df['Address'].apply(lookup_or_geocode)
    return df
```

**Time Savings:** 30-40 minutes → 1-2 minutes (95% reduction)

**When to Refresh Cache:**
- Monthly: Re-geocode all addresses (quality improvement)
- Daily: Add only new addresses to cache

### Strategy 2: Incremental Dashboard Updates (HIGH IMPACT)

**Problem:** Replacing entire 754K record dataset takes 10-20 minutes

**Solution:** Use ArcGIS REST API to append only new/changed records

**Implementation:**
```python
import requests
from arcgis import GIS

def incremental_update(baseline_path, recent_path, feature_layer_url):
    """
    Only update records that changed since last publish.
    """
    # Load baseline metadata (record counts, last IDs)
    baseline_meta = load_metadata(baseline_path)
    
    # Load recent data (already cleaned)
    recent_df = pd.read_excel(recent_path)
    
    # Find NEW records (Call IDs not in baseline)
    new_records = recent_df[~recent_df['Call_ID'].isin(baseline_meta['call_ids'])]
    
    # Find UPDATED records (changed since last publish)
    updated_records = find_updated_records(recent_df, baseline_meta)
    
    # Publish only delta to ArcGIS Online
    gis = GIS(portal_url, username, password)
    feature_layer = gis.content.get(feature_layer_id).layers[0]
    
    # Add new records
    if not new_records.empty:
        feature_layer.edit_features(adds=new_records.to_dict('records'))
    
    # Update changed records
    if not updated_records.empty:
        feature_layer.edit_features(updates=updated_records.to_dict('records'))
    
    return len(new_records), len(updated_records)
```

**Time Savings:** 10-20 minutes → 2-3 minutes (85% reduction)

**Caveat:** Requires switching from Model Builder to Python API workflow

### Strategy 3: Parallel Processing (MODERATE IMPACT)

**Problem:** Model Builder is single-threaded

**Solution:** Use Python multiprocessing for field calculations

**Implementation:**
```python
from multiprocessing import Pool
import pandas as pd

def process_chunk(df_chunk):
    """
    Process one chunk of data (field calculations).
    """
    # Phone/911 fix
    df_chunk['How_Reported'] = df_chunk['How_Reported'].replace({
        'Phone/911': 'Phone'  # Or split logic if needed
    })
    
    # Call type normalization
    df_chunk['Call_Type_Normalized'] = normalize_call_types(df_chunk['Call_Type'])
    
    # Date conversions
    df_chunk['TimeOfCall'] = pd.to_datetime(df_chunk['TimeOfCall'])
    
    return df_chunk

def parallel_process_data(df, n_workers=8):
    """
    Split dataframe into chunks, process in parallel.
    """
    chunks = np.array_split(df, n_workers)
    
    with Pool(n_workers) as pool:
        processed_chunks = pool.map(process_chunk, chunks)
    
    return pd.concat(processed_chunks)
```

**Time Savings:** 10 minutes → 3-4 minutes (60% reduction)

### Strategy 4: Skip Model Builder Entirely (HIGHEST LONG-TERM IMPACT)

**Problem:** Model Builder is slow, inflexible, hard to optimize

**Solution:** Python-only workflow using ArcGIS API

**Benefits:**
- Full control over performance optimization
- Parallel processing support
- Better error handling and logging
- Easier to test and debug
- Can use geocoding cache efficiently

**Trade-off:** Requires rewriting Model Builder workflow in Python

---

## Recommended Daily Automation Workflow

### Proposed Schedule

```
TIME          | ACTION                                    | DURATION
--------------|-------------------------------------------|----------
12:00 AM      | FileMaker export (last 7 days of data)    | 5 min
12:05 AM      | Python consolidation script starts        | 3 min
              |   - Load geocoding cache                  |
              |   - Clean/normalize recent 7 days        |
              |   - Geocode only NEW addresses            |
              |   - Generate polished ESRI output         |
12:08 AM      | Incremental dashboard update script       | 5 min
              |   - Load baseline metadata                |
              |   - Merge baseline + recent               |
              |   - Publish delta to ArcGIS Online        |
12:13 AM      | Dashboard refresh complete                | -
--------------|-------------------------------------------|----------
TOTAL TIME    | END-TO-END AUTOMATION                     | 13 min
```

### Daily Workflow Components

#### Step 1: Nightly Consolidation (3 minutes)

**Script:** `nightly_consolidate_recent.py`

```python
#!/usr/bin/env python3
"""
Nightly consolidation of recent CAD data (last 7-30 days).
Runs BEFORE dashboard publish to ensure clean data.
"""

def nightly_consolidation():
    # 1. Load FileMaker export (last 7 days)
    recent_export = load_filemaker_export()
    
    # 2. Load geocoding cache
    geocode_cache = load_geocoding_cache()
    
    # 3. Clean and normalize
    cleaned = apply_cleaning_pipeline(recent_export)
    
    # 4. Geocode only NEW addresses (cache lookup for existing)
    geocoded = geocode_with_cache(cleaned, geocode_cache)
    
    # 5. Save polished output
    save_polished_output(geocoded, date=today())
    
    # 6. Update geocoding cache with new addresses
    save_geocoding_cache(geocode_cache)
    
    return geocoded

if __name__ == '__main__':
    result = nightly_consolidation()
    print(f"Processed {len(result)} records in {elapsed} seconds")
```

**Time:** 3 minutes (vs 60+ minutes for full backfill)

#### Step 2: Incremental Dashboard Update (5 minutes)

**Script:** `incremental_dashboard_update.py`

```python
#!/usr/bin/env python3
"""
Publish cleaned recent data to ArcGIS Online dashboard.
Only updates changed/new records (not full replacement).
"""

def incremental_dashboard_update():
    # 1. Load baseline metadata (what's currently on dashboard)
    baseline_meta = load_baseline_metadata()
    
    # 2. Load cleaned recent data
    recent_cleaned = load_polished_output(date=today())
    
    # 3. Find NEW records (not in baseline)
    new_records = find_new_records(recent_cleaned, baseline_meta)
    
    # 4. Find UPDATED records (changed since last publish)
    updated_records = find_updated_records(recent_cleaned, baseline_meta)
    
    # 5. Publish delta to ArcGIS Online
    publish_results = publish_incremental_update(
        new_records=new_records,
        updated_records=updated_records,
        feature_layer_url=DASHBOARD_FEATURE_LAYER
    )
    
    # 6. Update baseline metadata
    update_baseline_metadata(baseline_meta, new_records, updated_records)
    
    return publish_results

if __name__ == '__main__':
    results = incremental_dashboard_update()
    print(f"Added: {results['new_count']}, Updated: {results['updated_count']}")
```

**Time:** 5 minutes (vs 10-20 minutes for full replacement)

#### Step 3: Verification (1 minute)

**Script:** `verify_dashboard_update.py`

```python
#!/usr/bin/env python3
"""
Quick verification that dashboard update completed successfully.
"""

def verify_dashboard():
    # 1. Query dashboard feature layer
    dashboard_records = query_feature_layer(DASHBOARD_FEATURE_LAYER)
    
    # 2. Check record count
    expected_count = get_expected_record_count()
    actual_count = len(dashboard_records)
    
    if actual_count != expected_count:
        raise ValueError(f"Record count mismatch: {actual_count} != {expected_count}")
    
    # 3. Check date range
    max_date = dashboard_records['TimeOfCall'].max()
    if max_date < today():
        raise ValueError(f"Dashboard not current: {max_date} < {today()}")
    
    # 4. Spot check recent records
    recent_records = dashboard_records[dashboard_records['TimeOfCall'] >= today() - timedelta(days=7)]
    if len(recent_records) < 100:
        raise ValueError(f"Not enough recent records: {len(recent_records)}")
    
    print("✅ Dashboard verification PASSED")
    return True
```

**Time:** 1 minute

---

## Implementation Roadmap

### Phase 1: Pre-Geocode Historical Data (1-2 days)

**Goal:** Create geocoding cache to eliminate 30-40 min bottleneck

**Tasks:**
1. Write `build_geocoding_cache.py` script
2. One-time geocoding of all 754K addresses
3. Save cache to `geocoding_cache.pkl`
4. Test cache lookup performance

**Deliverables:**
- `geocoding_cache.pkl` (geocoded coordinates for all historical addresses)
- `geocode_with_cache.py` (reusable caching function)

**Time Investment:** 1 day development + 2 hours for one-time geocoding run

### Phase 2: Create Nightly Consolidation Script (2-3 days)

**Goal:** Process only recent 7-30 days of data each night

**Tasks:**
1. Adapt `consolidate_cad_2019_2026.py` to accept date range
2. Integrate geocoding cache
3. Add CLI for daily automation
4. Test with sample data

**Deliverables:**
- `nightly_consolidate_recent.py`
- Updated `config/consolidation_sources.yaml` with date range params

**Time Investment:** 2-3 days development + 1 day testing

### Phase 3: Incremental Dashboard Update (3-4 days)

**Goal:** Publish only new/changed records to ArcGIS Online

**Tasks:**
1. Write `incremental_dashboard_update.py` using ArcGIS API
2. Implement delta detection logic
3. Test incremental adds/updates
4. Add verification checks

**Deliverables:**
- `incremental_dashboard_update.py`
- `verify_dashboard_update.py`
- Updated documentation

**Time Investment:** 3-4 days development + 1 day testing

**Caveat:** This replaces Model Builder workflow (big change)

### Phase 4: Scheduled Task Integration (1 day)

**Goal:** Automate nightly workflow via Task Scheduler

**Tasks:**
1. Create PowerShell wrapper for Python scripts
2. Add Task Scheduler job
3. Configure error notifications
4. Test end-to-end automation

**Deliverables:**
- `Schedule-NightlyConsolidation.ps1`
- Task Scheduler job XML
- Email notification on failures

**Time Investment:** 1 day

### Phase 5: Monthly Baseline Refresh (1 day)

**Goal:** Update immutable baseline on 1st of each month

**Tasks:**
1. Write `monthly_baseline_update.py` script
2. Full consolidation (2019 - end of previous month)
3. Update geocoding cache
4. Update baseline metadata

**Deliverables:**
- `monthly_baseline_update.py`
- Updated baseline files in `13_PROCESSED_DATA/`

**Time Investment:** 1 day development (runs monthly)

---

## Performance Comparison

### Current State (Full Backfill)

| Task | Time | Notes |
|------|------|-------|
| File copy | 2 min | Manual |
| Pre-flight checks | 1 min | Manual |
| Model Builder execution | 60+ min | **BOTTLENECK** |
| Verification | 5 min | Manual |
| **TOTAL** | **68+ min** | **Manual, slow** |

### Proposed State (Daily Automation)

| Task | Time | Notes |
|------|------|-------|
| Nightly consolidation | 3 min | Automated, uses cache |
| Incremental dashboard update | 5 min | Automated, delta only |
| Verification | 1 min | Automated |
| **TOTAL** | **9 min** | **Automated, fast** |

**Time Savings:** 68 minutes → 9 minutes = **87% reduction**

### Monthly Baseline Refresh (First of Month)

| Task | Time | Notes |
|------|------|-------|
| Full consolidation | 3 min | All yearly + monthly files |
| Geocoding (historical) | 40 min | Re-geocode all addresses |
| ESRI polishing | 5 min | Generate baseline Excel |
| Update baseline metadata | 1 min | Record counts, dates |
| **TOTAL** | **49 min** | **Once per month** |

**Note:** Monthly refresh ensures baseline stays high-quality (99%+)

---

## Risk Assessment

### Risk 1: Geocoding Cache Invalidation

**Problem:** Address coordinates change (rare but possible)

**Mitigation:**
- Monthly re-geocoding of all addresses
- Cache version tracking
- Manual override for specific addresses if needed

**Impact:** Low (address coordinates rarely change)

### Risk 2: ArcGIS API Rate Limits

**Problem:** Incremental updates hit API rate limits

**Mitigation:**
- Batch updates (100-1000 records at a time)
- Exponential backoff on rate limit errors
- Fallback to full replacement if API fails

**Impact:** Low (daily updates are small)

### Risk 3: Data Quality Drift

**Problem:** Daily automation masks emerging data quality issues

**Mitigation:**
- Weekly validation reports (quality score monitoring)
- Monthly comprehensive validation (using existing validators)
- Alert if quality score drops below 95%

**Impact:** Medium (can be mitigated with monitoring)

### Risk 4: Complexity Increase

**Problem:** More moving parts = more things to break

**Mitigation:**
- Comprehensive logging
- Error notifications (email/Slack)
- Rollback capability (keep previous baseline)
- Documentation and runbooks

**Impact:** Medium (but worth it for 87% time savings)

---

## Cost-Benefit Analysis

### Benefits

1. **Time Savings**
   - Daily: 68 min → 9 min (87% reduction)
   - Annual: ~412 hours → ~55 hours saved

2. **Data Quality**
   - Dashboard always shows cleanest recent data
   - No 7-day lag with "dirty" data
   - Automated quality checks

3. **Reliability**
   - Automated daily runs (no manual steps)
   - Error detection and notifications
   - Rollback capability

4. **Scalability**
   - Can handle growing dataset (incremental updates)
   - Geocoding cache grows with dataset
   - No re-geocoding overhead

### Costs

1. **Development Time**
   - Phase 1: 1 day (geocoding cache)
   - Phase 2: 2-3 days (nightly consolidation)
   - Phase 3: 3-4 days (incremental updates)
   - Phase 4: 1 day (Task Scheduler)
   - Phase 5: 1 day (monthly baseline)
   - **TOTAL: 8-10 days**

2. **Testing Time**
   - 2-3 days comprehensive testing
   - 1 week monitoring after deployment

3. **Maintenance**
   - Monthly baseline refresh monitoring
   - Quarterly cache cleanup
   - Annual validation of workflows

**ROI:** 10 days investment → 412 hours annual savings = **41x return**

---

## Alternate Approaches (Not Recommended, But Considered)

### Option 1: Keep Current Workflow, Just Run Less Often

**Idea:** Only backfill quarterly instead of daily

**Pros:**
- No development work
- Simple to understand

**Cons:**
- Dashboard shows dirty data for months
- 7-day lag persists
- No quality improvement

**Verdict:** ❌ Doesn't solve the problem

### Option 2: Buy Faster ArcGIS Server

**Idea:** Upgrade hardware to speed up geocoding

**Pros:**
- Minimal code changes
- Faster processing

**Cons:**
- Expensive (hardware + licensing)
- Still re-geocodes everything every time
- Only 20-30% improvement (not 87%)

**Verdict:** ❌ Not cost-effective

### Option 3: Pre-Geocode in ArcGIS Pro, Cache as Shapefile

**Idea:** Store pre-geocoded addresses in shapefile

**Pros:**
- Stays within ArcGIS ecosystem
- Familiar to GIS team

**Cons:**
- Shapefile limitations (255 char fields, 2GB max)
- Harder to script/automate
- Still requires Python for incremental logic

**Verdict:** ⚠️ Possible, but less flexible than Python cache

---

## Recommended Next Steps

### For Planning Session with Cursor AI

1. **Share this document** with Cursor AI
2. **Ask Cursor to:**
   - Review the proposed architecture
   - Identify any technical gaps or risks
   - Suggest implementation alternatives
   - Create detailed code templates for Phase 1-5
   - Design error handling and rollback strategies

3. **Focus areas for AI collaboration:**
   - Geocoding cache implementation (pickle vs database vs file-based)
   - ArcGIS API incremental update logic
   - Task Scheduler integration and error handling
   - Baseline metadata tracking and versioning

### Immediate Actions (Before AI Session)

1. ✅ Let current backfill finish (sunk cost, don't stop it)
2. ✅ Verify dashboard shows correct data after completion
3. ✅ Document any issues or unexpected behavior
4. ✅ Gather baseline metadata (record counts, date ranges, quality scores)

### During AI Planning Session

1. **Review this document** with AI
2. **Prioritize phases** (recommend: Phase 1 → Phase 2 → Phase 4 → Phase 3 → Phase 5)
3. **Generate code templates** for each phase
4. **Design error handling** and monitoring
5. **Create testing checklist** for each phase

### After AI Planning Session

1. **Implement Phase 1** (geocoding cache) - highest impact
2. **Test Phase 1** with sample data
3. **Implement Phase 2** (nightly consolidation)
4. **Test end-to-end** with real data
5. **Deploy to production** with monitoring

---

## Appendix: Technical Reference

### Current File Locations

```
# Baseline (static historical data)
C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\
└── CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx (76.1 MB, 754,409 records)

# Server staging area
C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\
└── ESRI_CADExport.xlsx (current dashboard input)

# Orchestrator scripts
C:\HPD ESRI\04_Scripts\
├── Invoke-CADBackfillPublish.ps1
├── Test-PublishReadiness.ps1
├── run_publish_call_data.py
└── config.json
```

### ArcGIS Feature Layer Details

```
Portal: https://hackensackpd.maps.arcgis.com
Feature Layer: CAD Call Data (2019-2026)
Current Records: ~750,000
Update Method: Full replacement (currently)
Proposed Method: Incremental (add/update only delta)
```

### Python Dependencies

```
pandas>=2.0.0
openpyxl>=3.1.0
arcgis>=2.3.0  # For ArcGIS API
requests>=2.31.0
pyyaml>=6.0
pickle>=4.0  # For geocoding cache
```

---

## Questions for AI Planning Session

1. **Geocoding Cache:**
   - Pickle file vs SQLite database vs JSON file?
   - How to handle address normalization (e.g., "123 Main St" vs "123 Main Street")?
   - Cache expiration strategy?

2. **Incremental Updates:**
   - How to detect record changes (field comparison)?
   - How to handle deleted records?
   - What if ArcGIS API fails mid-update?

3. **Error Handling:**
   - Email notifications vs Slack vs log files?
   - Automatic rollback on failure?
   - How many retries before giving up?

4. **Monitoring:**
   - Quality score tracking over time?
   - Dashboard uptime monitoring?
   - Alert thresholds (e.g., <95% quality = alert)?

5. **Testing Strategy:**
   - How to test without affecting production dashboard?
   - Staging environment needed?
   - Automated test suite?

---

**End of Document**

**Next Step:** Share this with Cursor AI and begin Phase 1 implementation planning.
