---
name: consolidation-run
description: Execute the CAD consolidation pipeline (full mode), verify record counts against expected thresholds, and report quality metrics. Use when running a new consolidation after monthly data arrives.
disable-model-invocation: true
argument-hint: [--dry-run]
allowed-tools: Bash(python *) Bash(pip *) Read Grep Glob
---

# Consolidation Run

Execute `consolidate_cad_2019_2026.py --full` and verify the output.

## Arguments

- `$ARGUMENTS` -- Pass `--dry-run` to only show pre-flight checks without running.

## Pre-Flight Checks

Before running, verify these conditions:

### 1. Config is current

Read `config/consolidation_sources.yaml` and check:

```bash
# Show configured sources and their expected counts
python -c "
import yaml
with open('config/consolidation_sources.yaml') as f:
    cfg = yaml.safe_load(f)
print('=== Yearly Sources ===')
for s in cfg['sources']['yearly']:
    print(f\"  {s['year']}: expected={s.get('expected_records', '?')} - {s['path'].split(chr(92))[-1]}\")
print()
print('=== Monthly Sources ===')
for s in cfg['sources']['monthly']:
    print(f\"  {s['month']}: {s['path'].split(chr(92))[-1]}\")
print()
print(f\"Baseline: {cfg['baseline']['path'].split(chr(92))[-1]}\")
print(f\"Baseline records: {cfg['baseline']['record_count']}\")
print(f\"Date range: {cfg['baseline']['date_range']['start']} to {cfg['baseline']['date_range']['end']}\")
"
```

### 2. Mode is full (not incremental)

Verify the config enforces full mode:
```bash
grep -A2 "incremental:" config/consolidation_sources.yaml | head -5
# Must show: enabled: false, mode: "full"
```

**CRITICAL:** Incremental mode is deprecated and causes data loss. Always use `--full`.

### 3. Output directory exists

```bash
ls -la consolidation/output/
ls -la consolidation/reports/
```

### 4. Dependencies available

```bash
python -c "import pandas, yaml, openpyxl, numpy; print('All dependencies OK')"
```

## If `--dry-run`: stop here and report pre-flight results.

## Execution

```bash
python consolidate_cad_2019_2026.py --full 2>&1 | tee consolidation/logs/run_$(date +%Y%m%d_%H%M%S).log
```

If this fails because the script expects Windows paths (OneDrive), tell the user:
- The consolidation script reads Excel files from `C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\`
- It must run on the Windows machine or the RDP server
- Generate the exact command for them to run there

## Post-Run Verification

### 1. Read the run report

```bash
# Find the most recent report
LATEST=$(ls -td consolidation/reports/*/  | head -1)
echo "Latest report: $LATEST"
cat "${LATEST}consolidation_summary.txt"
cat "${LATEST}consolidation_metrics.json" | python -m json.tool
```

### 2. Validate against thresholds

Apply thresholds from `config/consolidation_sources.yaml`:

| Metric | Threshold | Source |
|--------|-----------|--------|
| Total records | 700,000 - 800,000 | `validation.expected_total_records_min/max` |
| Quality score | >= 95 | `validation.min_quality_score` |
| Duplicate rate | <= 1% | `validation.max_duplicate_rate` |

### 3. Check for common issues

- **Record count drop** vs. previous run -- compare with prior `consolidation_metrics.json`
- **Missing months** -- verify all configured sources were loaded
- **Duplicate spike** -- may indicate overlapping date ranges in monthly + yearly files

## Report to User

```
## Consolidation Run: YYYY-MM-DD

**Status:** SUCCESS / FAILED
**Total Records:** XXX,XXX (threshold: 700K-800K)
**Quality Score:** XX/100 (threshold: >= 95)
**Duplicate Rate:** X.XX% (threshold: <= 1%)
**Duration:** X min Y sec

### Sources Loaded
- 2019: XX,XXX records
- 2020: XX,XXX records
- ...
- 2026-03: X,XXX records

### Comparison with Previous Run
- Previous: XXX,XXX records (YYYY-MM-DD)
- Delta: +X,XXX records

### Issues Found
- (none / list issues)

### Output File
- consolidation/output/<filename>.csv
```

## Performance Notes

The consolidation script uses:
- **Parallel loading:** 8 workers (configurable in `performance.parallel_loading.max_workers`)
- **Chunked reading:** Files >50MB read in 100K-row chunks
- **Memory optimization:** Categorical dtypes for low-cardinality strings
- Typical runtime: 2-3 minutes for full consolidation on a modern machine
