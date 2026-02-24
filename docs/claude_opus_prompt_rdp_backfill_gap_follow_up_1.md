> You previously produced v3 scripts: `probe_gap_record.py`, `fix_gap_calldate_local.py`, `fix_gap_calldate_online.py`. Please regenerate **v4** with the following requirements folded in. Output **all full scripts**.
>
> ---
>
> # Keep / confirm existing patches
>
> **Patch A (timezone hardening, all scripts) — must remain:**
>
> * Force `America/New_York` via `ZoneInfo`.
> * Conversion flow: naive datetime → stamp as NY → convert to UTC → epoch ms (AGOL). Reverse: epoch ms (UTC) → NY-aware datetime for display/derived fields.
> * `dispatchtime` computed as UTC-vs-UTC delta (DST-safe).
>
> **Patch A2 (probe mismatch detection) — must remain:**
>
> * Probe prints both `system_epoch_ms` (naive `.timestamp()`) and `ny_epoch_ms` (forced NY conversion).
> * If they differ, print delta seconds and a loud STOP warning.
>
> **Patch B (local WHERE clause) — must remain:**
>
> * Local cursor filter uses `callid LIKE '26-%'` (not lexicographic min/max) and relies on numeric `callid_in_gap_range()` inside loop.
>
> ---
>
> # Fix remaining operator cautions (new v4 work)
>
> ## 1) Add **local rollback** symmetry (`fix_gap_calldate_local.py`)
>
> * Implement CLI flag `--rollback <snapshot.json>` (or `--rollback` to auto-pick most recent snapshot in `snapshots/`).
> * Snapshot must include, per edited record: a stable key (`OBJECTID`), `callid`, and **all fields written by the script** (at minimum: `calldate`, `calldow`, `calldownum`, `callhour`, `callmonth`, `callyear`, `dispatchtime`, `responsetime`).
> * Rollback applies those “before” values back into `CFStable_GeocodeAddresses` using UpdateCursor by `OBJECTID`.
> * Rollback is **readable and loud**: prints count restored, and writes a rollback report JSON/CSV.
>
> ## 2) Add **live-run safety guardrails** (`fix_gap_calldate_local.py` + `fix_gap_calldate_online.py`)
>
> * Keep `DRY_RUN` toggle, but also require an explicit `--live` flag when `DRY_RUN=False`. If not provided, abort with a clear message.
> * Write logs + artifacts to an output folder: `./outputs/<timestamp>/` containing:
>
>   * `summary.json` (counts, timings)
>   * `changes.json` (before/after per record)
>   * `sample_before_after.csv` (human review)
>
> ## 3) Add **post-run audit + count assertions** (local + online)
>
> * Compute these counts and print them at end:
>
>   * lookup size (gap table)
>   * features matched in target (local/online)
>   * already-correct count
>   * updates-prepared count
>   * updates-succeeded / failed (online from edit_features result)
> * Add CLI: `--expected-updates N` and `--max-miss-rate PCT` (default e.g. 2%).
>
>   * If `abs(updates_prepared - expected) > expected * max_miss_rate`, **exit non-zero** and print why.
> * If `--expected-updates` not provided, still warn if prepared differs materially from lookup size.
>
> ## 4) Add **operator validation hooks**
>
> * Add CLI: `--sample-callids 26-011297,26-011300,...` (comma list).
> * For each sample callid, print:
>
>   * local table real datetime (gap table)
>   * current target value before
>   * value after (dry-run computed, or live re-query)
> * Online script should re-query those sample callids after live update and print the hosted layer values in NY time.
>
> ## 5) Make the scripts resilient + explicit
>
> * If any required field missing (schema drift), abort before doing any edits (both local + online).
> * If duplicate callids exist online, keep current behavior (update all) but output:
>
>   * number of callids with duplicates
>   * max duplicates for a callid
>   * list top 10 duplicate callids
>
> ---
>
> # Acceptance criteria
>
> * Local script supports: dry-run, live (`--live`), and rollback (`--rollback`).
> * Online script supports: dry-run, live (`--live`), and rollback.
> * Both produce output artifacts and a final audit summary.
> * All timezone conversions remain forced to America/New_York.
> * Local WHERE remains `LIKE '26-%'` with numeric range enforcement in code.
>
> Please output all three v4 scripts in full.

---

