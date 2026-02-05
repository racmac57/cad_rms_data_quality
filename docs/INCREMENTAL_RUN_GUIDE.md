# Incremental CAD Consolidation + January Quality Reports – Run Guide

**Date:** 2026-02-02  
**Purpose:** Append new CAD data (2026_01 + 2026_02) without re-adding January records already in baseline; produce January quality reports; update manifest for server copy.

---

## 1. Incremental consolidation (baseline + new records only)

From repo root:

```powershell
cd "c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
python consolidate_cad_2019_2026.py
```

- **Behavior:** Loads baseline from `13_PROCESSED_DATA/ESRI_Polished/base/` (724,794 records through 2026-01-30). Loads only 2026 monthly files: `2026_01_CAD.xlsx`, `2026_02_CAD.xlsx`. January records already in baseline (by `ReportNumberNew`) are excluded; February records from 2026-02-01 onward are included. Combined dataset is written to **CAD_Data_Cleaning_Engine** as CSV: `data/01_raw/2019_to_2026_01_30_CAD.csv`.
- **Runtime:** Baseline load ~5 min; merge + export can take several more minutes.

---

## 2. Run CAD_Data_Cleaning_Engine (normalize, RMS backfill, ESRI polish)

From the cleaning engine repo:

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine"
python scripts/enhanced_esri_output_generator.py
```

- **Input:** CSV produced in step 1.  
- **Output:** Polished Excel in `data/03_final/` (e.g. `CAD_ESRI_POLISHED_*.xlsx`).  
- **RMS backfill:** If the pipeline uses RMS for PDZone/Grid, point it at:
  - `05_EXPORTS\_RMS\monthly\2026\2026_01_RMS.xlsx`
  - `05_EXPORTS\_RMS\monthly\2026\2026_02_RMS.xlsx`  
  (Paths are in `config/consolidation_sources.yaml` under `monthly_processing.rms.incremental_2026`.)

---

## 3. Copy polished file to 13_PROCESSED_DATA and update manifest

From cad_rms_data_quality repo root:

```powershell
cd "c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
python scripts/copy_polished_to_processed_and_update_manifest.py
```

- **Default:** Uses the **latest** `.xlsx` in `CAD_Data_Cleaning_Engine\data\03_final\`.
- **Custom source:**  
  `python scripts/copy_polished_to_processed_and_update_manifest.py --source "C:\path\to\CAD_ESRI_POLISHED_*.xlsx"`
- **Dry run:**  
  `python scripts/copy_polished_to_processed_and_update_manifest.py --dry-run`

Result:

- Polished file is copied to  
  `13_PROCESSED_DATA\ESRI_Polished\incremental\YYYY_MM_DD_append\`.
- `13_PROCESSED_DATA\manifest.json` is updated so `latest` points to this file.
- `copy_consolidated_dataset_to_server.ps1` and the ArcGIS workflow then use the new file.

---

## 4. January quality reports (already run 2026-02-02)

Reports were generated for **January exports only**:

| Export            | Report folder                              | Contents |
|-------------------|--------------------------------------------|----------|
| 2026_01_CAD.xlsx  | `monthly_validation/reports/2026_02_02_jan_cad/` | validation_summary.html, action_items.xlsx, metrics.json |
| 2026_01_RMS.xlsx  | `monthly_validation/reports/2026_02_02_jan_rms/` | validation_summary.html, action_items.xlsx, metrics.json |

To re-run or run for another month:

```powershell
# CAD January
python monthly_validation/scripts/validate_cad.py --input "C:\...\05_EXPORTS\_CAD\monthly\2026\2026_01_CAD.xlsx" --output "monthly_validation/reports/2026_02_02_jan_cad"

# RMS January
python monthly_validation/scripts/validate_rms.py --input "C:\...\05_EXPORTS\_RMS\monthly\2026\2026_01_RMS.xlsx" --output "monthly_validation/reports/2026_02_02_jan_rms"
```

---

## 5. Config and code changes (summary)

- **config/consolidation_sources.yaml**
  - `sources.monthly`: 2026_01_CAD.xlsx and 2026_02_CAD.xlsx (paths as in repo).
  - `monthly_processing.rms.incremental_2026`: 2026_01_RMS.xlsx and 2026_02_RMS.xlsx for backfill.
- **consolidate_cad_2019_2026.py**
  - Incremental mode uses only 2026 monthly files from config.
  - January: exclude records whose `ReportNumberNew` is already in baseline.
  - February: include records with `TimeOfCall` ≥ 2026-02-01.
- **scripts/copy_polished_to_processed_and_update_manifest.py**
  - New script: copy latest polished Excel to 13_PROCESSED_DATA and update `manifest.json`.

---

## Deliverables checklist

- [x] Incremental logic: baseline + new/deduplicated monthly data only (no duplicate January rows).
- [x] Config: 2026_01/02 CAD and RMS paths; incremental uses 2026 monthly only.
- [x] Copy + manifest script for 13_PROCESSED_DATA and ArcGIS/server workflow.
- [x] January quality reports: 2026_01_CAD and 2026_01_RMS in `monthly_validation/reports/` (2026_02_02_jan_cad, 2026_02_02_jan_rms).
- [ ] **You run:** Consolidation to completion → Cleaning engine → `copy_polished_to_processed_and_update_manifest.py` so the new polished dataset and manifest are in place.
