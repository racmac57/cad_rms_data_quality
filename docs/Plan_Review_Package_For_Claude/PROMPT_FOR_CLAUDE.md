# Prompt for Claude Code: Review and Enhance the Plan

Use this prompt with **Claude Code** (agent mode). Give Claude Code access to the repo so it can read the paths below. You can @-mention the review package folder or paste this prompt into a new chat.

---

## File and directory locations (read these first)

**Plan to review and enhance (primary input):**  
`c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\Plan_Review_Package_For_Claude\CAD_RMS_Data_Quality_Expansion_Plan.md`

**Review package directory (all context files for the plan):**  
`c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\Plan_Review_Package_For_Claude\`

**Files in that directory to read for context:**
- `README.md` — index of files and why each is included
- `CHANGELOG.md` — version history and current state (e.g. 724,794 records, v1.1.1)
- `Claude.md` — project rules, directory roles, conventions
- `PLAN.md` — implementation roadmap and architecture
- `README_project.md` — project overview and structure
- `SUMMARY.md` — metrics and next steps
- `consolidation_sources.yaml` — CAD source paths and config
- `rms_sources.yaml` — RMS paths, output, validation config
- `consolidate_cad_2019_2026.py` — main consolidation script (loads yearly + monthly, writes CSV and summary)
- `backfill_january_incremental.py` — incremental backfill (merge new records with existing ESRI polished)
- `copy_consolidated_dataset_to_server.ps1` — copies polished file to server share

**Live project root (for reference; scripts and config live here):**  
`c:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\`

---

## Your task (Claude Code)

You are an expert in data pipelines, ETL design, and Python/pandas performance. Your job is to **review the expansion plan** at the path above and **produce an enhanced version** of that plan with concrete recommendations for **speed**, **efficiency of processing**, and **organization**.

**Steps:**

1. **Read the plan.** Open and read:  
   `docs/Plan_Review_Package_For_Claude/CAD_RMS_Data_Quality_Expansion_Plan.md`  
   (from the repo root, or use the full path to the file above.)

2. **Read the context files.** From the **review package directory** (`docs/Plan_Review_Package_For_Claude/`), read the files listed above (README.md, CHANGELOG.md, Claude.md, PLAN.md, README_project.md, SUMMARY.md, consolidation_sources.yaml, rms_sources.yaml, consolidate_cad_2019_2026.py, backfill_january_incremental.py, copy_consolidated_dataset_to_server.ps1). Use them to understand current behavior, paths, and conventions.

3. **Enhance the plan for speed and efficiency:**
   - Where can consolidation or ESRI generation use **more cores**, **chunking**, or **parallel I/O** (e.g. loading multiple Excel files in parallel, chunked reads for large workbooks)? Name specific scripts and config (e.g. `consolidate_cad_2019_2026.py`, `enhanced_esri_output_generator.py` in CAD_Data_Cleaning_Engine).
   - How should **baseline + incremental** mode be designed so append-only runs avoid re-reading 7 years of data? Be specific: config keys, script flow, where to load baseline vs new monthly data.
   - Call out any **pandas/numpy** or **disk I/O** optimizations (dtype, chunk size, intermediate files) that belong in the plan.
   - Should **monthly validation** use the same parallel/chunking patterns as consolidation? If yes, say where in the plan to add that.

4. **Enhance the plan for organization:**
   - Is the proposed layout for `13_PROCESSED_DATA\ESRI_Polished` (base + YYYY_MM_DD_ appended) clear for auditing and “latest file” resolution? Suggest refinements (naming, subfolders, manifest) and add them to the plan.
   - Is the split between `consolidation/reports/YYYY_MM_DD_*` and `monthly_validation/reports/YYYY_MM_DD_*` right, or should there be a single reports root with subfolders? Update the plan accordingly.
   - Suggest config/path conventions (e.g. single `paths.yaml` or new sections in existing YAML) that reduce duplication and make implementation clearer; add them to the plan.

5. **Output an enhanced plan.** Write an **enhanced version** of `CAD_RMS_Data_Quality_Expansion_Plan.md` that incorporates your recommendations. Keep the same structure (sections 1–6, implementation order, diagram). Add subsections or bullets for speed, efficiency, and organization. Be specific enough to implement without guessing (e.g. “add config key X under Y”, “in script Z add step W”).  
   - **Save the enhanced plan** in the same folder as:  
     `docs/Plan_Review_Package_For_Claude/CAD_RMS_Data_Quality_Expansion_Plan_ENHANCED.md`  
   - Optionally, add a short **ENHANCEMENT_SUMMARY.md** in that folder listing the main changes (speed, efficiency, organization) so the user can review quickly.

**Constraints:** Do not change the overall scope (baseline, 13_PROCESSED_DATA, reports, monthly processing, legacy archive, server + arcpy). Only refine and add detail for speed, efficiency of processing, and organization.

**Optional next step:** After you save the enhanced plan, the user may ask you to **implement** parts of it (e.g. add config keys, update scripts, create directories). If so, use the enhanced plan and the live project root above as the source of truth.
