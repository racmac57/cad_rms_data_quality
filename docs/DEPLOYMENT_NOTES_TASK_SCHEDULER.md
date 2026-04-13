# Task Scheduler Deployment Notes - ArcGIS Pro Monitoring
**Created:** 2026-02-15  
**Purpose:** Operational guidance for running `monitor_dashboard_health.py` under Windows Task Scheduler  
**Critical Context:** ArcGIS Pro authentication requirements and troubleshooting

---

## ⚠️ CRITICAL: ArcGIS Pro Authentication Requirement

### The #1 Failure Mode

**Symptom:**
- Monitor script exits with **code 4** consistently
- Error message: "Exception during validation" or "Unable to connect to GIS"
- Happens when run via Task Scheduler but works when run manually

**Root Cause:**
- `monitor_dashboard_health.py` uses `GIS("pro")` from ArcGIS API for Python
- This requires **cached ArcGIS Pro credentials** (named user sign-in)
- Task Scheduler "Run whether user is logged on or not" mode typically **does NOT have Pro sign-in context**
- Result: Authentication fails every time

### Why This Happens

```python
# In monitor_dashboard_health.py:
gis = GIS("pro")  # ← Requires active ArcGIS Pro session / cached credentials
```

**`GIS("pro")` depends on:**
1. Windows user profile has ArcGIS Pro installed
2. That user has signed into ArcGIS Pro at least once (cached credentials)
3. Task runs under the **same Windows account** that signed into Pro
4. If "Run whether user is logged on or not": cached credentials must be accessible to the task context

**Most common issue:**
- Task configured to "Run whether user is logged on or not"
- Task runs under `SYSTEM` account or different user
- No Pro sign-in context available → Exit code 4

---

## ✅ Recommended Task Scheduler Settings

### Initial Configuration (Stabilization Phase)

**Use these settings while testing and stabilizing:**

```
General Tab:
  ☑ Run only when user is logged on
  User account: <same account that's signed into ArcGIS Pro>
  
Triggers Tab:
  <as appropriate for your schedule>
  
Actions Tab:
  Program: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
  Arguments: -ExecutionPolicy Bypass -File "C:\HPD ESRI\04_Scripts\Invoke-CADBackfillPublish.ps1" -BackfillFile "..."
  Start in: C:\HPD ESRI\04_Scripts
  
Conditions Tab:
  ☐ Start the task only if the computer is on AC power (uncheck for server)
  ☑ Wake the computer to run this task (optional)
  
Settings Tab:
  ☑ Allow task to be run on demand
  ☐ Stop the task if it runs longer than: 3 hours (adjust as needed)
```

**Why "Run only when user is logged on":**
- Ensures Pro credentials are available
- Easier to troubleshoot (logs visible in same session)
- Monitor will succeed if user is signed into Pro

### Production Configuration (After Stabilization)

**If you need "Run whether user is logged on or not":**

1. **Service Account Setup:**
   - Create dedicated service account with ArcGIS Pro named user license
   - Sign into ArcGIS Pro as service account (cache credentials)
   - Keep session alive or re-authenticate periodically

2. **Task Settings:**
   ```
   ☑ Run whether user is logged on or not
   User account: <service_account>
   ☐ Do not store password (leave unchecked - credential required)
   ☑ Run with highest privileges
   ```

3. **Credential Persistence:**
   - Service account must remain signed into ArcGIS Pro
   - May require periodic re-authentication (org policy dependent)
   - Consider using ArcGIS Pro portal authentication tokens

4. **Alternative: Use `GIS("home")` fallback:**
   - Edit `monitor_dashboard_health.py` to prioritize `GIS("home")`
   - Requires ArcGIS Online portal authentication configured
   - Less dependent on local Pro installation state

---

## 📊 Monitor Output & Troubleshooting

### JSON Report Locations

**All monitor reports written to:**
```
C:\HPD ESRI\04_Scripts\_out\monitor_YYYYMMDD_HHMMSS.json
```

**Sample report structure:**
```json
{
  "timestamp_est": "2026-02-15T22:34:15.123456",
  "layer_url": "https://services1.arcgis.com/.../FeatureServer/0",
  "expected_wkids_ok": [3857, 102100],
  "sample_size": 1000,
  "max_null_geom_pct": 1.0,
  "total_count": 565470,
  "wkid": 3857,
  "effective_sample": 1000,
  "null_geom_count": 15,
  "null_geom_pct": 1.5,
  "status": "fail_geometry",
  "exit_code": 2
}
```

### Exit Code Reference

| Exit Code | Status | Meaning | Action Required |
|-----------|--------|---------|-----------------|
| **0** | OK | All checks passed | None - publish succeeded |
| **2** | Geometry Fail | >1% NULL geometry in sample | Investigate source data, check Prompt A patches |
| **3** | WKID Mismatch | Spatial reference not Web Mercator | Check layer projection, verify publish workflow |
| **4** | Connection/Auth Fail | Cannot connect to layer or GIS | Check ArcGIS Pro sign-in, network, credentials |

### Troubleshooting Guide

#### Exit Code 4: Connection/Authentication Failure

**If you see exit code 4, verify:**
- ✅ Task Scheduler "Run as" user matches ArcGIS Pro signed-in user
- ✅ ArcGIS Pro is activated/licensed for that user profile
- ✅ Run the smoke test interactively on RDP under that same account

**Check 1: ArcGIS Pro Sign-In**
```powershell
# Run manually as the task user:
C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat "C:\HPD ESRI\04_Scripts\monitor_dashboard_health.py"
echo $LASTEXITCODE
```

**If exit 4 when manual:**
- Open ArcGIS Pro
- Sign in with named user credentials
- Close Pro
- Re-run monitor script
- Should now exit 0 or 2 (depending on geometry state)

**Check 2: Task Scheduler User Context**
- Open Task Scheduler
- Right-click task → Properties → General tab
- Verify "Run only when user is logged on" is checked
- Verify user matches the one signed into Pro
- Try "Run" from Task Scheduler to test

**Check 3: Network Connectivity**
```powershell
# Test AGOL connectivity:
Test-NetConnection services1.arcgis.com -Port 443
```

#### Exit Code 2: Geometry Failure

**Meaning:**
- More than 1% of sampled features have NULL geometry
- Points won't display on dashboard

**Actions:**
1. Check if Prompt A patches are applied
2. Review publish script (verify XYTableToPoint logic)
3. Check source data for lat/lon values
4. Review JSON report for `null_geom_count` and `null_geom_pct`

**Example:**
```json
"null_geom_count": 150,
"null_geom_pct": 15.0,  // 15% missing - way over 1% threshold
"status": "fail_geometry",
"exit_code": 2
```

#### Exit Code 3: WKID Mismatch

**Meaning:**
- Layer spatial reference is not Web Mercator (3857 or 102100)
- Dashboard may not display correctly

**Actions:**
1. Check layer properties in ArcGIS Online
2. Verify publish workflow projects to EPSG:3857
3. Confirm source data CRS transformation

**Valid WKIDs:**
- `3857` = WGS 1984 Web Mercator Auxiliary Sphere
- `102100` = WGS 1984 Web Mercator (Esri variant)
- Both are functionally equivalent for AGOL

---

## 🧪 Smoke Test Commands

### Manual Test (PowerShell)

**Test 1: Run monitor directly**
```powershell
# Navigate to scripts directory:
cd "C:\HPD ESRI\04_Scripts"

# Run monitor via propy.bat:
C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat "C:\HPD ESRI\04_Scripts\monitor_dashboard_health.py"
echo $LASTEXITCODE
```

**Expected output:**
- Console shows validation steps and results
- Exit code appears after `echo $LASTEXITCODE`
- JSON file created in `_out\` directory

**Test 2: Run via PowerShell orchestrator (dry-run)**
```powershell
cd "C:\HPD ESRI\04_Scripts"

# Dry-run to see workflow without publishing:
.\Invoke-CADBackfillPublish.ps1 -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\test.xlsx" -DryRun
```

**Test 3: Verify Task Scheduler context**
```powershell
# Get task info:
$task = Get-ScheduledTask -TaskName "LawSoftESRICADExport"

# Show user context:
$task.Principal.UserId

# Show run mode:
$task.Principal.LogonType
```

**Valid LogonType values:**
- `InteractiveToken` = Run only when user is logged on ✅ (recommended initially)
- `Password` = Run whether user is logged on or not (requires credential management)

---

## 📝 Known Good Configuration

### Service URL (Confirmed 2026-02-15)

**CallsForService Layer:**
```
https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0
```

**Organization ID:** `JYl0Hy0wQdiiV0qh`  
**Service Name:** `CallsForService_2153d1ef33a0414291a8eb54b938507b`  
**Layer Index:** `0`

**Dashboard:**
- URL: `https://hpd0223.maps.arcgis.com/apps/dashboards/d9315ff773484ca999ae3e16758cbec1`
- Data Table: `https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data`

### Monitor Defaults

**Thresholds (hardcoded in script):**
- Sample size: `1000` features
- Max null geometry: `1.0%` (fail if >1%)
- Expected WKIDs: `{3857, 102100}`
- Output directory: `C:\HPD ESRI\04_Scripts\_out`

**Override via `config.json` (optional):**
```json
{
  "calls_for_service_layer_url": "https://services1.arcgis.com/.../FeatureServer/0",
  "monitor_out_dir": "C:\\HPD ESRI\\04_Scripts\\_out",
  "expected_wkids_ok": [3857, 102100],
  "monitor_sample_size": 1000,
  "monitor_max_null_geom_pct": 1.0
}
```

---

## 🔧 Quick Fixes for Common Issues

### Issue: "GIS('pro') failed, trying GIS('home')"

**Meaning:**
- Initial Pro connection failed
- Script attempting fallback to ArcGIS Online portal auth

**Resolution:**
```powershell
# 1. Open ArcGIS Pro
# 2. Sign in with named user
# 3. Close Pro (credentials cached)
# 4. Re-run monitor
```

### Issue: "Cannot find output directory"

**Symptom:**
```
Exception: [Errno 2] No such file or directory: 'C:\\HPD ESRI\\04_Scripts\\_out\\monitor_*.json'
```

**Resolution:**
```powershell
# Create _out directory:
New-Item -Path "C:\HPD ESRI\04_Scripts\_out" -ItemType Directory -Force
```

### Issue: Monitor hangs / takes forever

**Cause:**
- Large layer query (>1M features)
- Network latency to AGOL

**Resolution:**
- Reduce sample size in `config.json` (e.g., 500 instead of 1000)
- Check network connection to `services1.arcgis.com`

---

## 📋 Pre-Flight Checklist (Before Scheduling)

Before enabling Task Scheduler automation:

- [ ] ArcGIS Pro installed on server
- [ ] Named user signed into Pro at least once (credentials cached)
- [ ] Task configured to run as same user
- [ ] "Run only when user is logged on" initially checked
- [ ] Manual test passes with exit code 0 or 2
- [ ] JSON report created in `_out\` directory
- [ ] PowerShell orchestrator dry-run successful
- [ ] Backup folder structure exists (`00_Backups\`)
- [ ] Staging directory exists (`03_Data\CAD\Backfill\_STAGING\`)
- [ ] Heartbeat file path accessible

---

## 🚨 Emergency Recovery

**If monitor breaks Task Scheduler automation:**

1. **Disable monitor temporarily:**
   ```powershell
   # Edit Invoke-CADBackfillPublish.ps1
   # Comment out Step 6.5 (post-publish gate)
   # Re-deploy via Deploy-ToRDP-Simple.ps1
   ```

2. **Run publish without validation:**
   ```powershell
   # Use -SkipPreFlightChecks if needed (caution)
   .\Invoke-CADBackfillPublish.ps1 -BackfillFile "..." -SkipPreFlightChecks
   ```

3. **Check monitor directly:**
   ```powershell
   # Run isolated to diagnose:
   C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat "C:\HPD ESRI\04_Scripts\monitor_dashboard_health.py" > monitor_debug.log 2>&1
   ```

4. **Review JSON reports:**
   ```powershell
   # Check recent reports:
   Get-ChildItem "C:\HPD ESRI\04_Scripts\_out" | Sort-Object LastWriteTime -Descending | Select-Object -First 5
   ```

---

## 📚 Additional Resources

**Related Documentation:**
- `docs/RDP_DEPLOYMENT_VERIFICATION.md` - Deployment checklist
- `docs/PROMPT_B_IMPLEMENTATION_SUMMARY.md` - Monitor technical details
- `docs/arcgis/README.md` - ArcGIS workflow overview

**Log Locations:**
- Monitor output: `C:\HPD ESRI\04_Scripts\_out\monitor_*.json`
- Publish logs: `C:\HPD ESRI\04_Scripts\_out\` (if configured)
- Task Scheduler history: Task Scheduler → View → Show Task History

**Useful Commands:**
```powershell
# Check Pro Python environment:
C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat --version

# List installed packages:
C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat -m pip list | Select-String "arcgis"

# Test AGOL connectivity:
Test-NetConnection services1.arcgis.com -Port 443

# Check cached Pro credentials (indirect):
Test-Path "$env:APPDATA\ESRI\ArcGISPro"
```

---

## ✅ Success Indicators

Monitor is working correctly when:
- ✅ Manual test exits with 0 or 2 (not 4)
- ✅ JSON reports created consistently
- ✅ Task Scheduler runs complete without errors
- ✅ Exit code reflects actual dashboard state (geometry present/missing)
- ✅ Publish workflow fails loudly if geometry < 99%

