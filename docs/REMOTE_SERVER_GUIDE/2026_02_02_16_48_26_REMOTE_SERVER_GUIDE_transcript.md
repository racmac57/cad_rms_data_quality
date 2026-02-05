# Remote Server Guide

**Processing Date:** 2026-02-02 16:48:26
**Source File:** REMOTE_SERVER_GUIDE.md
**Total Chunks:** 1

---

# CAD Consolidated Dataset - Remote Server Guide
# ================================================================
# Working with the Consolidated CAD Dataset (2019-2026) on Remote Server
# ================================================================
# Date: 2026-01-31
# Server: HPD2022LAWSOFT (10.0.0.157)
# Purpose: Guide for using consolidated dataset with ArcGIS Pro on remote server
# ================================================================

## OVERVIEW

This guide provides instructions for working with the consolidated CAD dataset (2019-2026) on the remote server HPD2022LAWSOFT for use with ArcGIS Pro dashboards. ### Dataset Information

**File:** `CAD_ESRI_POLISHED_20260131_004142.xlsx` (friendly name: `CAD_Consolidated_2019_2026.xlsx`)

**Key Statistics:**
- **Total Records:** 716,420
- **Unique Case Numbers:** 553,624
- **Date Range:** 2019-01-01 to 2026-01-16
- **File Size:** 73.9 MB
- **Schema:** 20 ESRI-compatible columns
- **Quality:** EXCELLENT (99.9%+ field completeness)
- **RMS Backfill:** 41,137 PDZone values, 34 Grid values applied
- **Normalization:** Advanced v3.2 applied

### Important Notes

⚠ **Date Range Limitation:**
- Monthly file only contained data through 2026-01-16 (not full month through 01-30)
- Missing 14 days of January data (01-17 through 01-30)
- Tomorrow's update (01-31) will include full January data

✅ **Data Quality:**
- ReportNumberNew: 99.997% complete (22 nulls only)
- Incident: 99.96% complete (272 nulls only)
- How Reported: 100% complete
- Disposition: 100% complete
- All domains: 100% compliant

---

## PART 1: COPYING DATASET TO REMOTE SERVER

### Option A: Using PowerShell Script (Recommended)

**From local machine:**
```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
powershell -ExecutionPolicy Bypass -File .\copy_consolidated_dataset_to_server.ps1
```

**What the script does:**
1. Verifies source file exists
2. Checks server connectivity
3. Copies file to ESRI share: `\\10.0.0.157\esri\`
4. Attempts to copy to ESRIExport folder (if accessible)
5. Creates friendly filename: `CAD_Consolidated_2019_2026.xlsx`

### Option B: Manual Copy

**Step 1: Copy to ESRI Share**
```powershell
# From local machine
$source = "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final\CAD_ESRI_POLISHED_20260131_004142.xlsx"
$dest = "\\10.0.0.157\esri\CAD_Consolidated_2019_2026.xlsx"
Copy-Item -Path $source -Destination $dest -Force
```

**Step 2: Copy to ESRIExport Folder (via RDP)**
1. Connect to server via Remote Desktop
2. Copy file from `\\10.0.0.157\esri\CAD_Consolidated_2019_2026.xlsx`
3. Paste to `C:\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx`

### Option C: Copy via RDP Session

1. Connect to HPD2022LAWSOFT via Remote Desktop
2. Open File Explorer
3. Navigate to `\\10.0.0.157\esri` (or local OneDrive location)
4. Copy the file to `C:\ESRIExport\LawEnforcementDataManagement_New\`

---

## PART 2: ACCESSING THE DATASET ON REMOTE SERVER

### File Locations

**Network Share (accessible from local machine):**
```
\\10.0.0.157\esri\CAD_Consolidated_2019_2026.xlsx
```

**Server Local Path (when connected via RDP):**
```
C:\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx
```

**Alternative Path (if exists):**
```
C:\HPD ESRI\03_Data\CAD\CAD_Consolidated_2019_2026.xlsx
```

### Verification Commands

**From local machine:**
```powershell
# Check if file exists on server
Test-Path "\\10.0.0.157\esri\CAD_Consolidated_2019_2026.xlsx"

# Get file info
Get-Item "\\10.0.0.157\esri\CAD_Consolidated_2019_2026.xlsx" | 
    Select-Object Name, Length, LastWriteTime
```

**On remote server (via RDP):**
```powershell
# Check if file exists
Test-Path "C:\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx"

# Get file info
Get-Item "C:\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx" | 
    Select-Object Name, Length, LastWriteTime
```

---

## PART 3: IMPORTING INTO ARCGIS PRO

### Prerequisites

1. Connected to remote server via Remote Desktop
2. ArcGIS Pro installed and licensed
3. Consolidated dataset copied to server (see Part 1)
4. Active ArcGIS Pro project open

### Import Steps

**Step 1: Open ArcGIS Pro Project**
```
Path: C:\Users\carucci_r\OneDrive - City of Hackensack\10_Projects\ESRI\2026_dashboards\Projects\
Or: \\HPD2022LAWSOFT\ESRIExport\LawEnforcementDataManagement_New\
```

**Step 2: Add Consolidated Dataset as Data Source**

1. In ArcGIS Pro, open the **Catalog** pane
2. Right-click **Folders** → **Add Folder Connection**
3. Browse to `C:\ESRIExport\LawEnforcementDataManagement_New\`
4. Click **OK**

**Step 3: Import Excel Data**

1. Right-click the folder connection → **Import** → **Table to Geodatabase**
2. **Input Rows:** Browse to `CAD_Consolidated_2019_2026.xlsx`
3. **Output Location:** Select your project geodatabase
4. **Output Table:** Name it `CAD_Consolidated_2019_2026`
5. Click **Run**

**Step 4: Verify Import**

1. Open the attribute table of the imported table
2. Check **Record Count:** Should be **716,420**
3. Verify date range: **2019-01-01** to **2026-01-16**
4. Check field completeness:
   - ReportNumberNew: ~22 nulls
   - Incident: ~272 nulls
   - How Reported: 0 nulls
   - Disposition: 0 nulls

### Expected Schema (20 ESRI Columns)

| Field Name | Type | Description |
|------------|------|-------------|
| ReportNumberNew | Text | Report/Case Number |
| Incident | Text | Call Type/Incident Type |
| How Reported | Text | How call was reported |
| Disposition | Text | Call disposition |
| TimeOfCall | DateTime | Date/Time of call |
| TimeDispatched | DateTime | Time unit dispatched |
| TimeEnroute | DateTime | Time unit en route |
| TimeOnScene | DateTime | Time unit on scene |
| TimeCallComplete | DateTime | Time call completed |
| Officer | Text | Officer/Unit assigned |
| PDZone | Text | Police zone |
| Grid | Text | Grid location |
| Address | Text | Location address |
| Apt | Text | Apartment/Unit number |
| City | Text | City |
| State | Text | State |
| ZIP | Text | ZIP code |
| Cross | Text | Cross street |
| CADNotes | Text | CAD notes/comments |
| ResponseType | Text | Response type |

---

## PART 4: UPDATING EXISTING ARCGIS PRO DATA SOURCES

### If You Have Existing Dashboard Using Daily Exports

**Background:**
Your current setup uses daily exports:
- `C:\ESRIExport\LawEnforcementDataManagement_New\CADdata.xlsx` (daily export)

**To Use Consolidated Dataset Instead:**

1. **Backup Current Project:**
   ```
   File → Save As → Copy Project
   Name: LawEnforcementDataManagement_BACKUP_20260131
   ```

2. **Update Data Source in Map:**
   - In **Catalog** pane, locate your existing CAD layer
   - Right-click layer → **Properties** → **Source** tab
   - Click **Set Data Source**
   - Browse to consolidated dataset: `CAD_Consolidated_2019_2026.xlsx`
   - Click **OK**

3. **Update ModelBuilder Tools (if applicable):**
   - Open ModelBuilder tool: `Publish Call Data`
   - Update **Input Spreadsheet** parameter:
     - Old: `C:\ESRIExport\LawEnforcementDataManagement_New\CADdata.xlsx`
     - New: `C:\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx`
   - Save model

4. **Validate Changes:**
   - Run model or refresh layer
   - Verify 716,420 records load correctly
   - Check date range: 2019-01-01 to 2026-01-16

### Switching Back to Daily Exports

**After backfill is complete:**
```
1. Update data source back to: CADdata.xlsx
2. Run model to process latest daily export
3. Dashboard will continue with daily updates
```

---

## PART 5: TROUBLESHOOTING

### Issue: File Not Found on Server

**Symptoms:**
- Cannot access `\\10.0.0.157\esri\CAD_Consolidated_2019_2026.xlsx`

**Solutions:**
1. Check server connectivity:
   ```powershell
   Test-Connection -ComputerName 10.0.0.157 -Count 4
   ```

2. Verify ESRI share exists:
   ```powershell
   Get-ChildItem "\\10.0.0.157\esri" | Select-Object Name
   ```

3. Check file permissions (may need admin rights)

4. Try copying to alternative location:
   ```powershell
   Copy-Item "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final\CAD_ESRI_POLISHED_20260131_004142.xlsx" `
            -Destination "\\HPD2022LAWSOFT\c$\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx"
   ```

### Issue: Import Fails in ArcGIS Pro

**Symptoms:**
- "Unable to read file" error
- Import completes but no records
- Schema errors

**Solutions:**

1. **Verify Excel File Format:**
   - File should be `.xlsx` (not `.xls` or `.csv`)
   - Open file in Excel to verify it's not corrupted
   - Expected records: 716,420

2. **Check File Path:**
   - Use local path on server (not UNC path)
   - `C:\ESRIExport\...` not `\\10.0.0.157\...`

3. **Import via Table to Table:**
   - Catalog pane → Right-click geodatabase
   - **Import** → **Table**
   - Select Excel file
   - Choose sheet (usually `Sheet1` or first sheet)

4. **Try Alternative Import Method:**
   - Convert Excel to CSV first:
     ```python
     import pandas as pd
     df = pd.read_excel("CAD_Consolidated_2019_2026.xlsx")
     df.to_csv("CAD_Consolidated_2019_2026.csv", index=False)
     ```
   - Import CSV instead

### Issue: Record Count Mismatch

**Expected:** 716,420 records

**If you see different count:**

1. **Check date range filter** (if applied during import)
2. **Verify all records imported:**
   ```sql
   -- In ArcGIS Pro Python window
   import arcpy
   arcpy.management.GetCount("CAD_Consolidated_2019_2026")
   ```

3. **Check for nulls in key fields:**
   - ReportNumberNew: Should have ~22 nulls
   - Incident: Should have ~272 nulls

4. **Verify date range:**
   ```sql
   SELECT MIN(TimeOfCall), MAX(TimeOfCall) FROM CAD_Consolidated_2019_2026
   ```
   - Expected: 2019-01-01 to 2026-01-16

### Issue: Broken Data Sources After Import

**Symptoms:**
- Red exclamation marks on layers
- "Data source not found" errors

**Solution:**

1. **Repair Data Sources:**
   - Right-click broken layer
   - **Properties** → **Source**
   - Click **Set Data Source**
   - Browse to new consolidated dataset

2. **Use Repair Script (if available):**
   - See `10_Projects\ESRI\2026_dashboards\04_Fix_Broken_References\`
   - Run `02_Repair-BrokenReferences.ps1`

3. **Verify Folder Connections:**
   - Catalog pane → **Folders**
   - Ensure `C:\ESRIExport\LawEnforcementDataManagement_New` is connected

---

## PART 6: TOMORROW'S UPDATE (01-31)

### What's Happening Tomorrow

**Download Full January Export:**
- File: `2026_01_01_to_2026_01_31_CAD_Export.xlsx`
- Will include complete January data (01-01 through 01-31)
- Current file only goes through 01-16

**Re-run Consolidation:**
```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
python consolidate_cad_2019_2026.py
```

**Expected Output:**
- New file: `CAD_ESRI_POLISHED_20260131_HHMMSS.xlsx`
- Will include data through 2026-01-31
- Record count will be higher (additional 15 days of data)

**Copy to Server:**
```powershell
powershell -ExecutionPolicy Bypass -File .\copy_consolidated_dataset_to_server.ps1
```

**Update ArcGIS Pro:**
- Replace old consolidated dataset with new version
- Or update data source to point to new file

---

## PART 7: KEY PATHS REFERENCE

### Local Machine

**Consolidated Dataset Source:**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final\CAD_ESRI_POLISHED_20260131_004142.xlsx
```

**Scripts:**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\
├── consolidate_cad_2019_2026.py
├── copy_consolidated_dataset_to_server.ps1
└── outputs\consolidation\
    ├── CONSOLIDATION_RUN_2026_01_30_SUMMARY.txt
    └── EXECUTIVE_SUMMARY_2026_01_30.txt
```

**Project Documentation:**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\10_Projects\ESRI\2026_dashboards\
├── README.md
├── CHANGELOG.md
├── SUMMARY.md
└── 04_Fix_Broken_References\
```

### Remote Server (HPD2022LAWSOFT)

**Network Shares:**
```
\\10.0.0.157\esri\
\\HPD2022LAWSOFT\ESRIExport\LawEnforcementDataManagement_New\
```

**Server Local Paths (via RDP):**
```
C:\ESRIExport\LawEnforcementDataManagement_New\
C:\HPD ESRI\03_Data\CAD\
C:\Program Files\FileMaker\FileMaker Server\Data\Documents\ESRI\
```

**ArcGIS Pro Projects:**
```
C:\Users\carucci_r\OneDrive - City of Hackensack\10_Projects\ESRI\2026_dashboards\Projects\
```

---

## PART 8: QUICK REFERENCE COMMANDS

### Copy File to Server
```powershell
# Copy to ESRI share
Copy-Item "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final\CAD_ESRI_POLISHED_20260131_004142.xlsx" `
          -Destination "\\10.0.0.157\esri\CAD_Consolidated_2019_2026.xlsx" -Force

# Verify copy
Get-Item "\\10.0.0.157\esri\CAD_Consolidated_2019_2026.xlsx" | 
    Select-Object Name, Length, LastWriteTime
```

### Check Server Connectivity
```powershell
# Ping server
Test-Connection -ComputerName 10.0.0.157 -Count 4

# Check ESRI share
Test-Path "\\10.0.0.157\esri"

# List files in ESRI share
Get-ChildItem "\\10.0.0.157\esri" | Select-Object Name, Length, LastWriteTime
```

### ArcGIS Pro Python Window
```python
import arcpy

# Get record count
result = arcpy.management.GetCount("CAD_Consolidated_2019_2026")
print(f"Record count: {result}")

# Check date range
with arcpy.da.SearchCursor("CAD_Consolidated_2019_2026", ["TimeOfCall"]) as cursor:
    dates = [row[0] for row in cursor if row[0] is not None]
    print(f"Min date: {min(dates)}")
    print(f"Max date: {max(dates)}")
```

---

## PART 9: RELATED DOCUMENTATION

### Consolidation Documentation
- **Detailed Summary:** `outputs/consolidation/CONSOLIDATION_RUN_2026_01_30_SUMMARY.txt`
- **Executive Summary:** `outputs/consolidation/EXECUTIVE_SUMMARY_2026_01_30.txt`
- **Validation Report:** `CAD_Data_Cleaning_Engine/data/03_final/CAD_ESRI_POLISHED_20260131_004142_validation_report_20260131_005543.md`
- **Normalization Report:** `CAD_Data_Cleaning_Engine/data/03_final/normalization_report_20260131_004142.md`

### ArcGIS Pro Project Documentation
- **Project README:** `10_Projects/ESRI/2026_dashboards/README.md`
- **Change Log:** `10_Projects/ESRI/2026_dashboards/CHANGELOG.md`
- **Project Summary:** `10_Projects/ESRI/2026_dashboards/SUMMARY.md`
- **Fix Broken References:** `10_Projects/ESRI/2026_dashboards/04_Fix_Broken_References/`

### ESRI Dashboard Handoff
- **Handoff Documentation:** `KB_Shared/04_output/ChatGPT-ESRI_Dashboard_Handoff/`
- **Technical Summary:** See handoff package for comprehensive technical details

---

## SUPPORT

**For issues with:**
- **Consolidation script:** See `CONSOLIDATION_RUN_2026_01_30_SUMMARY.txt`
- **Server connectivity:** See network administrator
- **ArcGIS Pro import:** See `04_Fix_Broken_References/` documentation
- **Daily exports:** See `10_Projects/ESRI/2026_dashboards/README.md`

**Contact:** R. A. Carucci

---

**Document Created:** 2026-01-31  
**Last Updated:** 2026-01-31  
**Version:** 1.0  
**Status:** Active

================================================================
END OF GUIDE
================================================================

