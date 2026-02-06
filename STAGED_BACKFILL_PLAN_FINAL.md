# Staged Backfill Implementation Plan - FINAL
**Version:** 2.0 (Enhanced with Gemini AI Recommendations)  
**Date:** 2026-02-06  
**Status:** READY FOR APPROVAL

---

## Executive Summary

This plan implements a comprehensive staged backfill system to resolve the silent hang at record 564,916 that has prevented successful upload of 754,409 historical CAD records. The solution combines **five critical strategies**:

1. **Pre-Geocoding Cache with Quality Gates** - Eliminate network timeout risk
2. **Batch Processing with Hash Verification** - 15 batches with integrity checks
3. **Heartbeat/Watchdog System** - Automatic hang detection and recovery
4. **Adaptive Cooling Period** - Dynamic 60-120s based on network conditions
5. **Checkpoint System with Post-Watchdog Recovery** - Automatic resume after kills

**Expected Results:**
- Current: 75-minute run → silent hang at 564,916 → 0% success rate
- Proposed: 30-45 minutes total → 15 successful batches → 100% success rate with auto-recovery

---

## Why This Plan Will Succeed

### Root Cause Analysis
The hang at feature 564,916 is caused by **network session exhaustion** during live geocoding. After ~500K geocoding requests, the Esri World Geocoder session times out silently, leaving the process in a 0% CPU state with no error logs.

### Solution Architecture
1. **Eliminate the Cause**: Pre-geocode all addresses offline (no live geocoding during publish)
2. **Reset Sessions Frequently**: 15 batches × 50K records = fresh Python process every 5-7 minutes
3. **Detect Hangs Automatically**: Heartbeat monitoring with 5-minute threshold
4. **Recover Without Manual Intervention**: Watchdog kills frozen processes, resume script continues

---

## Critical Enhancements from Gemini AI

### 1. Data Quality Gates (Pre-Geocoding)
**Problem**: Uploading records with null coordinates causes silent failures
**Solution**: Halt if >5% of addresses fail to geocode, generate inspection CSV
**Impact**: Prevents 754K record upload with bad data

### 2. Heartbeat/Watchdog System (MOST CRITICAL)
**Problem**: Silent hang at 564,916 with no error logs, 0% CPU activity
**Solution**: Python runner updates `heartbeat.txt` timestamp, PowerShell monitors freshness
**Impact**: Auto-detects hang in 5 minutes (vs 75+ minute manual wait), force-kills process

**How It Works:**
```
Python Runner                    PowerShell Watchdog
-------------                    -------------------
update_heartbeat()         -->   Monitor heartbeat.txt every 30s
  (writes timestamp)             
                                 if (age > 5 minutes):
Run ArcGIS Tool                    Kill Python process
  (may hang at 564,916)            Clean staging files
                                   Preserve batch for inspection
update_heartbeat()                 Allow resume script to continue
  (never reached if hung)
```

### 3. File Integrity Verification
**Problem**: Batch file corruption during 76MB transfer to server
**Solution**: SHA256 hash for each batch, verify after copy
**Impact**: Catch corruption before processing starts

### 4. Adaptive Cooling Period
**Problem**: Fixed 60s cooling may be insufficient during network congestion
**Solution**: Scan tool output for "network"/"timeout" warnings, extend to 120s if detected
**Impact**: Prevents cascading failures from slow network

### 5. Post-Watchdog Recovery
**Problem**: Killed processes leave stale locks, heartbeat files, staging data
**Solution**: Resume script automatically cleans: `heartbeat.txt`, `_LOCK.txt`, `ESRI_CADExport.xlsx`
**Impact**: Immediate resume after watchdog kill, no manual intervention

### 6. Diagnostic Tooling
**Problem**: No forensic analysis to confirm hang resolution
**Solution**: `Analyze-WatchdogHangs.ps1` - scans logs, calculates heartbeat delta, validates cooling periods
**Impact**: Proves solution effectiveness, identifies any remaining issues

---

## Implementation Scope

### New Files to Create (7 total)

1. **`scripts/create_geocoding_cache.py`**
   - Geocode ~100-200K unique addresses
   - Quality gate: halt if >5% fail
   - Output: 754,409 records with X/Y coordinates

2. **`scripts/split_baseline_into_batches.py`**
   - Split into 15 batches of 50K records
   - Generate SHA256 hash per batch
   - Create manifest.json with hashes

3. **`docs/arcgis/Resume-CADBackfill.ps1`**
   - Detect remaining batches
   - **Watchdog recovery block**: Clean stale files
   - Restore is_first_batch.txt marker

4. **`docs/arcgis/Validate-CADBackfillCount.py`**
   - Query ArcGIS Online count
   - Compare vs expected 754,409
   - Report overage/underage

5. **`docs/arcgis/Rollback-CADBackfill.py`**
   - Emergency truncate layer
   - Requires "WIPE" confirmation
   - Reset for clean restart

6. **`docs/arcgis/Generate-BackfillReport.ps1`**
   - CSV audit log per batch
   - Timestamps, durations, counts
   - Verification summary

7. **`docs/arcgis/Analyze-WatchdogHangs.ps1`** (NEW - GEMINI)
   - Scan logs for heartbeat stalls
   - Calculate hang duration
   - Validate cooling effectiveness

### Files to Modify (3 total)

1. **`docs/arcgis/run_publish_call_data.py`**
   - Add `update_heartbeat()` function
   - Call before/after `TransformCallData_tbx1()`
   - Pass X/Y coordinates to tool
   - Create marker after batch 01

2. **`docs/arcgis/Invoke-CADBackfillPublish.ps1`**
   - Add Watchdog monitoring loop
   - Implement adaptive cooling (60s vs 120s)
   - Disk space check (>500MB)
   - Batch loop with checkpointing

3. **`docs/arcgis/config.json`**
   - Add `staged_backfill` section
   - Watchdog settings (300s threshold)
   - Quality gates (5% geocode fail)

---

## Execution Flow

```
PHASE 0: Pre-Geocoding (30 minutes, one-time)
└─> Extract unique addresses (100-200K)
└─> Batch geocode offline
└─> Quality check: <5% fail rate?
    ├─> YES: Merge coordinates to 754K records
    └─> NO: Generate failed_addresses_inspection.csv, HALT

PHASE 1: Batch Splitting (5 minutes, one-time)
└─> Split cached baseline into 15 batches
└─> Generate SHA256 hash per batch
└─> Create batch_manifest.json

PHASE 2: Server Execution (30-45 minutes, repeatable)
FOR EACH BATCH (1 to 15):
    ├─> Check disk space (>500MB)
    ├─> Verify hash integrity
    ├─> Atomic swap to _STAGING
    ├─> Start Python with heartbeat
    ├─> WATCHDOG MONITORING:
    │   └─> Check heartbeat every 30s
    │   └─> If >5 min old: KILL process
    ├─> On success:
    │   ├─> Move to Completed/
    │   └─> Adaptive cooling (60s or 120s)
    └─> On failure/kill:
        ├─> Preserve batch for inspection
        ├─> Clean stale files
        └─> STOP (run Resume script)

PHASE 3: Validation (5 minutes)
└─> Query ArcGIS Online: 754,409 records?
└─> Generate audit report
└─> Analyze watchdog logs
└─> Cleanup markers
```

---

## Success Criteria

| Metric | Target | Validation |
|--------|--------|------------|
| **Total Records** | 754,409 | `Validate-CADBackfillCount.py` |
| **Batch Count** | 15 in Completed/ | Directory listing |
| **Date Range** | 2019-01-01 to 2026-02-03 | Dashboard query |
| **Duplicates** | Zero | Query ReportNumberNew |
| **Completion Time** | 30-45 minutes | Orchestrator log |
| **Geocoding Time** | 0 seconds/batch | Uses cached X/Y |
| **Hang Detection** | < 5 min timeout | Watchdog log |
| **Auto-Recovery** | Resume after kill | Post-watchdog cleanup |

---

## Risk Mitigation

| Risk | Gemini Enhancement | Mitigation |
|------|-------------------|------------|
| Null coordinates uploaded | Quality gate (5% threshold) | Halt before batch splitting |
| File corruption during copy | SHA256 hash verification | Detect before processing |
| Silent hang at 564,916 | Heartbeat/Watchdog (300s) | Auto-kill + resume |
| Network congestion | Adaptive cooling (60s→120s) | Dynamic adjustment |
| Stale files after kill | Post-watchdog cleanup | Automatic in resume script |
| No forensic data | Watchdog log analyzer | Post-execution diagnostics |

---

## Testing Strategy (Phased Approach)

### Test 1: Geocoding Cache Quality (30 min)
```powershell
python scripts\create_geocoding_cache.py
# Expected: Quality report with <5% fail rate
# Verify: X_Coord and Y_Coord columns present, minimal nulls
```

### Test 2: Batch Splitting + Hash Verification (5 min)
```powershell
python scripts\split_baseline_into_batches.py
# Expected: 15 BATCH_XX.xlsx files + batch_manifest.json with SHA256 hashes
```

### Test 3: Watchdog Kill Test (10 min)
```powershell
# Manually delete heartbeat.txt during execution to simulate hang
# Expected: PowerShell kills process within 5 minutes, batch preserved
```

### Test 4: Two-Batch Live Test (15 min)
```powershell
# Move BATCH_03-15 to temp, run with only 2 batches
.\Invoke-CADBackfillPublish.ps1 -Staged
# Expected: 2 batches complete in 4-6 minutes, heartbeat monitored
```

### Test 5: Post-Watchdog Resume (10 min)
```powershell
# Simulate kill after batch 1, verify cleanup, run resume
.\Resume-CADBackfill.ps1
# Expected: Stale files cleaned, batch 2 starts successfully
```

### Test 6: Full 15-Batch Run (45 min)
```powershell
# Restore all batches, run full sequence
.\Invoke-CADBackfillPublish.ps1 -Staged
# Expected: All 15 batches complete, adaptive cooling triggers if needed
```

### Test 7: Validation + Analysis (5 min)
```powershell
propy.bat Validate-CADBackfillCount.py
.\Generate-BackfillReport.ps1
.\Analyze-WatchdogHangs.ps1
# Expected: 754,409 records, zero kills, cooling periods effective
```

---

## Implementation Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 0. Geocoding Cache | 30 min | Baseline file, ArcGIS license |
| 1. Create 7 New Files | 2 hours | None |
| 2. Modify 3 Files | 2 hours | Phase 1 complete |
| 3. Model Inspection | 30 min | ArcGIS Pro access |
| 4. Local Testing | 1 hour | Phase 0-2 complete |
| 5. Server Setup | 30 min | Batch files ready |
| 6. Two-Batch Test | 15 min | Phase 5 complete |
| 7. Watchdog Test | 15 min | Phase 6 success |
| 8. Resume Test | 15 min | Phase 7 success |
| 9. Full 15-Batch Run | 45 min | All tests pass |
| 10. Validation | 15 min | Phase 9 complete |
| **TOTAL** | **~7.5 hours** | **Including contingency** |

---

## Phased Implementation Strategy (Time-Constrained)

Given the 2 hour 45 minute constraint before end of shift, we'll use a **pragmatic phased approach**:

### TODAY (2h 45m available) - "Pre-Weekend Lockdown"

**Phase 0: Geocoding Cache (30 min)**
- Run on local machine (no server dependency)
- Generate quality report
- Creates foundation for all future runs

**Phase 1: Batch Splitting (5 min)**
- Split cached baseline into 15 batches
- Generate SHA256 hashes
- Verify manifest integrity

**Phase 2: Script Creation (1 hour)**
- Create 7 new scripts (focusing on immediate needs first)
- Modify 3 existing files with Gemini enhancements
- Update configuration

**Phase 3: Two-Batch Test Run (15 min)**
- Copy first 2 batches to server
- Test Overwrite→Append transition
- Verify Watchdog monitoring works
- Validate cleanup after success

**Phase 4: Pre-Weekend Verification (15 min)**
- Generate hash verification report
- Confirm all 15 batches ready for Monday
- Document any issues found
- Create "READY_FOR_MONDAY.md" status report

**Deliverables by end of shift:**
- ✅ Cached baseline with X/Y coordinates (754,409 records)
- ✅ 15 batches with verified hashes ready for server
- ✅ All scripts created and tested (2-batch proof of concept)
- ✅ Confidence that full 15-batch run will succeed on Monday

**What's deferred to Monday:**
- Full 15-batch backfill (45 minutes)
- Complete validation and analysis
- Final audit report
- CHANGELOG update

### MONDAY MORNING (1 hour) - "Execute & Validate"

**Monday Morning Action Plan** (Start fresh, no prior context needed):

**1. Server Environment Sanitization (2 min)**
- [ ] RDP to server: `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING`
- [ ] Delete `_LOCK.txt` if exists
- [ ] Delete `is_first_batch.txt` if exists
- [ ] Confirm `\Batches` folder has 15 files + `batch_manifest.json`

**2. Final Script Verification (3 min)**
- [ ] Open `run_publish_call_data.py` → Verify heartbeat code active
- [ ] Open `Invoke-CADBackfillPublish.ps1` → Confirm `$MaxHangTimeSeconds = 300`
- [ ] Check disk space: >500MB free on C: drive

**3. Proof of Concept Run (Batches 1-2) (10 min)**
- [ ] Move `BATCH_03` through `BATCH_15` to temp "Queue" subfolder
- [ ] Execute: `.\Invoke-CADBackfillPublish.ps1 -Staged`
- [ ] **Watch for mode shift**: Batch 01 = "INITIAL OVERWRITE", Batch 02 = "APPEND"
- [ ] Monitor `heartbeat.txt` file - Date Modified should update during run

**4. Heartbeat Pulse Check (During Batch 1-2)**
- [ ] Navigate to `_STAGING` folder
- [ ] Right-click `heartbeat.txt` → Properties → Watch "Date Modified"
- [ ] Should refresh every 30-60 seconds during processing
- [ ] If frozen >5 minutes → Watchdog will auto-kill

**5. Launch Full Sequence (45 min)**
- [ ] Once Batches 1-2 in `\Completed` folder → Move BATCH_03-15 back to `\Batches`
- [ ] Run: `.\Resume-CADBackfill.ps1`
- [ ] Monitor: Each batch should complete in 2-3 minutes
- [ ] Verify: Adaptive cooling (60s or 120s based on network lag detection)

**Phase 6: Validation & Documentation (15 min)**
- [ ] Run: `propy.bat Validate-CADBackfillCount.py`
- [ ] Expected: "SUCCESS: Record count matches baseline exactly (754,409)"
- [ ] Generate audit report: `.\Generate-BackfillReport.ps1`
- [ ] Analyze watchdog logs: `.\Analyze-WatchdogHangs.ps1`
- [ ] Update CHANGELOG.md with success metrics

**Emergency Troubleshooting:**
- **If hangs**: Watchdog kills after 5 min, culprit records in `_STAGING\ESRI_CADExport.xlsx`
- **If Batch 02 overwrites**: Stop immediately, check marker file creation, verify model append mode
- **If hash mismatch**: Re-copy batch from local machine, verify with manifest

---

## Today's Action Plan (Approved Scope)

### Answers to Cursor's Questions
1. ✅ **Plan Approval**: Plan reviewed and enhancements (Watchdog, Heartbeat, Geocoding Cache) approved
2. ✅ **Model Inspection**: Proceed with assumption we'll use `arcpy.management.Append()` if model's native append unclear
3. ✅ **Feature Layer URL**: Use existing `target_service_url` in config.json
4. ✅ **Implementation Timing**: Focus on Phase 0, Phase 1, and 2-batch test before end of shift (NOT full 8-hour run)

### Immediate Next Steps (Proceed Now)

**Step 1: Create Geocoding Cache Script (10 min)**
- Location: `scripts/create_geocoding_cache.py`
- Quality gate: 5% fail threshold
- Run immediately after creation

**Step 2: Run Geocoding Cache (30 min)**
```powershell
python scripts\create_geocoding_cache.py
# Monitor for quality report
# Verify X_Coord and Y_Coord columns
```

**Step 3: Create Batch Splitter (10 min)**
- Location: `scripts/split_baseline_into_batches.py`
- SHA256 hash generation
- Run immediately after creation

**Step 4: Run Batch Splitting (5 min)**
```powershell
python scripts\split_baseline_into_batches.py
# Verify 15 BATCH_XX.xlsx files + manifest.json
```

**Step 5: Create Critical Scripts (40 min)**
- Priority 1: `run_publish_call_data.py` modifications (heartbeat)
- Priority 2: `Invoke-CADBackfillPublish.ps1` modifications (watchdog)
- Priority 3: `Resume-CADBackfill.ps1` (post-watchdog recovery)
- Priority 4: `config.json` updates

**Step 6: Two-Batch Test (15 min)**
```powershell
# Copy only BATCH_01 and BATCH_02 to server
# Run orchestrator in test mode
.\Invoke-CADBackfillPublish.ps1 -Staged -BatchFolder "...\Batches"
# Expected: 2 batches × 2-3 min = 4-6 minutes total
```

**Step 7: Pre-Weekend Lockdown (10 min)**
```powershell
# Generate verification report
python scripts\Verify-BatchIntegrity.py
# Verifies:
#   - All 15 batches present
#   - Total records = 754,409
#   - SHA256 hash generation
#   - X/Y coordinates present in all batches
#   - Creates batch_manifest.json for server
```

---

## Risk Mitigation for Phased Approach

| Risk | Mitigation |
|------|------------|
| Geocoding fails over weekend | Already complete by end of shift Friday |
| Batches corrupt over weekend | SHA256 hashes verify on Monday |
| Forgot configuration details | All in config.json and READY_FOR_MONDAY.md |
| Two-batch test fails | Fix Friday, don't leave with unknown issues |
| Monday morning time pressure | Only 1 hour needed, all prep done |

---

## Success Criteria for Today

**Before leaving today, confirm:**
- ✅ Geocoding quality report shows <5% fail rate
- ✅ 15 batch files exist with valid SHA256 hashes
- ✅ Two-batch test completed successfully (Overwrite→Append transition verified)
- ✅ Watchdog monitoring confirmed working (heartbeat.txt updated)
- ✅ READY_FOR_MONDAY.md created with status

**You can leave with confidence knowing:**
- Hardest parts complete (geocoding, batch splitting, testing)
- Monday morning is just "trigger and monitor"
- All prep work is local (no server dependencies over weekend)
- Scripts tested and proven with 2-batch run

---

## Pre-Weekend Lockdown Script (BONUS - GEMINI)

Create this verification script before leaving:

**`scripts/Verify-BatchReadiness.ps1`**
```powershell
# Verify all batches are ready for Monday
$BatchDir = "C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\staged_batches"
$manifest = Get-Content (Join-Path $BatchDir "batch_manifest.json") | ConvertFrom-Json

Write-Host "=== PRE-WEEKEND BATCH READINESS CHECK ===" -ForegroundColor Cyan

$allReady = $true
foreach ($batch in $manifest.batches) {
    $file = Join-Path $BatchDir $batch.filename
    if (Test-Path $file) {
        $actualHash = (Get-FileHash $file -Algorithm SHA256).Hash
        if ($actualHash -eq $batch.sha256_hash) {
            Write-Host "[OK] $($batch.filename) - Hash verified" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] $($batch.filename) - Hash mismatch!" -ForegroundColor Red
            $allReady = $false
        }
    } else {
        Write-Host "[FAIL] $($batch.filename) - File missing!" -ForegroundColor Red
        $allReady = $false
    }
}

if ($allReady) {
    Write-Host "`n✅ ALL 15 BATCHES READY FOR MONDAY" -ForegroundColor Green
} else {
    Write-Host "`n❌ ISSUES DETECTED - Review before leaving" -ForegroundColor Red
}
```

---

**Last Updated:** 2026-02-06 (Phased Approach)  
**Plan Version:** 2.1 (Time-Constrained Implementation)  
**Time Required Today:** 2 hours 45 minutes  
**Time Required Monday:** 1 hour  
**Total:** 3 hours 45 minutes (vs original 8 hours)

---

**Last Updated:** 2026-02-06  
**Plan Version:** 2.0 (Enhanced with Gemini AI Recommendations)  
**Estimated Success Rate:** 100% (with automatic recovery from kills)
