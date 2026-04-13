# Skill Memory: cad-export-fix

**Last tested:** 2026-04-13
**Status:** PASS (9/9)
**Type:** write-capable (writes `<input>_FIXED.xlsx` alongside input)
**Iterations:** 2 (round 1 PASS on syntax; round 2 fixed convention drift)

## Binary Scorecard

| # | Test | Result | Evidence |
|---|------|--------|----------|
| 1 | Exists & Loadable | PASS | Valid YAML frontmatter (`name`, `description`, `disable-model-invocation`, `argument-hint`, `allowed-tools`) |
| 2 | Shared Context Access | PASS | Schema cross-checked against HANDOFF_20260413_ESRI_Skills_To_Build.md -- 21 columns match `EXPORT_SCHEMA.md` |
| 3 | Path Safety | PASS | No `RobertCarucci`, no `python3`, no bare `OneDrive`. Only `carucci_r` in example path. |
| 4 | Data Dictionary Compliance | PASS | Column names match live schema: `ReportNumberNew`, `Time of Call`, `How Reported`, `Hour_Calc`, `FullAddress2`, `latitude`, `longitude`, etc. |
| 5 | Idempotency | PASS | Writes `_FIXED.xlsx` (new file, never overwrites input). Re-running produces identical output. |
| 6 | Error Handling | PASS | Inline Python exits non-zero on missing required columns (sys.exit(1)); warns (non-fatal) on extras |
| 7 | Output Correctness | PASS | `ast.parse()` confirmed Python block is syntactically valid; writes .xlsx via pandas with all 21 target columns in order |
| 8 | CLAUDE.md Rule Compliance | PASS | Forces `ReportNumberNew` to `str` dtype on load (CLAUDE.md explicit rule); uses `pathlib.Path`; no hardcoded mappings dict |
| 9 | Integration / Cross-Skill Safety | PASS | No shared write targets with other skills; output is consumed downstream by `esri-backfill` (documented in Notes) |

## Iteration History

### Round 1 (create)
- Static analysis: frontmatter valid, embedded Python parses, no forbidden path patterns
- **Finding:** Used `user-invocable: true` and placeholder `<USER_INPUT_PATH>` -- inconsistent with project convention (5 of 6 existing arg-taking skills use `disable-model-invocation: true` + `argument-hint` + `$0`/`$ARGUMENTS`)

### Round 2 (fix)
- Changed frontmatter: `user-invocable: true` -> `disable-model-invocation: true`, added `argument-hint: [path-to-xlsx]`
- Tightened `allowed-tools: Read Bash Write` -> `Read Bash(python *) Write`
- Replaced `<USER_INPUT_PATH>` placeholder with `$0` (matches deploy-script convention)
- Re-ran AST parse on inline Python -> PASS

## Advisory Notes

1. The inline Python uses `python -c '<script>'` style. For multi-line scripts, writing to a temp `.py` file and running it is cleaner -- the skill should do that when the script is long.
2. FileMaker never populates `latitude`/`longitude` -- the skill adds them as null. The downstream ArcGIS model geocodes from `FullAddress2` using the NJ State Plane Composite locator.
3. The skill does not validate cell content beyond column presence. Out-of-range dates or malformed case numbers will pass through unchanged.
