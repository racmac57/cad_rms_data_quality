Subject: Assistance Needed - Model Builder Hang During Large Dataset Backfill (754K Records)

---

Hi Chris,

I hope this email finds you well. I'm reaching out for guidance on an issue we're experiencing with the "Publish Call Data" Model Builder tool you helped us develop for our ArcGIS dashboard.

## What We're Attempting

We're performing a one-time historical backfill to update our CAD dashboard with 754,409 cleaned and validated records spanning from 2019-01-01 to 2026-02-03. This backfill is critical to:
- Fix a data quality issue (Phone/911 combined values now properly separated)
- Provide complete 7+ years of historical context for analysis
- Establish a clean baseline before resuming daily automated updates

## Actions Taken

**Attempt 1 (Feb 4, ~9:00 PM):**
- Used standard backfill orchestrator: `Invoke-CADBackfillPublish.ps1`
- File: `CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx` (76.1 MB, 754,409 records)
- Model executed via `arcpy.TransformCallData_tbx1()` through propy.bat
- Process ran for ~75 minutes, streaming geocoding warnings normally

**Attempt 2 (Feb 5, ~12:30 AM):**
- Identical approach with same file
- Same behavior observed

## Outcome

Both attempts failed with identical symptoms:
1. **Geocoding phase progressed normally** for ~60-75 minutes
2. **Last warning displayed:** `WARNING 000635: Skipping feature 564916 because of NULL or EMPTY geometry.`
3. **Process hung indefinitely** at ~75% completion (564,916 of 754,409 features)
4. **Minimal CPU activity:** 0.015 seconds over 5-second intervals (essentially idle)
5. **No error messages** generated in:
   - ArcGIS Pro geoprocessing logs
   - Python crash dumps
   - Windows Event Log
6. **Termination:** After 10+ minutes of no activity, terminated with exit code -1

**Note:** Our emergency restore mechanism successfully cleaned up both times (killed process, removed lock file, restored staging file).

## Pain Points

### 1. Silent Hang (Most Critical)
- Process appears to hang between geocoding completion and the next step ("Join Attributes From Polygon")
- No timeout handling or progress indicators
- No error logs to diagnose root cause

### 2. Inconsistent Behavior
- **Previous successful run (Feb 3):** Same dataset (~565K records), same geocoding warnings at feature 564916, but **completed successfully** in ~2 hours
- **Current attempts:** Identical warnings at feature 564916, but **hangs indefinitely**
- Suggests external factor (network, ArcGIS Online server load, database state?)

### 3. Performance/Scale Concerns
- 754K records appears to be near the threshold where the process becomes unstable
- Geocoding generates 2,000+ "NULL or EMPTY geometry" warnings (expected for incomplete addresses)
- Large file uploads to ArcGIS Online may be timing out without proper error handling

### 4. Lack of Diagnostic Information
- Cannot determine if issue is:
  - Network timeout uploading to ArcGIS Online
  - Geodatabase lock contention
  - Memory exhaustion
  - Specific problematic records at/around feature 564916

## Comparison with Successful Run

**Successful (Feb 3, 2026):**
- Last geocoding warning: Feature 564916 ✓
- **Continued to:** "Join Attributes From Polygon (2)" → Success
- Completion time: ~2 hours

**Failed (Feb 4 & 5, 2026):**
- Last geocoding warning: Feature 564916 ✓
- **Hung after:** Geocoding completion (never reached "Join Attributes")
- No subsequent log entries

## Technical Environment

- **Server:** Windows Server (via RDP)
- **ArcGIS Pro Version:** [Current production version]
- **Toolbox:** `LawEnforcementDataManagement.atbx`
- **Model:** TransformCallData (callable: `arcpy.TransformCallData_tbx1()`)
- **Python Environment:** ArcGIS Pro's propy.bat
- **Feature Layer:** Publishing to ArcGIS Online
- **Workflow:** Automated via PowerShell orchestrator with staging file pattern

## Questions for ESRI

1. **Timeout Configuration:** Is there a way to configure explicit timeouts for:
   - Geocoding operations
   - Feature layer publishing to ArcGIS Online
   - Network operations

2. **Progress Monitoring:** Can we add more granular logging between major model steps to identify where the hang occurs?

3. **Batch Processing:** Would splitting into smaller batches (~150K records each) be advisable? If so, should we:
   - Use "Append" mode for subsequent batches?
   - Truncate and reload the feature layer entirely?

4. **API Alternative:** For datasets of this size, would you recommend bypassing Model Builder and using the ArcGIS REST API directly for feature uploads?

5. **Best Practices:** What's the recommended maximum record count for a single Model Builder execution? Should we implement a different workflow for historical backfills vs. daily incremental updates?

6. **Diagnostic Logs:** Are there additional ArcGIS Pro log files we should check for clues about what's happening during the silent hang?

## Planned Next Steps

We're planning to:
1. **Test with smaller dataset** (2024-2026 only, ~100K records) to isolate whether it's size-related
2. **Implement batch processing** if the test succeeds (4 batches of ~150K records)
3. **Develop API upload approach** if Model Builder proves unreliable for this scale

However, we'd greatly appreciate your guidance before proceeding, as you have deep knowledge of the model's design and intended use cases.

## Data Quality Confirmation

For context, our data is high quality and ready for deployment:
- **Validation Score:** 99.97%
- **Data Issues:** Zero "Phone/911" combined values (properly separated)
- **File Integrity:** SHA256 verified
- **Completeness:** No missing date ranges

The issue appears to be purely with the publishing mechanism, not the data itself.

## Request

Could you please advise on:
- Whether this is a known limitation with datasets of this size
- Recommended approaches for large historical backfills
- Any configuration changes we should make to the model or environment
- Whether you've seen similar hanging behavior with other clients

We're available for a call if that would be more efficient for troubleshooting. Our timeline is flexible - we'd rather implement the right solution than rush a workaround.

Thank you for your time and expertise. We truly appreciate the work you've done on this model, and it's been performing excellently for our daily automated updates. This is our first large-scale historical backfill, so any guidance would be invaluable.

Best regards,

Robert Carucci
City of Hackensack - Police Department
Data Systems Administrator

---

**Attachments (if needed):**
- BACKFILL_INVESTIGATION_20260205.md (detailed technical investigation)
- 2026_02_03_publish_call_data_tbx1.md (successful run log for comparison)
