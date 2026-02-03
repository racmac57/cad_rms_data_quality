# CAD Backfill Process - User Guide

## Quick Start

### One-Time Setup (On Server)

1. **Create Directory Structure**
   ```powershell
   # On HPD2022LAWSOFT via RDP
   New-Item -ItemType Directory -Path "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING" -Force
   New-Item -ItemType Directory -Path "C:\HPD ESRI\04_Scripts" -Force
   New-Item -ItemType Directory -Path "C:\HPD ESRI\05_Reports" -Force
   ```

2. **Copy Scripts to Server**
   - `config.json`
   - `run_publish_call_data.py`
   - `Test-PublishReadiness.ps1`
   - `Invoke-CADBackfillPublish.ps1`
   
   All to: `C:\HPD ESRI\04_Scripts\`

3. **Initialize Staging**
   ```powershell
   Copy-Item "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx" `
       "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx"
   ```

4. **Update ArcGIS Pro Model** (ONE TIME ONLY)
   - Open LawEnforcementDataManagement.aprx
   - Edit "Publish Call Data" tool
   - Change Input Spreadsheet to: `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx`
   - Save project

5. **Update Scheduled Task** (CRITICAL)
   - Edit `LawSoftESRICADExport` task
   - Add as FIRST action (before Publish Call Data):
   
   ```powershell
   # Daily staging refresh
   $src = "C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\ESRI_CADExport.xlsx"
   $tmp = "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx.tmp"
   $dst = "C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx"
   Copy-Item $src $tmp -Force
   Move-Item $tmp $dst -Force
   ```

---

## Backfill Workflow

### Step 1: Copy Polished Data to Server (Local Machine)

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\arcgis"
.\Copy-PolishedToServer.ps1

# Or test first:
.\Copy-PolishedToServer.ps1 -DryRun
```

### Step 2: Run Backfill Publish (On Server via RDP)

```powershell
cd "C:\HPD ESRI\04_Scripts"

# Test mode first (recommended)
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx" `
    -DryRun

# Actual run
.\Invoke-CADBackfillPublish.ps1 `
    -BackfillFile "C:\HPD ESRI\03_Data\CAD\Backfill\CAD_Consolidated_2019_2026.xlsx"
```

### Step 3: Verify Dashboard

- Open dashboard in web browser
- Check date range: 2019-01-01 to 2026-02-01
- Verify record counts match expected values
- Test key visualizations

---

## Key Files

| File | Location (Server) | Purpose |
|------|-------------------|---------|
| `config.json` | `C:\HPD ESRI\04_Scripts\` | Central configuration |
| `run_publish_call_data.py` | `C:\HPD ESRI\04_Scripts\` | Python runner for ArcGIS tool |
| `Test-PublishReadiness.ps1` | `C:\HPD ESRI\04_Scripts\` | Pre-flight checks |
| `Invoke-CADBackfillPublish.ps1` | `C:\HPD ESRI\04_Scripts\` | Main orchestrator |
| `ESRI_CADExport.xlsx` | `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\` | Staging file (model reads this) |
| `_LOCK.txt` | `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\` | Lock file (prevents collisions) |

---

## Troubleshooting

### Copy to Server Fails
- Run PowerShell as Administrator
- Test connection: `Test-NetConnection HPD2022LAWSOFT`
- Try admin share: `Copy-PolishedToServer.ps1 -UseAdminShare`
- Ask IT for dedicated SMB share

### Pre-Flight Checks Fail
- **Lock file exists**: Wait for current process to finish or remove stale lock manually
- **Scheduled task running**: Wait for nightly publish to complete
- **Geoprocessing active**: Close ArcGIS Pro or wait for processes to finish
- **Sheet name wrong**: Rename Excel sheet to "Sheet1"

### Publish Tool Fails
- Check `run_publish_call_data.py` output for geoprocessing messages
- Verify staging file exists and is not corrupted
- Check ArcGIS Pro license
- Review geodatabase locks

### Dashboard Doesn't Update
- Verify publish completed successfully (check GP messages)
- Check if service needs restart
- Verify output feature class was updated
- Clear browser cache

---

## Configuration

**Confirmed Values (DO NOT CHANGE):**
- Tool callable: `arcpy.TransformCallData_tbx1()`
- Toolbox: `C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.atbx`
- Project: `C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.aprx`

**Scheduled Tasks:**
- `LawSoftESRICADExport` (CAD daily publish)
- `LawSoftESRINIBRSExport` (NIBRS daily publish)

---

## Safety Features

1. **Lock file** prevents concurrent publishes
2. **Stale lock detection** auto-removes locks >2 hours with dead process
3. **Atomic file swaps** prevent partial reads during copy
4. **Hash verification** on backfill copies (size check on daily)
5. **Emergency restore** on error (best effort)
6. **Pre-flight checks** block unsafe runs

---

## Support

For issues or questions:
- Review this guide
- Check script output for error messages
- Review plan file: `.cursor\plans\streamlined_cad_backfill_process_*.plan.md`
- Contact: R. A. Carucci

---

**Last Updated:** 2026-02-02  
**Version:** 1.0.0  
**Status:** Production Ready
