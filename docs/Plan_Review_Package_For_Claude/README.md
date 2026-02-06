# Plan Review Package for Claude

This folder contains copies of all files needed for Claude to review and enhance the **CAD RMS Data Quality Expansion** plan, with a focus on **speed**, **efficiency of processing**, and **organization**.

---

## How to use this package

1. **Open this folder in Cursor/Claude** (or attach it to a chat).
2. **Give Claude the prompt** in `PROMPT_FOR_CLAUDE.md` (copy its contents into your message, or reference the file).
3. Claude will use the **plan** (`CAD_RMS_Data_Quality_Expansion_Plan.md`) and the **context files** listed below to suggest enhancements.

---

## File index

Each file below is a **copy** from the project. The **Full path (original)** is where it lives in the repo; the **copy** in this package has the same base name for easy reference.

| File in this folder | Brief summary | Why added | Full path (original) |
|---------------------|---------------|-----------|----------------------|
| **PROMPT_FOR_CLAUDE.md** | Prompt to give Claude to review and enhance the plan for speed, efficiency, and organization. | Primary instruction for the review task. | N/A (created for this package) |
| **CAD_RMS_Data_Quality_Expansion_Plan.md** | Full expansion plan: baseline dataset, 13_PROCESSED_DATA/ESRI_Polished, consolidation reports, monthly CAD/RMS, legacy archive, server copy + arcpy. | The artifact to review and improve. | `c:\Users\carucci_r\.cursor\plans\cad_rms_data_quality_expansion_df9c76f5.plan.md` |
| **CHANGELOG.md** | Version history and release notes (v1.1.1, 724,794 records, backfill, etc.). | Context on current state and what’s already implemented. | `c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\CHANGELOG.md` |
| **Claude.md** | AI context and rules: project purpose, directory roles, conventions, authoritative sources, validation rules. | Ensures enhancements align with project structure and standards. | `c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\Claude.md` |
| **PLAN.md** | Implementation plan and architecture (phases, new project structure, authoritative sources). | High-level roadmap and design decisions. | `c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\PLAN.md` |
| **README_project.md** | Project overview, structure, data sources, entry points (copy of project README). | Quick reference for layout and usage. | `c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\README.md` |
| **SUMMARY.md** | Short project summary, key metrics, next steps. | Current status and metrics (e.g. 724,794 records, 559,202 unique cases). | `c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\SUMMARY.md` |
| **consolidation_sources.yaml** | CAD source paths (yearly/monthly), expected counts. | Plan references new paths and baseline; config shows current paths. | `c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\config\consolidation_sources.yaml` |
| **rms_sources.yaml** | RMS base/monthly dirs, source files, output and validation config. | Plan adds monthly CAD/RMS; this defines current RMS layout. | `c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\config\rms_sources.yaml` |
| **consolidate_cad_2019_2026.py** | Production consolidation script: loads yearly + monthly CAD, filters date range, writes CSV and summary. | Plan changes output paths and adds baseline/incremental; this is the script to modify. | `c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\consolidate_cad_2019_2026.py` |
| **backfill_january_incremental.py** | Incremental backfill: merges new records (e.g. Jan 17–30) with existing ESRI polished file, RMS backfill, normalization. | Plan’s “baseline + incremental” and speed ideas apply here. | `c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\backfill_january_incremental.py` |
| **copy_consolidated_dataset_to_server.ps1** | Copies a fixed polished file path to `\\10.0.0.157\esri\`. | Plan updates this to use “latest” from 13_PROCESSED_DATA/ESRI_Polished. | `c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\copy_consolidated_dataset_to_server.ps1` |

---

## Package location

**This folder (full path):**  
`c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\Plan_Review_Package_For_Claude\`

**Parent project:**  
`c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\`

---

## After Claude’s review

- Apply suggested changes to the **actual plan** (e.g. in `.cursor/plans/` or wherever you keep it) and to the **live** config/scripts in the project.
- This package is for review only; the copies here are not the source of truth.
