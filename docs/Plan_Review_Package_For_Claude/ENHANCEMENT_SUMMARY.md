# Enhancement Summary: CAD/RMS Data Quality Expansion Plan

**Date:** 2026-02-01
**Reviewer:** Claude Code (Opus 4.5)
**Enhanced Plan:** `CAD_RMS_Data_Quality_Expansion_Plan_ENHANCED.md`

---

## Quick Reference: Main Changes

### 1. Speed Improvements

| Enhancement | What to Add | Where | Expected Impact |
|-------------|-------------|-------|-----------------|
| **Parallel file loading** | `ThreadPoolExecutor` with `MAX_WORKERS=8` | `consolidate_cad_2019_2026.py` | 3-4x faster Excel loading |
| **Chunked reading** | `load_excel_chunked()` using openpyxl read_only mode | `consolidate_cad_2019_2026.py` | Handle 100MB+ files without memory issues |
| **Baseline + incremental** | New script `consolidate_cad_incremental.py` | New file | Skip re-reading 7 years (~700K records) |
| **Dtype optimization** | `optimize_dtypes()` function | `shared/utils/memory_optimizer.py` | 40-60% memory reduction |
| **Configurable ESRI workers** | `n_workers: 4` under `performance.esri_generation` | `config/consolidation_sources.yaml` | Tunable parallelism |

### 2. Efficiency of Processing

| Enhancement | Config Keys to Add | Location |
|-------------|-------------------|----------|
| **Baseline tracking** | `baseline.enabled`, `baseline.path`, `baseline.date_range`, `baseline.record_count` | `config/consolidation_sources.yaml` |
| **Incremental mode** | `incremental.enabled`, `incremental.mode`, `incremental.last_run_date`, `incremental.dedup_strategy` | `config/consolidation_sources.yaml` |
| **Performance tuning** | `performance.parallel_loading.enabled`, `performance.chunked_reading.threshold_mb`, `performance.memory_optimization.use_categories` | `config/consolidation_sources.yaml` |

**Key Script Flow Change:**
```
BEFORE: Always read 8 yearly files (714K records) from scratch
AFTER:  Check baseline.enabled → load single baseline file → append new monthly only
```

### 3. Organization Improvements

| Enhancement | What to Create | Purpose |
|-------------|----------------|---------|
| **manifest.json** | `13_PROCESSED_DATA/manifest.json` | Tracks latest polished file, record counts, checksums |
| **Run-specific report folders** | `consolidation/reports/YYYY_MM_DD_consolidation/` | Auditable history of all runs |
| **latest.json pointers** | `consolidation/reports/latest.json` | Easy "get latest report" for scripts |
| **cad/rms report separation** | `monthly_validation/reports/cad/`, `monthly_validation/reports/rms/` | Clear separation by data source |
| **Action items export** | `action_items.xlsx` in each validation run | Structured list for manual corrections |

**Directory Layout:**
```
13_PROCESSED_DATA/
├── manifest.json                  # NEW: Latest file registry
├── ESRI_Polished/
│   ├── base/                     # Immutable baseline (724K records)
│   └── incremental/              # NEW: Run outputs by date
│       └── 2026_02_01_append/
```

---

## Implementation Checklist

### Phase 1: Paths and Baseline (Do First)
- [ ] Create `13_PROCESSED_DATA/ESRI_Polished/base/` directory
- [ ] Copy current polished file to base
- [ ] Create `manifest.json` with baseline entry
- [ ] Add `baseline` section to `config/consolidation_sources.yaml`
- [ ] Add `incremental` section to `config/consolidation_sources.yaml`

### Phase 2: Reports Reorganization
- [ ] Create `consolidation/reports/` directory
- [ ] Create `monthly_validation/reports/cad/` and `.../rms/`
- [ ] Add `latest.json` files
- [ ] Migrate `outputs/consolidation/` to `consolidation/reports/2026_01_30_legacy/`
- [ ] Update report paths in `consolidate_cad_2019_2026.py`

### Phase 3: Server Copy Script
- [ ] Update `copy_consolidated_dataset_to_server.ps1` to read from `manifest.json`
- [ ] Add file size verification step

### Phase 4: Speed Optimizations
- [ ] Add `load_files_parallel()` function
- [ ] Add `load_excel_chunked()` function
- [ ] Add `optimize_dtypes()` function
- [ ] Add `performance` section to config
- [ ] Create `consolidate_cad_incremental.py`

### Phase 5: Monthly Validation
- [ ] Add `monthly_processing` section to config
- [ ] Implement action items export format
- [ ] Wire in vectorized validation from CAD_Data_Cleaning_Engine

---

## Config Changes Summary

Add these sections to `config/consolidation_sources.yaml`:

```yaml
# 1. Baseline configuration
baseline:
  enabled: true
  path: "...13_PROCESSED_DATA/ESRI_Polished/base/CAD_ESRI_Polished_Baseline_20190101_20260130.xlsx"
  date_range:
    start: "2019-01-01"
    end: "2026-01-30"
  record_count: 724794

# 2. Incremental mode
incremental:
  enabled: true
  mode: "append"
  last_run_date: null
  dedup_strategy: "keep_latest"

# 3. Performance settings
performance:
  parallel_loading:
    enabled: true
    max_workers: 8
  chunked_reading:
    enabled: true
    threshold_mb: 50
    chunk_size: 100000

# 4. Processed data paths
processed_data:
  root: "...13_PROCESSED_DATA"
  manifest_path: "${processed_data.root}/manifest.json"
```

---

## Questions Answered

**Q: Should monthly validation use the same parallel/chunking patterns as consolidation?**

**A: Partially.** Monthly files are typically 2,500-3,000 records (~1-2MB). Parallel *loading* would add overhead. However:
- Use **vectorized validation** (pandas-based, not row-by-row)
- Enable parallel loading only for batch catch-up scenarios (processing multiple months)

**Q: Is the split between consolidation/reports and monthly_validation/reports right?**

**A: Yes, keep them separate.** Consolidation runs produce different outputs than monthly validation. Add `cad/` and `rms/` subfolders under `monthly_validation/reports/` for cleaner organization.

**Q: Should there be a single paths.yaml or new sections in existing YAML?**

**A: Add sections to existing files** (less file sprawl). Add `baseline`, `incremental`, `performance`, and `processed_data` sections to `config/consolidation_sources.yaml`. Only create separate `paths.yaml` if the config becomes unwieldy (>300 lines).

---

## Files Changed/Created

| File | Action | Purpose |
|------|--------|---------|
| `CAD_RMS_Data_Quality_Expansion_Plan_ENHANCED.md` | Created | Enhanced plan with all recommendations |
| `ENHANCEMENT_SUMMARY.md` | Created | This summary document |
| `config/consolidation_sources.yaml` | To modify | Add baseline, incremental, performance, processed_data sections |
| `consolidate_cad_2019_2026.py` | To modify | Add parallel loading, chunked reading, new report paths |
| `consolidate_cad_incremental.py` | To create | Baseline + append mode script |
| `shared/utils/memory_optimizer.py` | To create | Dtype optimization utility |
| `copy_consolidated_dataset_to_server.ps1` | To modify | Read from manifest.json |
| `13_PROCESSED_DATA/manifest.json` | To create | Latest file registry |

---

**Next Step:** Review the enhanced plan and begin implementation with Phase 1 (Paths and Baseline).
