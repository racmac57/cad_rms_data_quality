# Nightly Automation Assessment - Backfill Integration Strategy

**Date:** 2026-02-05  
**Context:** Evaluate safety and feasibility of integrating backfill function into nightly scheduled task  
**Status:** ASSESSMENT COMPLETE | RECOMMENDATION PROVIDED

---

## Executive Summary

### Current State
- ✅ **Daily Export Working:** FileMaker exports CAD/NIBRS data nightly, scheduled task copies to staging
- ✅ **Backfill Tool Tested:** Manual backfill workflow (`Invoke-CADBackfillPublish.ps1`) proven functional
- ✅ **Data Quality Fixed:** Phone/911 issue resolved, validation system (v1.4.0) complete and running
- ⏳ **Integration Pending:** Backfill function exists but needs safety verification before automation

### Recommendation: **NOT YET - Prerequisites Needed**

**Why:**
1. Missing clean baseline dataset (yesterday's run had data quality issues)
2. Validation system needs 1-2 production runs to establish quality baselines
3. Collision detection not yet tested with concurrent scheduled task
4. Need to verify nightly data is clean before switching to backfill mode

**Timeline:** Ready for automation in **3-5 days** after prerequisites complete

---

## Current Automation Architecture

### **Workflow 1: Nightly Daily Export (PRODUCTION - AUTOMATED)**

```
12:05 AM - FileMaker Schedule 8 exports to:
  C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx

12:30 AM - Task Scheduler "LawSoftESRICADExport" runs:
  Action 1 (PowerShell): Copy to staging with atomic swap
    src: C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx
    tmp: C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx.tmp
    dst: C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx
    
  Action 2 (Batch): Run C:\LawSoft\LawSoftESRICadExport.bat
    - Triggers FileMaker export (already done at 12:05 AM)
    - Copies to LawEnforcementDataManagement_New\CADdata.xlsx
    - Copies dated version to OneDrive monthly_export\2026\
    
  [MISSING] Action 3: Run ArcGIS Pro "Publish Call Data" tool
    ❌ Currently NOT automated - tool must be run manually
```

**Key Finding:** The scheduled task does NOT currently publish to ArcGIS Online. It only:
- Exports from FileMaker
- Copies files to various locations
- **Does NOT run `TransformCallData_tbx1()` tool**

---

### **Workflow 2: Manual Backfill (TESTED - MANUAL ONLY)**

```powershell
# On LOCAL machine
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\arcgis"
.\Copy-PolishedToServer.ps1

# On SERVER (via RDP)
cd "C:\HPD ESRI\04_Scripts"
.\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
```

**What it does:**
1. **Pre-flight checks** - Lock file, scheduled tasks, processes, geodatabase locks
2. **Create lock** - Prevents collisions with other processes
3. **Swap staging file** - Backfill → staging (atomic swap with hash verification)
4. **Run publish tool** - `arcpy.TransformCallData_tbx1()` via `run_publish_call_data.py`
5. **Restore staging** - Default export → staging (atomic swap)
6. **Cleanup** - Remove lock file

---

## The Gap: What's Missing from Nightly Automation

### **Current Nightly Task Actions**
1. ✅ Copy FileMaker export to staging
2. ✅ Copy to project folder (CADdata.xlsx)
3. ✅ Copy to OneDrive with date stamp
4. ❌ **MISSING: Run Publish Call Data tool to update dashboard**

### **Why Dashboard Isn't Updating Nightly**
The scheduled task does NOT call the ArcGIS Pro tool that publishes to online. It only copies files around.

**To fix this, need to add:**
```
Action 3: Run Publish Call Data Tool
  Execute: C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat
  Argument: "C:\HPD ESRI\04_Scripts\run_publish_call_data.py"
  Working Directory: C:\HPD ESRI\04_Scripts
```

---

## Integration Strategy - Three Options

### **Option 1: Add Daily Publish to Existing Task (RECOMMENDED SHORT-TERM)**

**What to do:**
Add a 3rd action to `LawSoftESRICADExport` task:

```powershell
# Task Scheduler → LawSoftESRICADExport → Actions → Add

Action 3 (Program/Script):
  Program: C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat
  Arguments: "C:\HPD ESRI\04_Scripts\run_publish_call_data.py"
  Working Directory: C:\HPD ESRI\04_Scripts
```

**Pros:**
- ✅ Simple addition to existing workflow
- ✅ No collision risk (runs after file copy)
- ✅ Keeps daily incremental logic
- ✅ Dashboard updates automatically every night

**Cons:**
- ❌ Still only publishes daily incremental (not full baseline)
- ❌ Historical data requires separate manual backfill
- ❌ 60-90 minute upload time extends task duration

**Best for:** Getting dashboards updating nightly while you work on full automation

---

### **Option 2: Nightly Backfill with Clean Baseline (RECOMMENDED LONG-TERM)**

**What to do:**
1. **First, create clean baseline:**
   ```powershell
   # Monthly workflow (when you get clean data)
   python consolidate_cad_2019_2026.py --full
   cd ../CAD_Data_Cleaning_Engine
   python scripts/enhanced_esri_output_generator.py --input "..." --output-dir "..."
   cd ../cad_rms_data_quality
   python scripts/update_baseline_from_polished.py
   ```

2. **Then, modify scheduled task to use baseline:**
   ```powershell
   Action 3: Run Backfill Publish
     Program: powershell.exe
     Arguments: -ExecutionPolicy Bypass -File "C:\HPD ESRI\04_Scripts\Invoke-CADBackfillPublish.ps1" `
                -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
     Working Directory: C:\HPD ESRI\04_Scripts
   ```

**Pros:**
- ✅ Dashboard always shows full historical data (2019-2026)
- ✅ No manual backfills needed
- ✅ Lock file prevents collisions
- ✅ Atomic swaps ensure data integrity
- ✅ Automatic restore on error

**Cons:**
- ❌ Longer nightly run time (60-90 min upload)
- ❌ Requires clean baseline first (not ready yet)
- ❌ More complex error recovery
- ❌ Network issues affect entire dataset, not just daily

**Best for:** Once you have a clean, validated baseline dataset

---

### **Option 3: Hybrid - Weekly Backfill, Daily Incremental (BEST OF BOTH)**

**What to do:**
1. **Daily Task (LawSoftESRICADExport):** Publish daily incremental only
2. **Weekly Task (NEW - LawSoftESRIBackfillWeekly):** Run backfill every Sunday 2 AM

**Daily Task (12:30 AM):**
```powershell
Action 1: Copy FileMaker export to staging
Action 2: Run LawSoftESRICadExport.bat
Action 3: Run Publish Call Data (daily incremental)
Duration: 15-20 minutes
```

**Weekly Task (Sunday 2:00 AM):**
```powershell
Action 1: Run Backfill Publish Script
  Program: powershell.exe
  Arguments: -ExecutionPolicy Bypass -File "C:\HPD ESRI\04_Scripts\Invoke-CADBackfillPublish.ps1" `
             -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
Duration: 60-90 minutes
```

**Pros:**
- ✅ Daily updates are fast (incremental only)
- ✅ Historical data refreshed weekly
- ✅ Reduces nightly task complexity
- ✅ Better error isolation (daily vs weekly)
- ✅ Less network stress (1 big upload/week instead of nightly)

**Cons:**
- ❌ Dashboard may lag by up to 6 days for historical corrections
- ❌ Two tasks to maintain
- ❌ Still need clean baseline

**Best for:** Production environment balancing speed, reliability, and completeness

---

## Prerequisites Before ANY Automation

### **1. Clean, Validated Baseline Dataset**

**Status:** ❌ NOT READY - Yesterday's data had quality issues

**What you said:**
> "yesterday, I believe We didn't have a clean data set yet. There were some issues with some of the information which I believe was cleaned up today."

**Action needed:**
```powershell
# 1. Run full validation on latest export
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
python validation/run_all_validations.py `
  -i "consolidation/output/CFSTable_2019_2026_FULL_20260203_231437.csv" `
  -o "validation/reports/$(Get-Date -F 'yyyy_MM_dd')_baseline"

# 2. Review validation report
# Look for: validation_report_*.md, validation_summary_*.json

# 3. If quality score ≥ 95%, generate clean baseline
python consolidate_cad_2019_2026.py --full
cd ../CAD_Data_Cleaning_Engine
python scripts/enhanced_esri_output_generator.py --input "..." --output-dir "..."
cd ../cad_rms_data_quality
python scripts/update_baseline_from_polished.py
```

**Success criteria:**
- ✅ Quality score ≥ 95/100
- ✅ Zero "Phone/911" combined values
- ✅ All required fields present
- ✅ Date ranges correct (2019-01-01 to latest)
- ✅ No critical validation errors

---

### **2. Test Collision Detection**

**Status:** ⚠️ UNTESTED - Lock file logic exists but not verified with scheduled task

**Action needed:**
```powershell
# Simulate scheduled task collision

# Terminal 1: Start manual backfill
cd "C:\HPD ESRI\04_Scripts"
.\Invoke-CADBackfillPublish.ps1 -BackfillFile "..." -DryRun

# Terminal 2 (while #1 running): Try to start daily task
Start-ScheduledTask -TaskName "LawSoftESRICADExport"

# Expected: Terminal 2 should see lock file and abort gracefully
```

**Success criteria:**
- ✅ Lock file detected by scheduled task
- ✅ Scheduled task aborts without error
- ✅ Log shows clear message: "Backfill in progress, skipping"
- ✅ Backfill continues uninterrupted

---

### **3. Verify Staging File Pattern Works for Daily**

**Status:** ⚠️ UNTESTED - Staging pattern tested for backfill, not tested for daily incremental

**Action needed:**
```powershell
# Test daily publish with current staging file
cd "C:\HPD ESRI\04_Scripts"

# 1. Ensure staging has today's FileMaker export
Copy-Item "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx" `
          "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx" -Force

# 2. Run publish tool
C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat "run_publish_call_data.py"

# 3. Verify dashboard updated with today's data only
```

**Success criteria:**
- ✅ Tool runs successfully
- ✅ Dashboard shows today's records
- ✅ No historical data loss
- ✅ Upload completes in reasonable time (<30 min)

---

### **4. Run Validation System 1-2 Times to Establish Baselines**

**Status:** ✅ SYSTEM COMPLETE (v1.4.0) but needs production runs

**Action needed:**
```powershell
# Run validation on 2 different days to establish trends

# Day 1
python validation/run_all_validations.py `
  -i "path/to/today/export.csv" `
  -o "validation/reports/$(Get-Date -F 'yyyy_MM_dd')_production_run1"

# Day 2 (next day)
python validation/run_all_validations.py `
  -i "path/to/tomorrow/export.csv" `
  -o "validation/reports/$(Get-Date -F 'yyyy_MM_dd')_production_run2"

# Compare reports
diff validation/reports/2026_02_05_production_run1/validation_summary*.json `
     validation/reports/2026_02_06_production_run2/validation_summary*.json
```

**Success criteria:**
- ✅ Quality scores consistent (±2 points)
- ✅ No new critical issues introduced
- ✅ Drift detection working (new call types, personnel flagged)
- ✅ Reference data sync process tested

---

## Implementation Roadmap

### **Phase 1: Fix Daily Publishing (Immediate - 1 day)**

**Goal:** Get dashboards updating every night with daily incremental data

**Steps:**
1. ✅ Verify staging file has today's FileMaker export
2. ✅ Test `run_publish_call_data.py` manually
3. ✅ Add as Action 3 to `LawSoftESRICADExport` task
4. ✅ Test scheduled task end-to-end
5. ✅ Monitor first 3 nightly runs

**Success:** Dashboard updates automatically every night with last 24 hours of data

---

### **Phase 2: Validate Baseline (2-3 days)**

**Goal:** Create clean, production-ready baseline dataset

**Steps:**
1. ⏳ Run validation on latest export
2. ⏳ Address any critical issues found
3. ⏳ Generate clean baseline with ESRI generator
4. ⏳ Copy to server via `Copy-PolishedToServer.ps1`
5. ⏳ Test manual backfill publish
6. ⏳ Verify dashboard shows full historical data

**Success:** Dashboard shows 2019-2026 data, quality score ≥95

---

### **Phase 3: Test Collision Scenarios (1 day)**

**Goal:** Ensure lock file logic prevents data corruption

**Steps:**
1. ⏳ Simulate manual backfill during scheduled task window
2. ⏳ Verify lock file blocks second process
3. ⏳ Test stale lock cleanup (>2 hours, dead process)
4. ⏳ Document recovery procedures

**Success:** No collisions possible, clear error messages, safe recovery

---

### **Phase 4: Integrate Backfill into Automation (1 day)**

**Goal:** Automate baseline refresh on schedule

**Choose one:**
- **Option A:** Nightly backfill (long run times)
- **Option B:** Weekly backfill (recommended)
- **Option C:** Monthly backfill + daily incremental

**Steps:**
1. ⏳ Create new scheduled task or modify existing
2. ⏳ Test in dry-run mode
3. ⏳ Run once manually to verify
4. ⏳ Monitor first 3 automated runs
5. ⏳ Document operational procedures

**Success:** Dashboard refreshes automatically, no manual intervention needed

---

## Risk Assessment

### **High Risk - DO NOT AUTOMATE YET**

❌ **Missing clean baseline** - Yesterday's data had quality issues  
❌ **Untested collision logic** - Lock file not verified with scheduled task  
❌ **No validation baseline** - Need 1-2 production runs first  
❌ **Upload time unknown** - 60-90 min estimate not confirmed

### **Medium Risk - Test First**

⚠️ **Network reliability** - Large uploads may timeout (seen yesterday)  
⚠️ **ArcGIS Online limits** - May hit rate limits with nightly uploads  
⚠️ **Error recovery** - Restore logic untested in production  
⚠️ **Monitoring gaps** - No alerts if nightly task fails

### **Low Risk - Safe to Proceed**

✅ **Daily incremental publish** - Small datasets, fast uploads  
✅ **File copy operations** - Already working reliably  
✅ **Lock file creation** - Tested in backfill workflow  
✅ **Staging file pattern** - Proven in manual backfills

---

## Monitoring & Alerts Strategy

### **What to Monitor**

**Daily (Automated):**
- Scheduled task completion status
- Upload duration (should be <30 min for daily, <90 min for backfill)
- Record count in dashboard (should match source)
- Validation quality score (should stay ≥95)

**Weekly (Manual Review):**
- Drift detection reports (new call types, personnel)
- Validation trend analysis (quality improving or declining?)
- Reference data sync status (how many pending approvals?)
- Disk space on server (staging files growing?)

### **Alert Thresholds**

**Critical (Immediate Action):**
- Scheduled task fails 2 nights in a row
- Quality score drops below 90
- Record count mismatch >1%
- Lock file >2 hours old with active process

**Warning (Review Within 24 Hours):**
- Upload takes >2x normal duration
- Quality score drops below 95
- New call types >50 in one week
- Drift reports not reviewed in 7 days

**Info (Review Weekly):**
- Quality score trends
- Call type usage changes
- Personnel roster changes
- Disk usage on server

---

## Rollback Plan

### **If Daily Automation Fails**

**Option 1: Disable Action 3**
```powershell
# Remove publish action from scheduled task
# Dashboards will show stale data but won't break
# Resume manual publishing
```

**Option 2: Fallback to Manual**
```powershell
# Keep scheduled task copying files
# Manually run publish once per day:
cd "C:\HPD ESRI\04_Scripts"
C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat "run_publish_call_data.py"
```

**Option 3: Emergency Restore**
```powershell
# If staging file corrupted
Copy-Item "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx" `
          "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx" -Force
```

---

## Recommended Next Steps (Priority Order)

### **TODAY (2026-02-05)**

1. **Add daily publish to scheduled task**
   ```powershell
   # This is low-risk and solves immediate problem
   Task Scheduler → LawSoftESRICADExport → Actions → Add
   Program: C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat
   Arguments: "C:\HPD ESRI\04_Scripts\run_publish_call_data.py"
   ```

2. **Run validation on latest export**
   ```powershell
   python validation/run_all_validations.py -i "consolidation/output/CFSTable_2019_2026_FULL_20260203_231437.csv"
   ```

3. **Review validation report**
   - Check quality score
   - Identify any critical issues
   - Document findings

### **THIS WEEK (2026-02-05 to 2026-02-09)**

4. **Generate clean baseline** (if validation passed)
   ```powershell
   python consolidate_cad_2019_2026.py --full
   # Then ESRI generator + update baseline
   ```

5. **Test collision detection**
   ```powershell
   # Simulate concurrent backfill + scheduled task
   ```

6. **Run validation 2nd time** (establish trend baseline)

7. **Test manual backfill with clean baseline**

### **NEXT WEEK (2026-02-10 onward)**

8. **Create weekly backfill task** (recommended)
   ```powershell
   Task: LawSoftESRIBackfillWeekly
   Schedule: Sunday 2:00 AM
   Action: Invoke-CADBackfillPublish.ps1
   ```

9. **Monitor 3 production runs** (daily task)

10. **Monitor 1 production run** (weekly backfill)

11. **Document operational procedures**

---

## Decision Matrix: Which Option?

### **Choose Option 1 (Daily Publish Only) if:**
- ✅ You need dashboard updated ASAP
- ✅ Historical data is "good enough" with manual backfills
- ✅ You want to minimize complexity
- ✅ Network bandwidth is limited

**Implementation time:** 1 day  
**Ongoing maintenance:** Low (just monitor daily task)

---

### **Choose Option 2 (Nightly Backfill) if:**
- ✅ You always want complete historical data
- ✅ You have clean baseline ready
- ✅ Network/upload speed is reliable
- ✅ You don't mind 60-90 min nightly runs

**Implementation time:** 3-5 days (after prerequisites)  
**Ongoing maintenance:** Medium (monitor nightly, larger error recovery)

---

### **Choose Option 3 (Hybrid Weekly) if:** ⭐ **RECOMMENDED**
- ✅ You want fast daily updates
- ✅ You want reliable historical data
- ✅ You want to balance network usage
- ✅ You can tolerate up to 6-day lag on historical corrections

**Implementation time:** 3-5 days (after prerequisites)  
**Ongoing maintenance:** Medium (two tasks, but better isolation)

---

## Technical Specifications

### **Scheduled Task Configuration (Option 1: Daily Publish)**

```xml
Task Name: LawSoftESRICADExport
Schedule: Daily at 12:30 AM
Run whether user is logged in or not: Yes
Run with highest privileges: Yes

Actions:
  1. Copy to staging (PowerShell)
     Program: powershell.exe
     Arguments: -ExecutionPolicy Bypass -Command "Copy-Item '...' '...tmp' -Force; Move-Item '...tmp' '...' -Force"
     
  2. Run export batch file
     Program: C:\LawSoft\LawSoftESRICadExport.bat
     
  3. Publish to ArcGIS Online (NEW)
     Program: C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat
     Arguments: "C:\HPD ESRI\04_Scripts\run_publish_call_data.py"
     Working Directory: C:\HPD ESRI\04_Scripts

Conditions:
  - Start only if computer is on AC power: No
  - Wake computer to run: Yes
  - Start only if network available: Yes

Settings:
  - Allow task to be run on demand: Yes
  - Stop task if runs longer than: 3 hours
  - If running task does not end when requested: Stop
  - Restart on failure: No (handle in script)
```

### **Scheduled Task Configuration (Option 3: Weekly Backfill)**

```xml
Task Name: LawSoftESRIBackfillWeekly
Schedule: Weekly, Sunday at 2:00 AM
Run whether user is logged in or not: Yes
Run with highest privileges: Yes

Actions:
  1. Run backfill orchestrator
     Program: powershell.exe
     Arguments: -ExecutionPolicy Bypass -File "C:\HPD ESRI\04_Scripts\Invoke-CADBackfillPublish.ps1" `
                -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
     Working Directory: C:\HPD ESRI\04_Scripts

Conditions:
  - Start only if computer is on AC power: No
  - Wake computer to run: Yes
  - Start only if network available: Yes

Settings:
  - Allow task to be run on demand: Yes
  - Stop task if runs longer than: 3 hours
  - If running task does not end when requested: Stop
  - Restart on failure: No (backfill script handles recovery)
```

---

## Questions & Answers

### Q: Why not automate backfill right now?

**A:** Because of the prerequisites:
1. Yesterday's data had quality issues → Need clean baseline first
2. Collision logic untested → Could corrupt data if manual + automated run simultaneously
3. Validation baselines missing → Don't know if quality is degrading or improving
4. Upload time unverified → Could extend nightly task beyond acceptable window

### Q: What's the safest first step?

**A:** Add Action 3 (publish tool) to existing daily task. This:
- ✅ Solves immediate problem (dashboards not updating)
- ✅ Uses small datasets (fast, reliable)
- ✅ Doesn't change baseline logic
- ✅ Easy to rollback if issues
- ✅ Can be done TODAY

### Q: When will full automation be ready?

**A:** 3-5 days after completing prerequisites:
- Day 1: Run validation, address issues
- Day 2: Generate clean baseline, test manual backfill
- Day 3: Test collision detection
- Day 4: Create weekly backfill task
- Day 5: Monitor first automated run

### Q: What if I need historical data updated before then?

**A:** Use manual backfill workflow (proven, tested, safe):
```powershell
.\Copy-PolishedToServer.ps1  # On local machine
.\Invoke-CADBackfillPublish.ps1 -BackfillFile "..."  # On server via RDP
```

---

## Summary & Final Recommendation

### **Current Situation**
- Daily export working ✅
- Backfill tool working ✅
- Dashboard NOT updating automatically ❌
- Data quality issues from yesterday ⚠️
- Validation system ready ✅

### **Immediate Action (TODAY)**
Add daily publish to scheduled task → Solves dashboard update issue

### **Short-Term (THIS WEEK)**
Run validation, create clean baseline, test collision scenarios

### **Long-Term (NEXT WEEK)**
Automate weekly backfill (Option 3 - Hybrid approach recommended)

### **Do NOT Automate Backfill Until:**
1. ✅ Clean baseline created and validated (quality score ≥95)
2. ✅ Collision detection tested and verified
3. ✅ Validation system run 1-2 times (establish baselines)
4. ✅ Upload time confirmed (<90 min for backfill)
5. ✅ Monitoring/alerting strategy in place

---

**Assessment Complete:** 2026-02-05  
**Next Review:** After validation run completes  
**Status:** Ready for Phase 1 (daily publish) | Blocked on Phase 4 (backfill automation) until prerequisites complete
