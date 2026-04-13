# Skill Memory: esri-pipeline-status

**Last tested:** 2026-04-13
**Status:** PASS (9/9)
**Type:** read-only (emits PowerShell text for the user to paste on RDP)
**Iterations:** 2 (round 1 PASS on PS syntax; round 2 aligned frontmatter)

## Binary Scorecard

| # | Test | Result | Evidence |
|---|------|--------|----------|
| 1 | Exists & Loadable | PASS | Valid YAML frontmatter with `disable-model-invocation`, `allowed-tools: Read` |
| 2 | Shared Context Access | PASS | Log path `C:\Users\administrator.HPD\AppData\Local\ESRI\ArcGISPro\Geoprocessing\ScheduledTools\Logs` matches existing `pipeline-status` skill |
| 3 | Path Safety | PASS | No `RobertCarucci`; `administrator.HPD` is the real server account (not a typo of user) |
| 4 | Data Dictionary Compliance | PASS | Task names `Publish Call Data_2026_NEW`, `Publish Crime Data_2026` match the existing `pipeline-status` skill and server reality. Status codes 4=success, 5=license, 0=unknown match handoff docs. |
| 5 | Idempotency | PASS | Read-only PowerShell; runs produce snapshot of current state |
| 6 | Error Handling | PASS | `-ErrorAction SilentlyContinue` on Get-ScheduledTaskInfo, Get-ChildItem, and Get-Content; `if ($info)` guards for missing tasks |
| 7 | Output Correctness | PASS | `[System.Management.Automation.Language.Parser]::ParseFile()` confirmed zero parse errors; emits a `Format-Table` with 6 named columns |
| 8 | CLAUDE.md Rule Compliance | PASS | No hardcoded mappings; PowerShell style matches existing `pipeline-status` / `deploy-script` skills |
| 9 | Integration / Cross-Skill Safety | PARTIAL-OK (see note) | Scope overlap with existing `pipeline-status` skill -- see advisory |

## Iteration History

### Round 1 (create)
- Static analysis: frontmatter valid, PowerShell parses
- **Finding:** `user-invocable: true` instead of the dominant `disable-model-invocation: true` convention
- No arguments; no placeholder issues

### Round 2 (fix)
- Frontmatter: `user-invocable: true` -> `disable-model-invocation: true`
- Re-ran PowerShell parse via `[Parser]::ParseFile()` -> PASS

## Advisory Notes

1. **Scope overlap with `pipeline-status`.** The existing `pipeline-status` skill already covers all 4 ESRI tasks (CAD/NIBRS exports + Call/Crime publishes) using XML log parsing. This new skill focuses specifically on the 2 publish tasks, scrapes log content for status + record counts, and reads the log files as text rather than XML. They are complementary, not duplicates:
   - `pipeline-status`: broad status of all 4 tasks, accepts `[call-data|crime-data|all]` arg, parses XML `Result/@status` attribute
   - `esri-pipeline-status`: deep scrape of the 2 publish tasks' logs, extracts record counts via regex
2. The log parser uses text-mode regex (`status["'']?\s*[:=]\s*(\d+)`) rather than XML parsing. The existing `pipeline-status` uses `[xml]$log = ...`. Both work because ArcGIS ScheduledTools logs have `status="4"` as an XML attribute -- text regex catches it as a substring. If ArcGIS ever changes log format, the regex approach is more brittle than XML parsing.
3. "Records" column is best-effort -- any "<number> records|features|rows" pattern in the log will match. Treat as sanity check, not authoritative.
