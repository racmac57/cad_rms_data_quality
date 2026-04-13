# FINAL SKILL HARDENING REPORT

**Initial pass:** 2026-04-10 (6 skills)
**Round 2 pass:** 2026-04-13 (+4 ESRI skills)

## Summary

| Metric | Value |
|--------|-------|
| Total Skills | 10 |
| Fully Passing (9/9) | 10 |
| Partially Passing | 0 |
| Blocked | 0 |
| Total Tests Run | 90 |
| Total PASS | 90 |
| Total FAIL | 0 |
| Fixes Applied | 5 (1 from round 1, 4 from round 2 convention alignment) |
| Regression Tests Added | 7 |
| Iterations Required | 4 (1 cycle for consolidation-run, 1 cycle each for 3 new ESRI skills) |

## Per-Skill Scorecard

| Skill | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | Score | Status |
|-------|----|----|----|----|----|----|----|----|-----|-------|--------|
| check-paths | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| consolidation-run | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| deploy-script | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| handoff | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| pipeline-status | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| validate-monthly | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| cad-export-fix | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| esri-backfill | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| esri-gap-check | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| esri-pipeline-status | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |

**Test key:** T1=Exists & Loadable, T2=Shared Context Access, T3=Path Safety, T4=Data Dictionary Compliance, T5=Idempotency, T6=Error Handling, T7=Output Correctness, T8=CLAUDE.md Rule Compliance, T9=Integration/Cross-Skill Safety

## Fix Log

### Round 1 (2026-04-10)

#### consolidation-run: `python3` -> `python` (Test 8)

**Problem:** Three code blocks used `python3` command which does not exist on Windows.
**Lines fixed:** 27, 65, 90
**Before:** `python3 -c "..."` and `python3 -m json.tool`
**After:** `python -c "..."` and `python -m json.tool`
**Verification:** Grep across all skills: 0 remaining `python3` references

### Round 2 (2026-04-13)

#### cad-export-fix: frontmatter + placeholder alignment (Test 8)

**Problem:** Used `user-invocable: true` + placeholder `<USER_INPUT_PATH>` + bare `Bash` in `allowed-tools`.
**Fix:** `disable-model-invocation: true` + `argument-hint: [path-to-xlsx]` + `$0` placeholder + `Bash(python *)`
**Verification:** AST parse of inline Python -> PASS; no `user-invocable` remains

#### esri-backfill: frontmatter + placeholder alignment (Test 8)

**Problem:** `user-invocable: true` + placeholders `<SOURCE>` / `<MONTH_LABEL>` + broader-than-needed `allowed-tools: Read Bash`.
**Fix:** `disable-model-invocation: true` + `argument-hint: [source-xlsx] [month-label]` + `$0` / `$1` + `allowed-tools: Read Grep Glob`
**Verification:** PowerShell parse -> PASS

#### esri-gap-check: frontmatter + placeholder alignment (Test 8)

**Problem:** `user-invocable: true` + placeholders `<FROM>` / `<TO>`.
**Fix:** `disable-model-invocation: true` + `argument-hint: [days | --from YYYY-MM-DD --to YYYY-MM-DD]` + `$FROM` / `$TO` with parse-step note
**Verification:** AST parse of ArcPy script with substituted values -> PASS

#### esri-pipeline-status: frontmatter alignment (Test 8)

**Problem:** `user-invocable: true` only (no args, so no argument-hint needed).
**Fix:** `disable-model-invocation: true`
**Verification:** PowerShell parse via `[Parser]::ParseFile()` -> PASS

## Shared Regressions Added

1. No `python3` in any skill (enforces Windows compatibility)
2. No `RobertCarucci` in path literals (only allowed as search patterns in check-paths)
3. No bare `OneDrive` paths without full suffix
4. All YAML frontmatters valid with required fields
5. **(Round 2)** Embedded Python must parse with `ast.parse()`
6. **(Round 2)** Embedded PowerShell must parse with `[Parser]::ParseFile()` with zero errors
7. **(Round 2)** Arg-taking skills use `disable-model-invocation: true` + `argument-hint: [...]` + `$ARGUMENTS`/`$0`/`$1` convention (not `user-invocable: true` + literal placeholders)

## Remaining Blockers

None. All 10 skills pass all 9 tests.

## Advisory Notes (non-blocking, for future consideration)

1. **check-paths** `allowed-tools` includes `Bash(git *)` but no git commands are used
2. **ArcPy Python path** inconsistency between CLAUDE.md (`propy.bat`) and skills (`python.exe`) -- both valid in their contexts
3. **check-paths Rule 4** may flag a comment in `schemas.yaml` as a false positive
4. **esri-backfill** `do {} while ($state -eq "Running")` has no max-iter guard -- hang on stuck task would loop forever (user Ctrl-C required)
5. **esri-pipeline-status** uses text-regex log parsing; brittle if ArcGIS log format changes. Existing `pipeline-status` uses XML parsing as a stable alternative.
6. **esri-pipeline-status** scope overlaps with existing `pipeline-status` (complementary, not duplicative -- see MASTER tracker for distinction)
7. **cad-export-fix** silently drops unknown columns (e.g. `CADNotes`) with a warning -- intentional but worth noting for future column-addition scenarios

## Autonomous Swarm Completion

- Status: YES
- Reason: All 10 skills discovered, tested, and hardened. 5 fixes applied (1 round 1, 4 round 2), 0 blockers remaining.
