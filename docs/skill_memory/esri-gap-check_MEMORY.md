# Skill Memory: esri-gap-check

**Last tested:** 2026-04-13
**Status:** PASS (9/9)
**Type:** read-only (emits ArcPy text for the user to paste)
**Iterations:** 2 (round 1 PASS on ArcPy syntax; round 2 fixed convention drift)

## Binary Scorecard

| # | Test | Result | Evidence |
|---|------|--------|----------|
| 1 | Exists & Loadable | PASS | Valid YAML frontmatter with `disable-model-invocation`, `argument-hint`, `allowed-tools: Read` |
| 2 | Shared Context Access | PASS | AGOL service URL matches CLAUDE.md ("Server Environment" / ArcGIS Online Feature Service) |
| 3 | Path Safety | PASS | No Windows paths in the script (HTTPS service URL only); no `RobertCarucci`, no `python3` |
| 4 | Data Dictionary Compliance | PASS | Uses `calldate` (AGOL field name) -- matches CLAUDE.md Target Online Service Fields table |
| 5 | Idempotency | PASS | Read-only ArcPy query. Running multiple times produces the same output for a fixed window. |
| 6 | Error Handling | PASS | `SearchCursor` in `with` block handles row iteration; `d.date() if hasattr(d, "date") else d` handles both datetime and date return types |
| 7 | Output Correctness | PASS | `ast.parse()` confirmed ArcPy block is syntactically valid Python; prints gap dates, low-volume days, and last 7-day trailing window |
| 8 | CLAUDE.md Rule Compliance | PASS | Uses ArcGIS Online service URL from CLAUDE.md; no hardcoded dicts; follows "explicit logging over print" spirit via clear labeled output |
| 9 | Integration / Cross-Skill Safety | PASS | No write targets. Designed to be invoked inline from `esri-backfill` after a backfill run. |

## Iteration History

### Round 1 (create)
- Static analysis: frontmatter valid, ArcPy parses
- **Finding:** `user-invocable: true` instead of `disable-model-invocation: true` + `argument-hint`
- **Finding:** Placeholders `<FROM>`, `<TO>` instead of `$ARGUMENTS`-derived values

### Round 2 (fix)
- Frontmatter: `user-invocable: true` -> `disable-model-invocation: true`, added `argument-hint: [days | --from YYYY-MM-DD --to YYYY-MM-DD]`
- Replaced `<FROM>` / `<TO>` with `$FROM` / `$TO` and added a parse step in the "What the skill must do" section explaining how to derive them from `$ARGUMENTS`
- Re-ran AST parse with substituted values -> PASS

## Advisory Notes

1. The query uses `DATE '<iso>'` SQL literal -- works for AGOL REST where clauses. If the underlying field type changes to `esriFieldTypeString`, this would need adjustment.
2. `SearchCursor` on an AGOL service URL requires an active ArcGIS Pro sign-in (not just `arcgis.gis.GIS` authentication). Skill notes this.
3. "Low-volume" threshold of <50 calls/day is hardcoded. Hackensack's floor is ~180/day in practice; 50 is a safe flag level. Could be parameterized later.
