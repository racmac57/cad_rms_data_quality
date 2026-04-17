# CLAUDE.md

Project context and rules for any Claude instance working in this repository.

## Project Overview

**CAD/RMS Data Quality System** for the City of Hackensack Police Department.
Consolidates, validates, and publishes CAD (Computer-Aided Dispatch) and RMS
(Records Management System) data to ArcGIS Online dashboards.

Three components:
1. **Historical Consolidation** — Merge 2019-2026 CAD data into a single validated dataset (~750K+ records)
2. **Monthly Validation** — Reusable validation scripts for ongoing CAD/RMS exports with quality scoring
3. **Historical Backfill** — Load consolidated data to ArcGIS Online feature service (571K+ records live)

**Current version:** 1.7.0 | **Python:** >=3.9 | **License:** Internal Use

---

## Rules for AI Agents

### Path Rules (CRITICAL)
- **DO NOT** change `carucci_r` to `RobertCarucci` in scripts or configs
- `scripts.json` uses `carucci_r` paths — this is correct and intentional
- `path_config.py` resolves the correct root at runtime via `get_onedrive_root()`
- If a path appears broken, check junction status before editing any file
- Do not rename `PowerBI_Data` back to any old misspelled folder name; the canonical folder is `PowerBI_Data`

Path junctions (created 2026-03-22):
```
C:\Users\carucci_r  -->  C:\Users\RobertCarucci
C:\Users\RobertCarucci\OneDrive  -->  C:\Users\RobertCarucci\OneDrive - City of Hackensack
```
Active root: `C:\Users\carucci_r\OneDrive - City of Hackensack`

### Coding Conventions
- Line length: 100 (configured in ruff)
- Target Python: 3.9+
- Use `pathlib.Path` for all file paths
- Use `logging` module, not `print()`, for status output in scripts
- Config lives in `config/*.yaml` — do not hardcode paths or thresholds in scripts
- All normalization mappings load from `Standards/CAD_RMS/mappings/*.json` at runtime (not hardcoded dicts)
- Schemas resolve `${standards_root}` via `shared/utils/schemas_loader.py`
- Always use `--full` mode for consolidation (incremental mode is deprecated — caused data loss)

### ArcPy / ESRI Conventions
- Use `XYTableToPoint` with existing lat/lon fields — do NOT live-geocode at scale
- Use field copying (`AddField` + `CalculateField`) instead of `FieldMappings` API (it silently fails)
- Two-stage append: temp FC -> local geodatabase -> ArcGIS Online (never direct)
- Spatial reference: WGS84 (EPSG:4326)
- ArcPy Python: `C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat`

---

## Quick Commands

```bash
# Install dependencies
pip install -e ".[dev]"
# or
pip install -r requirements.txt

# Lint
ruff check .

# Type check
mypy shared/ consolidation/ monthly_validation/ validation/

# Run consolidation (entry point)
python consolidate_cad_2019_2026.py --full

# Run all validations
python validation/run_all_validations.py --input data.xlsx --output reports/

# Validate a monthly CAD export
python -m monthly_validation.scripts.validate_cad

# Validate a monthly RMS export
python -m monthly_validation.scripts.validate_rms
```

**CAD / Sandbox migration (selective):** See `docs/MIGRATION_CAD_CLEANING_ENGINE.md` for the phased backlog (Standards JSON mappings, consolidation path decoupling, golden tests). Do not big-bang port `_Sandbox\CAD_Data_Cleaning_Engine`.

Note: No test suite exists yet. The `pyproject.toml` configures pytest (`testpaths = ["tests"]`)
but the `tests/` directory has not been created.

---

## Custom Skills (Slash Commands)

Project-level skills in `.claude/skills/`. Invoke with `/<name>` in Claude Code.

| Skill | Usage | Purpose |
|-------|-------|---------|
| `/handoff` | `/handoff Crime-Data-Scheduler` | Generate a structured AI handoff document for the next session |
| `/pipeline-status` | `/pipeline-status all` | Generate PowerShell to check nightly Task Scheduler results on the RDP server |
| `/validate-monthly` | `/validate-monthly cad 2026-03` | Run monthly CAD or RMS validation and summarize quality score |
| `/check-paths` | `/check-paths` | Lint configs and scripts for path convention violations (carucci_r, junctions) |
| `/consolidation-run` | `/consolidation-run --dry-run` | Execute full consolidation and verify record counts against thresholds |
| `/deploy-script` | `/deploy-script scripts/monitor.py --schedule 02:00` | Generate PowerShell to deploy a script to the RDP server and optionally schedule it |

---

## Skill Documentation

How-to guides for all skills in this project live in:
`C:\Users\carucci_r\OneDrive - City of Hackensack\00_dev\ai_enhancement\docs\skills\`

- `cad_rms_data_quality_skills.md` — project skills (10 skills)
- `SKILLS_INDEX.md` — full index of all global and project skills

---

## Directory Structure

```
cad_rms_data_quality/
|-- config/                          # YAML configs (sources, schemas, validation rules)
|   |-- consolidation_sources.yaml   #   CAD source paths, baseline config, performance tuning
|   |-- schemas.yaml                 #   Paths to Standards JSON schemas (uses ${standards_root})
|   |-- validation_rules.yaml        #   Field rules, quality scoring, anomaly thresholds
|   +-- rms_sources.yaml             #   RMS source paths
|
|-- shared/                          # Shared library code
|   |-- utils/
|   |   |-- schemas_loader.py        #   Load schemas.yaml with variable expansion
|   |   |-- version_check.py         #   Warn if schemas.yaml diverges from Standards/VERSION
|   |   |-- report_builder.py        #   HTML/Excel report generation
|   |   +-- call_type_normalizer.py  #   Normalize incident types to ESRI categories
|   |-- validators/                  #   Base validator classes
|   +-- processors/                  #   Data processing utilities
|
|-- validation/                      # Comprehensive validation framework
|   |-- run_all_validations.py       #   Master orchestrator (9 validators + 2 drift detectors)
|   |-- validators/                  #   Individual field validators
|   |   |-- how_reported_validator.py
|   |   |-- disposition_validator.py
|   |   |-- case_number_validator.py
|   |   |-- datetime_validator.py
|   |   |-- geography_validator.py
|   |   +-- ... (9 total)
|   +-- sync/                        #   Drift detection (call type, personnel)
|
|-- monthly_validation/              # Monthly export validation
|   +-- scripts/
|       |-- validate_cad.py          #   Monthly CAD validation entry point
|       +-- validate_rms.py          #   Monthly RMS validation entry point
|
|-- consolidation/                   # Consolidation outputs and reports
|   |-- output/                      #   Generated CSV files
|   +-- reports/                     #   Run reports and metrics JSON
|
|-- scripts/                         # Operational scripts (run on RDP server)
|   |-- complete_backfill_simplified.py  # v1.6.0 production backfill script
|   |-- backup_current_layer.py      #   Export online layer to local FGDB
|   |-- truncate_online_layer.py     #   Delete all records (triple confirmation)
|   |-- restore_from_backup.py       #   Emergency rollback
|   |-- cad_fulladdress2_qc.py       #   Address quality analysis
|   +-- monitor_dashboard_health.py  #   Post-publish health monitoring
|
|-- consolidate_cad_2019_2026.py     # Main consolidation script (root-level entry point)
|-- scheduled_publish_call_data.py   # Scheduled publishing to ArcGIS Online
|-- pyproject.toml                   # Project metadata, ruff, mypy, pytest config
|-- requirements.txt                 # Pip dependencies
+-- docs/                            # Extended documentation and session logs
```

---

## Key Configuration

### consolidation_sources.yaml
- **sources.yearly** — Paths to yearly CAD Excel files (2012-2025)
- **sources.monthly** — Paths to monthly CAD Excel files (2026+)
- **baseline** — Generic pointer path and versioned archive path; always use `--full` mode
- **performance** — Parallel loading (8 workers), chunked reading (100K rows), memory optimization
- **processed_data** — Output directories for ESRI-polished files and manifests

### validation_rules.yaml
- **case_number.pattern** — `^\d{2}-\d{6}([A-Z])?$` (e.g., `25-000001`, `25-000001A`)
- **required_fields.cad** — `ReportNumberNew`, `Incident`, `TimeOfCall`, `FullAddress2`, `PDZone`, `Disposition`, `HowReported`
- **required_fields.rms** — `CaseNumber`, `IncidentDate`, `IncidentTime`, `FullAddress`, `Zone`
- **quality_scoring** — Weighted 0-100 scale (required_fields: 30%, formats: 25%, address: 20%, domain: 15%, consistency: 10%)
- **response_time_exclusions** — Self-Initiated calls and admin categories excluded from response time calculations

### schemas.yaml
- Resolves `${standards_root}` to the Standards directory (env var `STANDARDS_ROOT` overrides)
- Points to canonical, CAD, RMS, and transformation JSON schemas
- Points to normalization mapping JSONs (`how_reported_normalization_map.json`, `disposition_normalization_map.json`)

---

## Data Model

### CAD Source Fields (FileMaker Excel exports)
| Field | Type | Description |
|-------|------|-------------|
| `ReportNumberNew` | TEXT | Primary key (`YY-NNNNNN` or `YY-NNNNNNA`) |
| `Incident` | TEXT | Call type |
| `How_Reported` | TEXT | Call source (Phone, 9-1-1, Radio, etc.) |
| `FullAddress2` | TEXT | Full address (may have leading `,` or `&`) |
| `Time_Of_Call` | TEXT | Datetime `YYYY-MM-DD HH:MM:SS` |
| `Time_Dispatched` | TEXT | Datetime |
| `Time_Out` | TEXT | Datetime |
| `Time_In` | TEXT | Datetime |
| `latitude` | TEXT/DOUBLE | Y coordinate (e.g., `40.8856`) |
| `longitude` | TEXT/DOUBLE | X coordinate (e.g., `-74.0435`) |

### Target Online Service Fields (after transformation)
| Source | Target | Transformation |
|--------|--------|----------------|
| `ReportNumberNew` | `callid` | Field copy |
| `Incident` | `calltype` | Field copy |
| `How_Reported` | `callsource` | Field copy |
| `FullAddress2` | `fulladdr` | Address cleaning (strip leading `,`/`&`) |
| `Time_Of_Call` | `calldate` | Text -> DATE conversion |
| `Time_Dispatched` | `dispatchdate` | Text -> DATE conversion |
| `Time_Out` | `enroutedate` | Text -> DATE conversion |
| `Time_In` | `cleardate` | Text -> DATE conversion |
| (derived) | `dispatchtime` | Minutes: `dispatchdate - calldate` |
| (derived) | `queuetime` | Minutes: `enroutedate - dispatchdate` |
| (derived) | `cleartime` | Minutes: `cleardate - enroutedate` |
| (derived) | `responsetime` | `dispatchtime + queuetime` |
| (derived) | `calldow`, `calldownum`, `callhour`, `callmonth`, `callyear` | Date attribute extraction |

---

## Server Environment

**Server:** HPD2022LAWSOFT (Remote Desktop)
- ArcGIS Pro 3.6.1 installed
- Scripts deployed to `C:\HPD ESRI\04_Scripts\`
- Local geodatabase: `C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb\CFStable`
- Staging: `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx`

**ArcGIS Online Feature Service:**
- Service URL: `https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0`
- Dashboard: `https://hpd0223.maps.arcgis.com/apps/dashboards/d9315ff773484ca999ae3e16758cbec1`
- Current records: 571,282 (as of v1.6.1)

---

## Architecture Decisions (lessons learned)

| Decision | Rationale |
|----------|-----------|
| **Field copying over FieldMappings API** | `arcpy.FieldMappings` silently produces NULL attributes; `AddField` + `CalculateField` is explicit and verifiable |
| **XYTableToPoint over live geocoding** | CAD exports already contain lat/lon; Esri geocoding service hangs at 564K+ features |
| **Two-stage append** | Local verification before pushing to online service; enables rollback |
| **Full-mode consolidation only** | Incremental mode caused data loss because the baseline is already deduplicated |
| **JSON mapping files at runtime** | Normalization maps (`how_reported`, `disposition`) loaded from Standards repo, not hardcoded |
| **${standards_root} variable expansion** | `schemas_loader.py` resolves paths so config stays portable across machines |

---

## Version History

| Version | Date | Milestone |
|---------|------|-----------|
| 1.7.0 | 2026-04-10 | Standards audit complete; `schemas_loader` + `version_check` added; `data/` archived |
| 1.6.1 | 2026-02-16 | Gap backfill date fix (2,680 records corrected) |
| 1.6.0 | 2026-02-09 | Historical backfill SUCCESS (565,470 records in 13.8 min) |
| 1.5.0 | 2026-02-06 | Staged planning and validation framework |
| 1.4.0 | 2026-02-04 | Validation pipeline established |
