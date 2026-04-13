---
name: cad-export-fix
description: Convert a raw FileMaker CAD export to the exact schema the ArcGIS TransformCallData model requires. Detects schema mismatches, renames columns, adds missing lat/lon, reorders, and writes a _FIXED.xlsx ready to stage.
disable-model-invocation: true
argument-hint: [path-to-xlsx]
allowed-tools: Read Bash(python *) Write
---

# CAD Export Fix -- Normalize FileMaker Export to Model Schema

Fix a raw FileMaker CAD export so it matches the live `ESRI_CADExport.xlsx` schema
consumed by the ArcGIS `TransformCallData` model.

## Trigger

`/cad-export-fix $ARGUMENTS` or "fix this CAD export".

- `$0` -- absolute path to the raw `.xlsx` CAD export (required)

Example:
```
/cad-export-fix C:\Users\carucci_r\OneDrive - City of Hackensack\Desktop\2026_04_CAD.xlsx
```

## Required Output Schema (21 columns, in order)

```
ReportNumberNew, Incident, How Reported, FullAddress2, PDZone, Grid,
Time of Call, cYear, cMonth, Hour_Calc, DayofWeek, Time Dispatched,
Time Out, Time In, Time Spent, Time Response, Officer, Disposition,
latitude, longitude, Response Type
```

## Known Column Name Mappings

FileMaker manual exports use underscore-variants and one typo. The model reads the
space-variants. `latitude`/`longitude` must exist but may be null — the ArcGIS model
geocodes addresses using the NJ State Plane Composite locator.

| FileMaker Manual Export | Model Expected | Notes |
|---|---|---|
| `HourMinuetsCalc` | `Hour_Calc` | Typo in FileMaker layout name |
| `How_Reported` | `How Reported` | Underscore -> space |
| `Time_Of_Call` | `Time of Call` | Underscore -> space |
| `Time_Dispatched` | `Time Dispatched` | Underscore -> space |
| `Time_Out` | `Time Out` | Underscore -> space |
| `Time_In` | `Time In` | Underscore -> space |

Columns not in the live schema (e.g. `CADNotes`) should be dropped with a warning.

## Execution

Generate and run an inline Python script (project venv has pandas + openpyxl):

```python
import sys
from pathlib import Path
import pandas as pd

SRC = Path(r"$0")  # <- substitute the user-provided xlsx path here
OUT = SRC.with_name(SRC.stem + "_FIXED.xlsx")

RENAMES = {
    "HourMinuetsCalc": "Hour_Calc",
    "How_Reported": "How Reported",
    "Time_Of_Call": "Time of Call",
    "Time_Dispatched": "Time Dispatched",
    "Time_Out": "Time Out",
    "Time_In": "Time In",
}

TARGET_COLS = [
    "ReportNumberNew", "Incident", "How Reported", "FullAddress2", "PDZone", "Grid",
    "Time of Call", "cYear", "cMonth", "Hour_Calc", "DayofWeek", "Time Dispatched",
    "Time Out", "Time In", "Time Spent", "Time Response", "Officer", "Disposition",
    "latitude", "longitude", "Response Type",
]

df = pd.read_excel(SRC, dtype={"ReportNumberNew": str})
before = list(df.columns)

df = df.rename(columns=RENAMES)

for col in ("latitude", "longitude"):
    if col not in df.columns:
        df[col] = None

missing = [c for c in TARGET_COLS if c not in df.columns]
extras = [c for c in df.columns if c not in TARGET_COLS]

if missing:
    print(f"ERROR: missing required columns: {missing}")
    sys.exit(1)

if extras:
    print(f"WARNING: dropping extra columns not in live schema: {extras}")

df = df[TARGET_COLS]
df.to_excel(OUT, index=False)

print(f"Rows: {len(df):,}")
print(f"Before columns: {before}")
print(f"After columns:  {list(df.columns)}")
print(f"Wrote: {OUT}")
```

## Steps

1. Confirm the input file exists (Read or Bash `ls`).
2. Substitute the user-supplied path into the script and run it via Bash
   (`python -c '<script>'` or write a temp .py file).
3. Validate the output file has all 21 columns in the correct order.
4. Report:
   - Row count
   - Before/after column diff
   - Any extras dropped or columns renamed
   - Output path (`<input>_FIXED.xlsx`)
   - If a `Time of Call` column is present, note the min/max dates so the user can
     sanity-check the gap/date range.

## Notes

- Always force `ReportNumberNew` to string dtype on load (Excel strips leading zeros
  from `YY-NNNNNN` case numbers).
- Do not overwrite the original file. Always write `_FIXED.xlsx` alongside it.
- The live staging path on the RDP server is
  `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx` — the fixed file
  is typically copied there by the `esri-backfill` skill.
