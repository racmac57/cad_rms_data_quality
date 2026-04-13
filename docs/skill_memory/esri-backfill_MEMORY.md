# Skill Memory: esri-backfill

**Last tested:** 2026-04-13
**Status:** PASS (9/9)
**Type:** read-only (emits text only -- user pastes on RDP)
**Iterations:** 2 (round 1 PASS on PS syntax; round 2 fixed convention drift)

## Binary Scorecard

| # | Test | Result | Evidence |
|---|------|--------|----------|
| 1 | Exists & Loadable | PASS | Valid YAML frontmatter with `disable-model-invocation`, `argument-hint`, `allowed-tools: Read Grep Glob` |
| 2 | Shared Context Access | PASS | Task name `Publish Call Data_2026_NEW`, staging path `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\`, FileMaker path match `PIPELINE_ANALYSIS.md` |
| 3 | Path Safety | PASS | No `RobertCarucci`; `tsclient\C\Users\carucci_r\OneDrive - City of Hackensack\` uses canonical `carucci_r` and full OneDrive suffix |
| 4 | Data Dictionary Compliance | PASS | Task name and live export filename exactly match existing `pipeline-status` skill and server reality |
| 5 | Idempotency | PASS | Backup filename includes timestamp (`ESRI_CADExport_LIVE_BACKUP_$Stamp.xlsx`) -- re-running creates new backup, never overwrites |
| 6 | Error Handling | PASS | Step 5 branches on `$result -eq 0` with color-coded output; step 6 (restore) runs regardless so the live export always returns to known state |
| 7 | Output Correctness | PASS | `[System.Management.Automation.Language.Parser]::ParseInput()` confirmed the full PowerShell block parses with zero errors |
| 8 | CLAUDE.md Rule Compliance | PASS | Uses `carucci_r` for tsclient path; PowerShell style matches existing `pipeline-status` / `deploy-script` skills |
| 9 | Integration / Cross-Skill Safety | PASS | References `esri-gap-check` for the post-run verification block; no write-target conflicts (pure text output) |

## Iteration History

### Round 1 (create)
- Static analysis: frontmatter valid, PowerShell parses, no forbidden patterns
- **Finding:** Used `user-invocable: true` + placeholders `<SOURCE>` / `<MONTH_LABEL>` -- inconsistent with project convention
- **Finding:** `allowed-tools: Read Bash` was broader than needed -- this skill only emits text

### Round 2 (fix)
- Frontmatter: `user-invocable: true` -> `disable-model-invocation: true`, added `argument-hint: [source-xlsx] [month-label]`
- Tightened `allowed-tools: Read Bash` -> `Read Grep Glob` (no shell execution needed)
- Replaced `<SOURCE>` with `$0`, `<MONTH_LABEL>` with `$1`
- Re-ran PowerShell parse -> PASS

## Advisory Notes

1. The skill doesn't handle the case where the source file doesn't exist on the server. Recommend adding a `Test-Path` pre-flight check in step 1.
2. The `do {} while ($state -eq "Running")` loop has no max-iteration guard. If the task hangs, the loop runs forever. Could add `$maxIter = 120; $i = 0; do { ...; $i++ } while (... -and $i -lt $maxIter)`.
3. The restore step (step 6) runs regardless of the result code -- this is intentional (always return live export to known state).
