# Regression Tests

**Date:** 2026-04-10
**Trigger:** consolidation-run `python3` -> `python` fix

## Post-Fix Regression Scan

After fixing `python3` to `python` in consolidation-run/SKILL.md (3 occurrences), the following regression checks were run:

| Check | Scope | Result | Evidence |
|-------|-------|--------|----------|
| `python3` eliminated | All 6 skills | PASS | Grep: 0 matches across `.claude/skills/` |
| `RobertCarucci` in path literals | All 6 skills | PASS | Only in check-paths as search pattern |
| Bare `OneDrive` paths | All 6 skills | PASS | Grep: 0 matches |
| YAML frontmatter intact | All 6 skills | PASS | All 6 have valid name, description, allowed-tools |
| Read-only skills unchanged | check-paths, deploy-script, pipeline-status | PASS | No edits to these files |
| Write-capable output dirs disjoint | consolidation-run, handoff, validate-monthly | PASS | No path overlap |

## Standing Regression Checks

These checks should be re-run after any skill modification:

1. `grep -rn "python3" .claude/skills/` -- must return 0 matches
2. `grep -rn "RobertCarucci" .claude/skills/ | grep -v "search\|pattern\|Rule\|check"` -- must return 0 matches
3. All `SKILL.md` files must have valid YAML frontmatter with `name:` and `allowed-tools:`
4. No two write-capable skills share the same output directory
5. **(Added 2026-04-13)** Embedded Python in any skill must parse with `ast.parse()`
6. **(Added 2026-04-13)** Embedded PowerShell in any skill must parse with `[System.Management.Automation.Language.Parser]::ParseFile()` with zero errors
7. **(Added 2026-04-13)** Arg-taking skills should prefer `disable-model-invocation: true` + `argument-hint: [...]` + `$ARGUMENTS`/`$0`/`$1` over `user-invocable: true` + literal placeholders (convention consistency)

## 2026-04-13 Round 2 Regression Scan

After adding 4 new ESRI skills (cad-export-fix, esri-backfill, esri-gap-check,
esri-pipeline-status) and aligning their frontmatter + arg conventions:

| Check | Scope | Result | Evidence |
|-------|-------|--------|----------|
| `python3` eliminated | All 10 skills | PASS | Grep: 0 matches across `.claude/skills/` |
| `RobertCarucci` in path literals | All 10 skills | PASS | Only in check-paths as search pattern |
| Bare `OneDrive` paths | All 10 skills | PASS | Grep: 0 matches |
| `user-invocable` on arg-taking skills | 4 new skills | PASS after fix | Swapped to `disable-model-invocation: true` + `argument-hint` |
| Embedded Python AST parse | cad-export-fix, esri-gap-check | PASS | `ast.parse()` succeeds on both scripts |
| Embedded PowerShell parse | esri-backfill, esri-pipeline-status | PASS | `[Parser]::ParseFile()` reports 0 errors |
| Existing 6 skills unchanged | check-paths, consolidation-run, deploy-script, handoff, pipeline-status, validate-monthly | PASS | No edits to those files |
| Write target disjointness | All 10 skills | PASS | `cad-export-fix` writes to user-supplied dir; others either write unique paths or text only |
