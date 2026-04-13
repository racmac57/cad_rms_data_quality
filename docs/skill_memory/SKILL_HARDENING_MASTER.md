# Skill Hardening Master Tracker

**Project:** CAD/RMS Data Quality System
**Initial pass:** 2026-04-10 (6 skills)
**Round 2 pass:** 2026-04-13 (+4 ESRI skills)
**Skills discovered:** 10
**Skills passing:** 10 (100%)

## Global Status

| Skill | Type | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | Score | Status |
|-------|------|----|----|----|----|----|----|----|----|-----|-------|--------|
| check-paths | read-only | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| consolidation-run | write-capable | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| deploy-script | read-only | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| handoff | write-capable | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| pipeline-status | read-only | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| validate-monthly | write-capable | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| cad-export-fix | write-capable | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| esri-backfill | read-only | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| esri-gap-check | read-only | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |
| esri-pipeline-status | read-only | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 9/9 | PASS |

**Test legend:** T1=Exists, T2=Context, T3=Paths, T4=DataDict, T5=Idempotent, T6=Errors, T7=Output, T8=CLAUDE.md, T9=Integration

## Skill Classification

| Skill | Type | allowed-tools | Write targets |
|-------|------|---------------|---------------|
| check-paths | read-only | Bash(git *) Read Grep Glob | None |
| consolidation-run | write-capable | Bash(python *) Bash(pip *) Read Grep Glob | consolidation/output/, reports/, logs/ |
| deploy-script | read-only | Read Grep Glob | None |
| handoff | write-capable | Bash(git log *) Read Grep Glob | docs/ai_handoff/ |
| pipeline-status | read-only | Read Grep | None |
| validate-monthly | write-capable | Bash(python *) Bash(pip *) Read Grep Glob | monthly_validation/reports/ |
| cad-export-fix | write-capable | Read Bash(python *) Write | `<input>_FIXED.xlsx` (user-supplied directory) |
| esri-backfill | read-only | Read Grep Glob | None (emits text block) |
| esri-gap-check | read-only | Read | None (emits ArcPy text) |
| esri-pipeline-status | read-only | Read | None (emits PowerShell text) |

## Cross-Skill Dependency Map

```
check-paths ----reads----> config/*.yaml, *.py files
consolidation-run --reads--> config/consolidation_sources.yaml
                  --runs---> consolidate_cad_2019_2026.py
                  --writes-> consolidation/output/, reports/, logs/

deploy-script ----reads----> arbitrary script files ($0 arg)
                  --generates-> PowerShell commands (text output only)

handoff ----------reads----> git log, docs/ai_handoff/*.md
                  --writes-> docs/ai_handoff/HANDOFF_*.md

pipeline-status --generates-> PowerShell commands (text output only)

validate-monthly -reads----> config/*.yaml, validation/run_all_validations.py
                  --runs---> validation scripts
                  --writes-> monthly_validation/reports/

cad-export-fix --reads----> user-supplied .xlsx
                 --runs---> python (pandas) to rename/reorder columns
                 --writes-> <input>_FIXED.xlsx (alongside input)

esri-backfill --reads----> nothing (emits PowerShell text)
               --generates-> PowerShell block for user to paste on RDP
               --references-> esri-gap-check (emits its block as a companion)

esri-gap-check --generates-> ArcPy block for user to paste in ArcGIS Pro
                 --queries--> AGOL CallsForService feature service

esri-pipeline-status --generates-> PowerShell block for user to paste on RDP
                       --reads---> nothing locally (no shared write targets)
```

**Write target conflicts:** NONE. `cad-export-fix` writes to wherever the user's input
file lives, which is outside every other skill's scope. All text-emitting skills have
no write targets.

**Scope overlap note:** `esri-pipeline-status` and `pipeline-status` are complementary,
not duplicative. `pipeline-status` covers all 4 ESRI tasks via XML log parsing; the new
`esri-pipeline-status` deep-scrapes the 2 publish tasks' logs for status + record
counts. Both are valid entry points depending on what the user needs.

## Shared Lessons Learned

1. **Windows vs Linux commands:** Use `python` not `python3` on Windows. All skill commands must be Windows-compatible since the environment is Windows 11.
2. **ArcPy Python paths:** `propy.bat` (CLAUDE.md canonical) and `envs\arcgispro-py3\python.exe` (skills) are both valid. Direct `python.exe` is preferred for Task Scheduler jobs.
3. **Read-only skills are inherently safe:** Skills restricted to `Read Grep Glob` cannot cause side effects. The pipeline-status skills have the most restrictive toolset (`Read Grep` or just `Read`).
4. **Frontmatter convention for user-invoked skills with args:** Use `disable-model-invocation: true` + `argument-hint: [...]`, and reference args as `$ARGUMENTS` / `$0` / `$1` in the body. This was caught in the 2026-04-13 round 2 pass where 4 new skills initially used `user-invocable: true` + literal placeholders.
5. **Embedded script validation:** Python code in SKILL.md can be AST-parsed with `ast.parse()`; PowerShell code with `[System.Management.Automation.Language.Parser]::ParseFile()`. Syntax errors in emitted scripts are catchable at hardening time, not runtime.

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| check-paths Rule 4 false positive on comments | Low | Agent reviewer would dismiss; could add `grep -v "^#"` |
| Same-day handoff overwrite | Low | Intentional behavior; user gate at Step 5 |
| validate-monthly same-day report overwrite | Low | Acceptable for validation reports |
| esri-backfill hangs if task never leaves Running state | Low | User can Ctrl-C; recommend adding max-iter guard to `do {} while` loop |
| esri-pipeline-status regex-based log parsing brittle if ArcGIS log format changes | Low | Existing `pipeline-status` uses XML parsing as a stable alternative |
| cad-export-fix silently drops unknown columns (`CADNotes` etc.) | Low | Intentional; warned in output but non-fatal. Model schema is the source of truth. |
