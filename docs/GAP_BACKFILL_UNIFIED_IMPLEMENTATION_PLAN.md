# Unified Implementation Plan: Gap Backfill Calldate Fix
**Date:** 2026-02-16  
**Author:** R. A. Carucci  
**AI Collaboration:** Perplexity (architecture), Claude Opus (scripts), Code Copilot (safety review)

---

## Executive Summary

### What Was Fixed
- **Gap records (Feb 3-15, 2026):** 2,680 records successfully added to ArcGIS Online CallsForService layer with geometry ✓
- **Geometry restoration:** All 571,282 records (2019-2026) now have valid point geometry on dashboard map ✓
- **Date field issue:** Gap records show wrong `calldate` values (all showing "2/6/26 10:00:00" estimate instead of real dates from Feb 3-15)

### What Remains
1. **Fix gap calldate values** using real dates from `gap_for_append_v2` table
2. **Recalculate derived fields:** calldow, calldownum, callhour, callmonth, callyear
3. **Recalculate response metrics:** dispatchtime, responsetime (depend on corrected calldate)
4. **Update both:** Local baseline (CFStable_GeocodeAddresses) and online layer
5. **Verify:** Dashboard chronological sort shows Feb 15 records at top

---

## Context from Three AI Sessions

### 1. Perplexity (Architecture & Gap Fill)
**Chatlog:** `docs/chatlog/perpexity_spaces_backfill_gap_fix_x_and_y/`
- **Achieved:** Added 2,680 gap records to online layer with valid geometry
- **Issue discovered:** All gap records showing same date "2/6/26 10:00:00" (estimation fallback)
- **Real dates:** Available in local `gap_for_append_v2` table (field: `USER_Time_of_Call`)
- **Decision:** Use surgical API update (ArcGIS API for Python) instead of truncate/reload for 571K records

### 2. Claude Opus (Production Scripts)
**Chatlog:** `docs/chatlog/Claude-Fixing_incorrect_calldate_values_in_ArcGIS_backfill/`
- **Delivered:** Three production-ready scripts (v4) with CLI, dry-run, rollback, audit
- **Key features:** Forced America/New_York timezone, min/max range enforcement, schema preflight, derived field recalculation
- **Scripts:**
  1. `probe_gap_record.py` - Timezone verification and field probe (read-only)
  2. `fix_gap_calldate_local.py` - Update local baseline (CFStable_GeocodeAddresses)
  3. `fix_gap_calldate_online.py` - Surgical update of online layer (2,680 records)

### 3. Code Copilot (Safety Review)
**Chatlog:** `docs/chatlog/ChatGPT-ArcGIS_Date_Field_Fix/`
- **Identified 6 risks:** Range enforcement, timezone shift, stale dispatch metrics, duplicate Call IDs, schema drift, NULL vs wrong dates
- **Resulted in v4 patches:** All safety issues addressed in Opus scripts
- **Key improvements:** Numeric range checks, timezone logging, out-of-range → NULL, duplicate detection

---

## File Update List

### ✅ Already Created (Opus v4 Scripts)
**Location:** `C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\scripts\`

- [x] `probe_gap_record.py` (277 lines) - Timezone + field verification probe
- [x] `fix_gap_calldate_local.py` (720 lines) - Local baseline (CFStable_GeocodeAddresses) update
- [x] `fix_gap_calldate_online.py` (991 lines) - Online layer surgical update

**Features:**
- CLI with `--live`, `--rollback`, `--dry-run` (default)
- Forced America/New_York timezone (prevents DST/offset bugs)
- Audit assertions with `--expected-updates 2680`
- Sample tracking with `--sample-callids 26-011297,26-011300`
- JSON artifacts: snapshot.json, changes.json, summary.json
- CSV exports: sample_before_after.csv
- Output directory: `C:\HPD ESRI\04_Scripts\_out\{script}_YYYYMMDD_HHMMSS\`

### 📋 Documentation Updates Needed
**Location:** Local repo root and `docs/`

1. **CHANGELOG.md** - Add v1.6.1 entry:
   ```markdown
   ## [1.6.1] - 2026-02-16
   ### Fixed - Gap Record Calldate Values
   - Corrected 2,680 gap records (Feb 3-15, 2026) showing wrong calldate
   - Real dates from gap_for_append_v2 applied to local baseline and online layer
   - Recalculated derived fields: calldow, callhour, callmonth, callyear
   - Recalculated response metrics: dispatchtime, responsetime
   - Dashboard chronological sort now displays most recent calls first
   - Scripts: probe_gap_record.py, fix_gap_calldate_local.py, fix_gap_calldate_online.py
   - Safety: Forced America/New_York timezone, min/max range enforcement, rollback capability
   ```

2. **SUMMARY.md** - Update status section:
   ```markdown
   STATUS: v1.6.1 COMPLETE ✓
   - Historical records: 571,282 (2019-01-01 to 2026-02-15)
   - Geometry: 100% present (map fully operational)
   - Gap closure: 2,680 records (Feb 3-15) with corrected dates
   - Dashboard: Chronological sort, full attribute data
   ```

3. **README.md** - Add Gap Fix Scripts section:
   ```markdown
   ### Gap Backfill Date Fix Scripts (v1.6.1)
   | Script | Purpose | Status |
   |--------|---------|--------|
   | probe_gap_record.py | Timezone & field verification | PRODUCTION |
   | fix_gap_calldate_local.py | Local baseline date correction | PRODUCTION |
   | fix_gap_calldate_online.py | Online layer surgical update | PRODUCTION |
   
   **Usage (RDP):**
   ```powershell
   # 1. Verify timezone (read-only)
   propy.bat probe_gap_record.py
   
   # 2. Fix local baseline (dry-run first)
   propy.bat fix_gap_calldate_local.py
   propy.bat fix_gap_calldate_local.py --live
   
   # 3. Fix online layer (dry-run first)
   propy.bat fix_gap_calldate_online.py
   propy.bat fix_gap_calldate_online.py --live --expected-updates 2680
   
   # 4. Rollback if needed
   propy.bat fix_gap_calldate_online.py --rollback
   ```
   ```

4. **Claude.md** - Update project status:
   ```markdown
   **Current Version:** 1.6.1 ✅  
   **Last Updated:** 2026-02-16  
   **Status:** Gap backfill complete | Dates corrected | Dashboard operational
   
   Recent fixes:
   - v1.6.1: Gap record calldate correction (surgical API update, 2,680 records)
   - v1.6.0: Historical backfill (565,470 records with XY coordinates)
   ```

5. **perplexity_spaces_handoff.md** - Mark as COMPLETE:
   ```markdown
   🟢 STATUS: COMPLETE (2026-02-16)
   - Gap records added: 2,680 ✓
   - Geometry restored: 571,282 ✓
   - Dates corrected: Opus v4 scripts ✓
   - Dashboard operational: Full coverage 2019-2026 ✓
   ```

---

## RDP Execution Guide

### Pre-Flight: Deploy Updated Scripts

```powershell
# On local machine
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"

# Deploy to RDP (uses cached Windows credentials)
.\Deploy-ToRDP-Simple.ps1
```

**Expected:** 3 scripts deployed to `C:\HPD ESRI\04_Scripts\`:
- probe_gap_record.py
- fix_gap_calldate_local.py
- fix_gap_calldate_online.py

---

### Step 1: Timezone Verification (Read-Only, 30 seconds)

**Purpose:** Confirm RDP server timezone is Eastern and epoch conversion has no drift.

```powershell
# On RDP
cd "C:\HPD ESRI\04_Scripts"
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" probe_gap_record.py
```

**Expected Output:**
```
[1. SYSTEM TIMEZONE]
  Timezone name:    ('Eastern Standard Time', 'Eastern Daylight Time')
  UTC offset (std): -5 hours
  UTC offset (DST): -4 hours
  System TZ:        Eastern CONFIRMED

[2. EPOCH CONVERSION CHECK]
  System and NY epochs MATCH
  NY round-trip: 2026-02-03 10:14:14-05:00
  Drift: 0.000s
  Status: PASS

[3. LOCAL: gap_for_append_v2]
  26-011297 -> 2026-02-03 10:14:14

[4. ONLINE: ArcGIS Online Feature Layer]
  26-011297: calldate (NY): 2026-02-06 10:00:00 (WRONG)
  
[5. NEXT STEPS]
  Proceed with fix scripts.
```

**Decision:**
- ✅ If PASS and epochs match → Continue to Step 2
- ❌ If timezone mismatch or drift >1s → STOP, investigate server timezone config

---

### Step 2: Fix Local Baseline — Dry Run (1 minute)

**Purpose:** Update `CFStable_GeocodeAddresses` with real dates from `gap_for_append_v2`. Dry run first to verify changes.

```powershell
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" fix_gap_calldate_local.py
```

**Expected Output:**
```
[STEP 1] Building lookup from gap_for_append_v2
  Lookup: 2,680 Call IDs
  Sample: 26-011288 -> 2026-02-03 08:15:23

[STEP 2] Scanning CFStable_GeocodeAddresses
  Total records: 571,282
  WHERE: callid LIKE '26-%'
  Scanned: ~10,000
  Updates prepared: 2,680
  Already correct: 0
  
[STEP 3] Verification
  Skipping (dry run)

[AUDIT]
  Updates prepared: 2,680
  AUDIT PASS: 2,680 updates vs 2680 expected
  
  >>> DRY RUN complete. Re-run with --live to apply. <<<
```

**Files Created:**
- `C:\HPD ESRI\04_Scripts\_out\local_fix_YYYYMMDD_HHMMSS\snapshot.json`
- `C:\HPD ESRI\04_Scripts\_out\local_fix_YYYYMMDD_HHMMSS\changes.json`
- `C:\HPD ESRI\04_Scripts\_out\local_fix_YYYYMMDD_HHMMSS\fix.log`

**Decision:**
- ✅ If audit PASS and update count = 2,680 → Continue to Step 3
- ❌ If audit FAIL or count mismatch → Review `changes.json`, investigate

---

### Step 3: Fix Local Baseline — LIVE (1 minute)

**Purpose:** Apply changes to local baseline.

```powershell
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" fix_gap_calldate_local.py --live --expected-updates 2680 --sample-callids 26-011297,26-011300
```

**Expected Output:**
```
  Mode: LIVE
  
[STEP 2] Scanning CFStable_GeocodeAddresses
  UPDATE: 26-011288  2026-02-06 10:00:00 -> 2026-02-03 08:15:23  DOW=Tuesday, Hour=8
  ...
  Updated: 2,680
  
[STEP 3] Verification
  SAMPLE OK: 26-011297 = 2026-02-03 10:14:14
  All verified!
  
[AUDIT]
  AUDIT PASS: 2,680 updates vs 2680 expected (within 2%)
  
  >>> Local baseline fixed. Run fix_gap_calldate_online.py next. <<<
```

**Verification:**
```powershell
# Quick check (optional)
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" -c "import arcpy; cur = arcpy.da.SearchCursor(r'C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb\CFStable_GeocodeAddresses', ['callid', 'calldate'], \"callid = '26-011297'\"); row = next(cur); print(f'{row[0]}: {row[1]}')"
```

**Expected:** `26-011297: 2026-02-03 10:14:14`

**Rollback (if needed):**
```powershell
propy.bat fix_gap_calldate_local.py --rollback
```

---

### Step 4: Fix Online Layer — Dry Run (2-3 minutes)

**Purpose:** Surgically update 2,680 gap records on ArcGIS Online. Dry run first to verify changes and save snapshot.

```powershell
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" fix_gap_calldate_online.py --sample-callids 26-011297,26-011300
```

**Expected Output:**
```
[TIMEZONE VERIFICATION]
  System timezone:  ('Eastern Standard Time', 'Eastern Daylight Time')
  Forced LOCAL_TZ:  America/New_York
  System/NY match:  YES
  NY round-trip drift=0.000s

[SCHEMA PREFLIGHT]
  calldate type: esriFieldTypeDate (OK)
  All 12 read / 8 write fields present
  
[STEP 1] Building lookup from gap_for_append_v2
  Lookup: 2,680 Call IDs

[STEP 2] Connecting to ArcGIS Online
  Connected as: [your AGOL username]
  Online layer total: 571,282
  Querying gap records...
  Total gap features found: 2,680
  
[STEP 3] Saving pre-update snapshot
  Saved: ...\_out\online_fix_YYYYMMDD_HHMMSS\snapshot.json
  Records: 2,680
  *** KEEP THIS FILE — rollback data ***
  
[STEP 4] Building update payloads
  26-011288 (OID 567831): 2026-02-06 10:00:00 -> 2026-02-03 08:15:23  DOW=Tuesday, Hr=8, disp=12.5 min
  ...
  Updates to apply: 2,680
  Already correct:  0
  
[STEP 5] DRY RUN — no changes will be made
  Would update 2,680 records in 14 batches
  Re-run with --live to apply.
  
[AUDIT]
  Updates prepared: 2,680
  AUDIT PASS: 2,680 updates vs 2680 expected (within 2%)
  
  >>> DRY RUN complete. Re-run with --live to apply. <<<
```

**Files Created:**
- `C:\HPD ESRI\04_Scripts\_out\online_fix_YYYYMMDD_HHMMSS\snapshot.json` (CRITICAL for rollback)
- `C:\HPD ESRI\04_Scripts\_out\online_fix_YYYYMMDD_HHMMSS\changes.json`
- `C:\HPD ESRI\04_Scripts\_out\online_fix_YYYYMMDD_HHMMSS\sample_before_after.csv`
- `C:\HPD ESRI\04_Scripts\_out\online_fix_YYYYMMDD_HHMMSS\fix.log`

**Review Before Going Live:**
1. Open `sample_before_after.csv` → verify before/after dates for your sample Call IDs
2. Check `changes.json` → review first 10 records
3. Confirm audit PASS and update count = 2,680

---

### Step 5: Fix Online Layer — LIVE (3-5 minutes)

**Purpose:** Apply surgical update to ArcGIS Online layer.

```powershell
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" fix_gap_calldate_online.py --live --expected-updates 2680 --sample-callids 26-011297,26-011300
```

**Expected Output:**
```
  Mode: LIVE
  
[STEP 5] APPLYING UPDATES TO AGOL (LIVE)
  Batch 1/14: 200 OK, 0 fail (running: 200/2680)
  Batch 2/14: 200 OK, 0 fail (running: 400/2680)
  ...
  Batch 14/14: 80 OK, 0 fail (running: 2680/2680)
  RESULTS: 2680 OK, 0 failed / 2680 total
  
[STEP 6] Post-update verification
  SAMPLE 26-011297 [OK]: online=2026-02-03 10:14:14, expected=2026-02-03 10:14:14
    dow=Tuesday, hr=10, yr=2026, disp=12.5, resp=25.7
  ...
  All verified!
  
[AUDIT]
  Updates succeeded: 2,680
  Updates failed: 0
  AUDIT PASS
  
  >>> To rollback: propy.bat fix_gap_calldate_online.py --rollback <<<
```

**Timing:**
- Batches (14 × 200 records): ~2-3 minutes
- Verification query: ~30 seconds
- Total: ~3-5 minutes

**Success Criteria:**
- ✅ RESULTS: 2680 OK, 0 failed
- ✅ All verified (no MISMATCH)
- ✅ AUDIT PASS
- ✅ Exit code: 0

**If Failures Occur:**
- Partial success (some records failed): Review `_out/*/fix.log` for failed OBJECTIDs
- Complete failure: Check ArcGIS API connection, schema, or run rollback

---

### Step 6: Dashboard Validation (5 minutes)

**Purpose:** Verify dashboard displays corrected data.

1. **Open Dashboard:**  
   https://hpd0223.maps.arcgis.com/apps/dashboards/d9315ff773484ca999ae3e16758cbec1

2. **Check Chronological Sort:**
   - Latest record should be **Feb 15, 2026** (not Feb 6)
   - Call list should show recent dates at top
   - No clustering of "2/6/26 10:00:00" for gap records

3. **Filter to Gap Period (Feb 3-15, 2026):**
   - Total calls: ~2,680
   - Map shows blue points across Hackensack
   - Sample records show correct dates:
     - 26-011297: Feb 3, 2026 10:14 AM
     - 26-011300: Feb 3, 2026 10:30 AM
     - etc.

4. **Check Derived Fields (Sample Record):**
   - Call ID: 26-011297
   - Call Date: 2026-02-03 10:14:14
   - Day of Week: Tuesday (not Monday/Saturday)
   - Hour: 10 (not 10:00:00 estimate)
   - Dispatch Time: ~12-15 minutes (realistic)

**Success Indicators:**
- ✅ Latest dashboard record: Feb 15, 2026
- ✅ Gap records (Feb 3-15): Show proper date progression
- ✅ Derived fields: Correct day-of-week, hour, response times
- ✅ Map points: All 571,282 visible

---

## Safety Protocols

### Rollback Capability

**If online update goes wrong:**
```powershell
# Restore from snapshot (reverts 2,680 records to pre-fix state)
propy.bat fix_gap_calldate_online.py --rollback
```

**What it does:**
- Reads most recent `snapshot.json` from `_out\online_fix_*\`
- Pushes original values back to ArcGIS Online
- Updates same 2,680 records (matched by OBJECTID)
- Takes ~2-3 minutes

**Local baseline rollback:**
```powershell
propy.bat fix_gap_calldate_local.py --rollback
```

### Safety Constraints

**Range Enforcement:**
- Only touches Call IDs in range `26-011288` to `26-014999`
- Numeric comparison (not lexicographic)
- Skips any records outside range

**Schema Validation:**
- Preflight checks all required fields exist before any updates
- Aborts with clear error if schema drifted
- Lists available fields for troubleshooting

**Timezone Hardening:**
- All datetime conversions forced to `America/New_York`
- Prevents DST/offset bugs on RDP server
- Probe script validates zero drift before proceeding

**Out-of-Range Metrics:**
- If dispatchtime <0 or >1440 minutes → set to NULL
- Prevents keeping stale response metrics based on old wrong calldate
- Logs count of nulled records

**Duplicate Detection:**
- Logs duplicate Call IDs (multi-unit calls)
- Updates all instances (expected behavior)
- Warns if duplicates found

**Audit Assertions:**
- `--expected-updates 2680` enforces count check
- Aborts if actual updates differ by >2% (default threshold)
- Exit code 1 if audit fails

---

## Verification Checklist

### After Step 5 (Online Fix LIVE)

**On RDP:**
```powershell
# Check last 3 gap records in online layer
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" -c "from arcgis.gis import GIS; from arcgis.features import FeatureLayer; gis = GIS('pro'); fl = FeatureLayer('https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0'); result = fl.query(where=\"callid IN ('26-011297','26-011300','26-012000')\", out_fields='callid,calldate,calldow,callhour'); [print(f\"{f.attributes['callid']}: {f.attributes['calldate']} dow={f.attributes['calldow']} hr={f.attributes['callhour']}\") for f in result.features]"
```

**Expected:**
```
26-011297: 1675435454000 dow=Tuesday hr=10
26-011300: 1675436400000 dow=Tuesday hr=10
26-012000: 1675536000000 dow=Saturday hr=14
```

**Convert epoch to human-readable:**
- 1675435454000 = 2026-02-03 10:14:14 Eastern

### Dashboard Visual Check

1. **Open dashboard** (link above)
2. **Remove all filters** → Total count: 571,282
3. **Sort by Call Date (newest first):**
   - Top record: Feb 15, 2026 (latest in dataset)
   - Gap records visible: Feb 3-15, 2026 (proper chronological progression)
   - No "2/6/26 10:00:00" clustering

4. **Filter to Feb 3-15, 2026:**
   - Count: ~2,680 records
   - Map: Blue points across city
   - Sample Call IDs: Click to verify correct dates/times

---

## Documentation Block (Add to Repo)

### Technical Notes: Gap Backfill Date Fix (v1.6.1)

**Problem Resolved:**  
Gap records from Feb 3-15, 2026 (2,680 records) were appended to ArcGIS Online with valid geometry but incorrect `calldate` values. All showed an estimated date of "2/6/26 10:00:00" instead of real dates from the source CAD export.

**Root Cause:**  
Perplexity session used estimation fallback logic when the correct dates existed in `gap_for_append_v2` table (field: `USER_Time_of_Call`). The estimation assigned the same timestamp to all gap records.

**Solution Architecture:**  
Surgical API update using ArcGIS API for Python to avoid truncating and reloading all 571K records:

1. **Local baseline fix:** Update `CFStable_GeocodeAddresses` with real dates from `gap_for_append_v2`
2. **Online fix:** Use `FeatureLayer.edit_features()` to update only the 2,680 affected records
3. **Derived field recalculation:** Update calldow, calldownum, callhour, callmonth, callyear based on corrected calldate
4. **Response metric recalculation:** Update dispatchtime, responsetime (depend on calldate)

**Scripts Created:**
- `scripts/probe_gap_record.py` (277 lines) - Timezone verification and field probe
- `scripts/fix_gap_calldate_local.py` (720 lines) - Local baseline date correction
- `scripts/fix_gap_calldate_online.py` (991 lines) - Online layer surgical update

**Key Features:**
- **Timezone hardening:** All conversions forced to America/New_York (prevents DST bugs)
- **Safety bounds:** Only touches Call IDs in range 26-011288 to 26-014999
- **Dry-run default:** No changes unless `--live` specified
- **Rollback capability:** Snapshot saved before updates, can restore with `--rollback`
- **Audit assertions:** `--expected-updates 2680` enforces count validation
- **Batch processing:** 200 records per API call (14 batches total)
- **Comprehensive logging:** JSON artifacts (snapshot, changes, summary) + CSV exports

**Safety Considerations:**
- **No truncate/reload:** Avoids geometry regression risk (v1.6.0 issue)
- **Zero downtime:** Dashboard remains operational during update
- **Reversible:** Exact rollback to pre-fix state via snapshot
- **Schema preflight:** Validates all required fields exist before queries
- **Out-of-range handling:** Nulls dispatch/response metrics if computed value invalid

**Performance:**
- Local baseline fix: ~1 minute (2,680 UpdateCursor operations)
- Online update: ~3-5 minutes (14 API batches of 200 records)
- Total: ~5-7 minutes vs 13+ minutes for full truncate/reload

**Testing Sequence:**
1. Probe (verify timezone, read-only)
2. Fix local — dry run → inspect changes.json → fix local — live
3. Fix online — dry run → inspect snapshot.json → fix online — live
4. Verify dashboard: chronological sort, proper dates, correct derived fields

**Outcome:**
- ✅ 571,282 total records with valid geometry and correct dates
- ✅ Gap closure complete: Feb 3-15, 2026
- ✅ Dashboard operational: Full coverage 2019-01-01 to 2026-02-15
- ✅ Chronological sort: Most recent calls display first

---

## Multi-AI Workflow Summary

This gap backfill completion involved coordinated work across four AI systems:

| AI | Role | Key Contributions |
|----|------|-------------------|
| **Perplexity** | Backfill Architecture | Gap data identification, geometry restoration, 2,680 records added to online layer |
| **Claude Opus** | Production Scripts | Three v4 scripts with CLI, dry-run, rollback, timezone hardening, audit assertions |
| **Code Copilot** | Safety Review | Identified 6 risks: range enforcement, timezone, stale metrics, duplicates, schema, NULL vs wrong |
| **Cursor AI** | Documentation & Git | This unified plan, CHANGELOG updates, git commits, handoff synthesis |

**Collaboration Pattern:**
- Perplexity: Architectural decisions and pipeline design
- Opus: Implementation (production-ready code with error handling)
- Copilot: Code review and safety audit
- Cursor: Documentation, git management, deployment coordination

---

## Troubleshooting

### If Dry Run Shows Wrong Count

**Problem:** Dry run reports updates ≠ 2,680  
**Check:**
1. Review `_out/*/changes.json` — how many records matched?
2. Check `gap_for_append_v2` table count on RDP
3. Verify Call ID range (26-011288 to 26-014999) matches your gap export
4. Check if some records already have correct dates (already_correct count)

**Solution:** Adjust `--expected-updates` or investigate source data mismatch

### If Timezone Probe Shows Mismatch

**Problem:** System epoch ≠ NY epoch  
**Check:**
1. Probe output: "System/NY mismatch: [delta]s"
2. RDP server timezone settings

**Solution:**  
- If delta is small (<60s) and consistent: Scripts use forced-NY, safe to proceed
- If delta is large (hours): RDP timezone config is wrong, fix server settings first

### If Online Update Fails (Exit Code 1)

**Problem:** Some records failed to update  
**Check:**
1. Review `_out/*/fix.log` for failed OBJECTIDs
2. Check ArcGIS Online edit permissions
3. Verify network connectivity to services1.arcgis.com

**Solution:**
- Partial failure: Rollback, fix issues, re-run
- Complete failure: Check AGOL connection via `GIS("pro")` test

### If Rollback Needed

**When to use:**
- Wrong dates applied (verification shows MISMATCH)
- Partial update (some records failed)
- Unexpected dashboard behavior

**How:**
```powershell
# Auto-rollback (uses most recent snapshot)
propy.bat fix_gap_calldate_online.py --rollback

# Specify snapshot
propy.bat fix_gap_calldate_online.py --rollback "C:\HPD ESRI\04_Scripts\_out\online_fix_20260216_220000\snapshot.json"
```

**Restores:**
- All 2,680 records to pre-fix state
- calldate + all 7 derived/response fields
- Matched by OBJECTID (exact restore)

---

## Files Modified in This Session

### Scripts (Already on RDP)
✅ `C:\HPD ESRI\04_Scripts\probe_gap_record.py`  
✅ `C:\HPD ESRI\04_Scripts\fix_gap_calldate_local.py`  
✅ `C:\HPD ESRI\04_Scripts\fix_gap_calldate_online.py`

### Documentation (Local Repo - Needs Update)
- [ ] `CHANGELOG.md` - Add v1.6.1 entry
- [ ] `SUMMARY.md` - Update status to v1.6.1 COMPLETE
- [ ] `README.md` - Add Gap Fix Scripts section
- [ ] `Claude.md` - Update current version and status
- [ ] `docs/perplexity_spaces_handoff.md` - Mark as COMPLETE

---

## Next Actions (After Successful Update)

1. **Dashboard screenshot:** Capture Feb 15 records at top (proof of correct sort)
2. **Git commit:** Version 1.6.1 with gap fix complete
3. **Update handoff:** Mark gap backfill COMPLETE in all docs
4. **Archive artifacts:** Save `_out/online_fix_*/` folder for audit trail
5. **Resume normal operations:** Daily automation (3 AM task) handles new data going forward

---

**Status:** READY TO EXECUTE  
**Prerequisites:** All three scripts deployed to RDP  
**Estimated Total Time:** 10-15 minutes (probe → local fix → online fix → verify)  
**Risk Level:** LOW (dry-run first, rollback available, surgical update only)

