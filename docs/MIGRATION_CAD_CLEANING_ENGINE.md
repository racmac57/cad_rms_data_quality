# CAD cleaning logic — selective migration (living checklist)

**Purpose:** Consolidate *specific* Sandbox assets into `cad_rms_data_quality` without big-bang copying `_Sandbox\CAD_Data_Cleaning_Engine`. This doc is the backlog + definition of done; update checkboxes as work lands.

**Discovery context (2026-04):** Three locations, one logical pipeline:

| Location | Role | Notes |
|----------|------|--------|
| **This repo** (`cad_rms_data_quality`) | Validation + QA + consolidation entry | Canonical for monthly validation and production reports. Lean; tests minimal. |
| **`C:\_Sandbox\02_ETL_Scripts\CAD_Data_Cleaning_Engine`** | Full cleaning / normalization / ESRI-adjacent ops | Large (100+ `.py`, many JSON). Spec source + perf ideas, not a wholesale merge target. |
| **OneDrive `...\02_ETL_Scripts\CAD_Data_Cleaning_Engine`** | Thin mirror | Treat as **deprecated stub** (e.g. single large script + raw CSV)—not a migration source. |

**Key relationship:** `cad_rms_data_quality` is **not** a replacement cleaning engine; it validates and consolidates. Consolidation output has been **coupled** to Sandbox-style paths—decouple via config (see backlog).

---

## Real duplication / merge points (fix deliberately)

1. **Disposition / HowReported:** subset mappings in `validation/validators/disposition_validator.py` and `how_reported_validator.py` vs fuller mappings in Sandbox (e.g. ESRI deploy story). **Winner:** canonical JSON under `Standards/CAD_RMS/mappings/*.json`, loaded via `schemas_loader` / shared loaders—aligned with `CLAUDE.md` (no long-lived hardcoded dicts).
2. **Consolidation output path:** `consolidate_cad_2019_2026.py` (and related backfills) writing into `...\CAD_Data_Cleaning_Engine\data\01_raw\`. **Winner:** `config/consolidation_sources.yaml` → `processed_data` / consolidated paths.
3. **Standards root:** `shared/utils/schemas_loader.py` must remain consistent with `path_config` / env (`STANDARDS_ROOT`), not one-off user literals.
4. **Quality score weights:** `config/validation_rules.yaml` is the production contract; Sandbox `config.yml` weights are **not** authoritative.

**Do not import across repos.** `enhanced_esri_output_generator.py` stays in Sandbox; this repo consumes **Standards JSON + contracts** only.

---

## Phase B — Ordered backlog (one PR / merge per row)

Use this as the shipping order (smallest risk first).

- [ ] **1. Epic anchored** — This file + pointer in `CLAUDE.md` Quick Commands (done when merged).
- [x] **2. Disposition normalization** — Extract full mapping from Sandbox sources into `09_Reference/Standards/CAD_RMS/mappings/disposition_normalization_map.json` (path must match `config/schemas.yaml`). Add `shared/utils/normalization.py` loader; refactor `disposition_validator.py` to use it. Unit test on a golden subset.
- [ ] **3. HowReported normalization** — Same pattern as (2) for `how_reported_normalization_map.json` and `how_reported_validator.py`.
- [ ] **4. Golden-sample lock** — One ~10k-row CAD export fixture under `tests/fixtures/`; snapshot `validate_cad` metrics; `tests/test_validate_cad_golden.py` asserts drift ≤ agreed tolerance vs baseline. **Do before large validator refactors.**
- [ ] **5. Schema pre-flight** — Port generic `SchemaValidator` from Sandbox `utils/validate_schema.py` to `shared/utils/schema_validator.py` (strict/warn); wire optional pre-flight in `validate_cad.py`.
- [ ] **6. Decouple consolidation paths** — Remove hardcoded `...\CAD_Data_Cleaning_Engine\...` writes; drive from `consolidation_sources.yaml` (`processed_data.consolidated_csv` or equivalent).
- [ ] **7. Vectorized validators (optional)** — Port patterns from `validate_cad_export_parallel.py` **only if** profiling shows monthly validation > ~2 minutes on a typical export; implement as e.g. `.validate_vectorized(df)` on existing classes.
- [ ] **8. Gap evaluation** — CADNotes/mojibake (`01_validate_and_clean.py`), duplicate detection beyond date filter—port **only** if quality reports show material defects.
- [ ] **9. Sandbox policy** — Separate decision: archive one-offs, tag release for ESRI scripts, retire OneDrive stub.

---

## Out of scope (remain Sandbox or ops repo)

- ArcPy geocoding / locator paths tied to GIS machines  
- ESRI rebuild / deploy scripts, Dask `01_validate_and_clean.py`  
- Majority of one-off Sandbox `scripts/`

---

## Definition of done (migration “complete” for this epic)

- [ ] `python -m monthly_validation.scripts.validate_cad` on the golden sample matches pre-migration metrics within **±0.5%** (or documented tolerance).
- [ ] Disposition + HowReported domains in validators are **1:1** with the JSON in Standards (verified by diff / tests).
- [ ] No long-lived `get_*_mapping()` hardcoded dicts in `validation/validators/`—load via shared loader + `schemas.yaml`.
- [ ] `pytest tests/` green with at least: golden-sample test, one loader test per normalization map, `SchemaValidator` test (once ported).
- [ ] `consolidate_cad_2019_2026.py` does not hardcode Sandbox engine data paths.
- [ ] This checklist updated; epic row in `CLAUDE.md` (if added) shows complete.

---

## Suggested verification commands (non-destructive)

```bash
# Baseline monthly validation
python -m monthly_validation.scripts.validate_cad

# Consolidation (use project conventions; --full per CLAUDE.md)
python consolidate_cad_2019_2026.py --full

# Inventory path coupling before refactors
# Ripgrep: CAD_Data_Cleaning_Engine
```

---

## Related downstream

- **Acute_Crime T4** (`10_Projects/Acute_Crime`): disposition-based Tier 1 weighting remains **policy TBD**; this migration supplies **consistent domain normalization** for validators and future scoring.

---

## Status notes

**2026-04-16 — item #2 done.** Discovery showed `09_Reference/Standards/CAD_RMS/mappings/disposition_normalization_map.json` already existed (55 entries, `_metadata.canonical_targets` of 20) and the canonical generator (OneDrive `enhanced_esri_output_generator.py`, April 2026) already loaded from it. The Sandbox `_Sandbox\…\esri_production_deploy.py` mapping at line 369 is **stale/diverged** (e.g. `"CANCELED": "Cancelled"`, targets like `"Report Taken"` / `"Citation"` not in canonical_targets) and was **not** merged. Standards JSON is the winner.

Changes landed in this repo:
- `config/schemas.yaml` — added `mappings.disposition_normalization` and `mappings.how_reported_normalization` (item #3 unblocked).
- `shared/utils/normalization.py` — new module with `load_disposition_map()`, `load_disposition_canonical_targets()` plus the same pair for how_reported.
- `validation/validators/disposition_validator.py` — `get_disposition_mapping()` now passes through to the JSON; `VALID_DISPOSITIONS` is built from `canonical_targets ∪ legacy safety set`; reference string updated to point at the Standards JSON.
- `tests/conftest.py` + `tests/test_disposition_normalization.py` — first pytest in the repo (12 tests, golden raw→canonical pairs, validator passthrough). All pass.

Follow-ups uncovered (deferred):
- `backfill_january_incremental.py:133` still has its own hardcoded `disposition_map` dict. Out of scope here (one-off backfill); fold into item #6 when consolidation paths are decoupled.
- Item #3 (HowReported) is now a near-trivial mirror of item #2 since `load_how_reported_map()` is already in place — pick it up next.
- Repo-wide ruff/mypy cleanup is a separate, larger epic (baseline shows 70+ ruff errors and 20+ mypy errors in untouched files).
