# Skill Memory: validate-monthly

**Last tested:** 2026-04-10
**Status:** PASS (9/9)
**Type:** write-capable
**Iterations:** 1 (no fixes required)

## Binary Scorecard

| # | Test | Result |
|---|------|--------|
| 1 | Exists & Loadable | PASS |
| 2 | Shared Context Access | PASS |
| 3 | Path Safety | PASS |
| 4 | Data Dictionary Compliance | PASS |
| 5 | Idempotency | PASS |
| 6 | Error Handling | PASS |
| 7 | Output Correctness | PASS |
| 8 | CLAUDE.md Rule Compliance | PASS |
| 9 | Integration / Cross-Skill Safety | PASS |

## Evidence

- **T1:** Valid frontmatter with `argument-hint: [cad|rms] [YYYY-MM]`
- **T2:** All deps verified: `run_all_validations.py` (accepts `--validators`), `validate_cad.py`, `validate_rms.py`, `validation_rules.yaml`, `monthly_validation/reports/`
- **T3:** Two paths (lines 24-25) use `carucci_r` + full OneDrive suffix; 0 RobertCarucci
- **T4:** Field names (ReportNumberNew, Incident, FullAddress2) match CLAUDE.md; all 9 validator class names map to actual files; case number pattern matches `validation_rules.yaml`
- **T5:** Timestamped output dirs; same-day overwrite acceptable for validation reports
- **T6:** Local vs server guidance; 3-tier quality thresholds (Pass/Warning/Fail); record count anomaly flagging
- **T7:** Summary template with Quality Score, Records, Duplicates, Field Completeness, Action Items, Recommendation
- **T8:** Uses `python` (not `python3`); quality weights match CLAUDE.md (30/25/20/15/10); correct validator names
- **T9:** Writes to `monthly_validation/reports/` only; disjoint from `consolidation/` output
