# ArcGIS Import Guide for CAD Consolidated Dataset

This directory contains scripts and documentation for importing the consolidated CAD dataset (2019-2026) into ArcGIS Pro geodatabases.

## Overview

After running the consolidation pipeline and copying the polished file to the server, use the scripts in this directory to import the data into ArcGIS Pro for dashboards and analysis.

## Workflow Order of Operations

```
1. Local Machine: Run consolidation
   python consolidate_cad_2019_2026.py

2. Local Machine: Copy to server
   powershell -ExecutionPolicy Bypass -File .\copy_consolidated_dataset_to_server.ps1

3. Remote Server (HPD2022LAWSOFT): Import to geodatabase
   python docs/arcgis/import_cad_polished_to_geodatabase.py

4. Remote Server: Refresh ArcGIS Pro project
   (Manual step in ArcGIS Pro)
```

## Files in This Directory

| File | Purpose | Run Location |
|------|---------|--------------|
| `import_cad_polished_to_geodatabase.py` | Import Excel to geodatabase using arcpy | Server (HPD2022LAWSOFT) |
| `README.md` | This documentation | N/A |

## Prerequisites

### For Server Copy (Step 2)
- Network connectivity to `10.0.0.157`
- Access to `\\10.0.0.157\esri` share
- PowerShell execution policy allows script execution

### For ArcGIS Import (Step 3)
- Remote Desktop access to HPD2022LAWSOFT
- ArcGIS Pro installed with valid license
- Python environment with arcpy available
- Write access to target geodatabase

## Detailed Instructions

### Step 1: Run Consolidation (Local Machine)

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
python consolidate_cad_2019_2026.py
```

This generates the ESRI polished Excel file and updates the manifest in `13_PROCESSED_DATA/`.

### Step 2: Copy to Server (Local Machine)

```powershell
# Test with dry run first
powershell -ExecutionPolicy Bypass -File .\copy_consolidated_dataset_to_server.ps1 -DryRun

# Execute actual copy
powershell -ExecutionPolicy Bypass -File .\copy_consolidated_dataset_to_server.ps1
```

**What the script does:**
1. Reads `13_PROCESSED_DATA/manifest.json` to find latest polished file
2. Verifies server connectivity and share access
3. Copies file to `\\10.0.0.157\esri\` with two filenames:
   - `CAD_Consolidated_2019_2026.xlsx` (friendly name)
   - Original timestamped filename
4. Verifies copy integrity (file size match)

### Step 3: Import to Geodatabase (Remote Server)

Connect to HPD2022LAWSOFT via Remote Desktop, then:

**Option A: Run ArcPy Script**
```powershell
# Open ArcGIS Pro Python Command Prompt
cd C:\ESRIExport\LawEnforcementDataManagement_New
python import_cad_polished_to_geodatabase.py
```

**Option B: Manual Import via ArcGIS Pro**
1. Open ArcGIS Pro
2. Open Catalog pane
3. Navigate to `C:\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx`
4. Right-click > Import > Table to Geodatabase
5. Select target geodatabase: `C:\HPD ESRI\03_Data\CAD\CAD_Data.gdb`
6. Set table name: `CAD_Consolidated_2019_2026`
7. Run import

### Step 4: Verify Import

After import, verify:
- Record count: **724,794** (or current count from manifest)
- Date range: **2019-01-01** to latest date
- Key fields present: ReportNumberNew, Incident, TimeOfCall, Disposition, Officer, PDZone

**Via ArcGIS Pro Python window:**
```python
import arcpy
table = r"C:\HPD ESRI\03_Data\CAD\CAD_Data.gdb\CAD_Consolidated_2019_2026"
count = arcpy.management.GetCount(table)
print(f"Record count: {count}")
```

## Configuration

The import script (`import_cad_polished_to_geodatabase.py`) uses the following default paths:

```python
CONFIG = {
    # Source Excel file
    "excel_source_share": r"\\10.0.0.157\esri\CAD_Consolidated_2019_2026.xlsx",
    "excel_source_local": r"C:\ESRIExport\LawEnforcementDataManagement_New\CAD_Consolidated_2019_2026.xlsx",

    # Target geodatabase
    "geodatabase": r"C:\HPD ESRI\03_Data\CAD\CAD_Data.gdb",

    # Output table name
    "table_name": "CAD_Consolidated_2019_2026",

    # Expected record count
    "expected_records": 724794,
}
```

Update these values in the script if your server paths differ.

## Troubleshooting

### Issue: Server Not Reachable

```
ERROR: Server HPD2022LAWSOFT (10.0.0.157) is NOT reachable
```

**Solution:**
- Verify VPN connection if working remotely
- Check network connectivity: `ping 10.0.0.157`
- Verify server is online

### Issue: ESRI Share Not Accessible

```
ERROR: ESRI share is NOT accessible: \\10.0.0.157\esri
```

**Solution:**
- Verify share permissions with IT
- Try accessing via Windows Explorer first
- Check credentials/authentication

### Issue: arcpy Not Available

```
ERROR: arcpy not available
```

**Solution:**
- This script must run on a machine with ArcGIS Pro
- Connect to HPD2022LAWSOFT via Remote Desktop
- Use ArcGIS Pro's Python environment

### Issue: Record Count Mismatch

```
WARN: Record count does not match expected
```

**Solution:**
- Verify source Excel file is complete
- Check manifest.json for current expected count
- Re-run consolidation if data is missing

## Related Documentation

- [REMOTE_SERVER_GUIDE.md](../../REMOTE_SERVER_GUIDE.md) - Comprehensive guide for server operations
- [manifest.json](../../../13_PROCESSED_DATA/manifest.json) - Latest file registry
- [Claude.md](../../CLAUDE.md) - Project context and rules

## Data Flow Diagram

```
Local Machine                          Server (HPD2022LAWSOFT)
=============                          ======================

CAD Source Files
(05_EXPORTS/_CAD/)
       |
       v
consolidate_cad_2019_2026.py
       |
       v
13_PROCESSED_DATA/
  manifest.json
  ESRI_Polished/base/*.xlsx
       |
       v
copy_consolidated_dataset_to_server.ps1  -->  \\10.0.0.157\esri\
                                                    |
                                                    v
                                       import_cad_polished_to_geodatabase.py
                                                    |
                                                    v
                                       CAD_Data.gdb/CAD_Consolidated_2019_2026
                                                    |
                                                    v
                                       ArcGIS Pro Dashboard
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-01 | Initial release with arcpy import script |

---

**Author:** R. A. Carucci
**Created:** 2026-02-01
**Last Updated:** 2026-02-01
