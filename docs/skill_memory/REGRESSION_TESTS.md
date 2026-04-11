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
3. All 6 `SKILL.md` files must have valid YAML frontmatter with `name:` and `allowed-tools:`
4. No two write-capable skills share the same output directory
