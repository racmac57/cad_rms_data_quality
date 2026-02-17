# 🕒 2026-02-16-22-05-00
# cad_rms_data_quality/fix_gap_calldate_local.py
# Author: R. A. Carucci
# Purpose: Fix calldate in CFStable_GeocodeAddresses (local baseline) using
#          real dates from gap_for_append_v2. v4: rollback support, --live
#          guardrail, output artifacts, audit assertions, sample validation.

"""
=============================================================================
FIX GAP CALLDATE — LOCAL BASELINE (v4)
=============================================================================

MODES:
  propy.bat fix_gap_calldate_local.py                          # dry run
  propy.bat fix_gap_calldate_local.py --live                   # apply
  propy.bat fix_gap_calldate_local.py --rollback [snapshot]    # undo
  propy.bat fix_gap_calldate_local.py --expected-updates 2680  # audit
  propy.bat fix_gap_calldate_local.py --sample-callids 26-011297,26-011300

All patches retained: forced America/New_York, LIKE WHERE, numeric range,
out-of-range dispatch -> NULL.
=============================================================================
"""

import arcpy
import os
import sys
import csv
import json
import argparse
from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

# =============================================================================
# TIMEZONE
# =============================================================================

LOCAL_TZ_NAME = "America/New_York"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME) if ZoneInfo else datetime.now().astimezone().tzinfo
UTC_TZ = timezone.utc


def as_local(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(LOCAL_TZ)


# =============================================================================
# CONFIG
# =============================================================================

GDB = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb"
GAP_TABLE = os.path.join(GDB, "gap_for_append_v2")
BASELINE_TABLE = os.path.join(GDB, "CFStable_GeocodeAddresses")

BASE_OUT_DIR = r"C:\HPD ESRI\04_Scripts\_out"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

GAP_CALLID_MIN = "26-011288"
GAP_CALLID_MAX = "26-014999"

DOW_NAMES = {
    0: ("Monday", 2), 1: ("Tuesday", 3), 2: ("Wednesday", 4),
    3: ("Thursday", 5), 4: ("Friday", 6), 5: ("Saturday", 7),
    6: ("Sunday", 1),
}

# Fields we write (for schema preflight + snapshot)
WRITE_FIELD_NAMES = [
    "calldate", "calldow", "calldownum", "callhour",
    "callmonth", "callyear", "dispatchtime", "responsetime"
]

# =============================================================================
# OUTPUT DIR
# =============================================================================

RUN_OUT_DIR = os.path.join(BASE_OUT_DIR, f"local_fix_{TIMESTAMP}")
os.makedirs(RUN_OUT_DIR, exist_ok=True)

LOG_FILE = os.path.join(RUN_OUT_DIR, "fix.log")
SNAPSHOT_FILE = os.path.join(RUN_OUT_DIR, "snapshot.json")
CHANGES_FILE = os.path.join(RUN_OUT_DIR, "changes.json")
SUMMARY_FILE = os.path.join(RUN_OUT_DIR, "summary.json")
SAMPLE_CSV = os.path.join(RUN_OUT_DIR, "sample_before_after.csv")

# =============================================================================
# LOGGING
# =============================================================================

_log_fh = None


def log(msg):
    global _log_fh
    if _log_fh is None:
        _log_fh = open(LOG_FILE, "w", encoding="utf-8")
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line)
    _log_fh.write(line + "\n")
    _log_fh.flush()


# =============================================================================
# HELPERS
# =============================================================================

def callid_in_gap_range(callid):
    if not callid or not callid.startswith("26-"):
        return False
    try:
        num = int(callid.split("-", 1)[1].lstrip("0") or "0")
        lo = int(GAP_CALLID_MIN.split("-", 1)[1].lstrip("0") or "0")
        hi = int(GAP_CALLID_MAX.split("-", 1)[1].lstrip("0") or "0")
        return lo <= num <= hi
    except (ValueError, IndexError):
        return False


def dates_match(dt1, dt2, tol=1.0):
    if dt1 is None and dt2 is None:
        return True
    if dt1 is None or dt2 is None:
        return False
    d1 = dt1.replace(tzinfo=None) if dt1.tzinfo else dt1
    d2 = dt2.replace(tzinfo=None) if dt2.tzinfo else dt2
    return abs((d1 - d2).total_seconds()) < tol


def resolve_fields(table):
    """Return dict {lowercase_name: actual_name} for all fields."""
    return {f.name.lower(): f.name for f in arcpy.ListFields(table)}


def schema_preflight_local(avail):
    """Check required fields exist. Returns True or aborts."""
    required = ["callid", "calldate"]
    missing = [r for r in required if r not in avail]
    if missing:
        log(f"  SCHEMA FAIL: missing required fields: {missing}")
        log(f"  Available: {sorted(avail.keys())}")
        return False
    return True


# =============================================================================
# BUILD LOOKUP
# =============================================================================

def build_lookup():
    log("=" * 60)
    log("STEP 1: Building lookup from gap_for_append_v2")
    log("=" * 60)

    if not arcpy.Exists(GAP_TABLE):
        log(f"  ERROR: {GAP_TABLE} not found")
        sys.exit(1)

    fields = [f.name for f in arcpy.ListFields(GAP_TABLE)]
    log(f"  Fields: {fields}")

    cid_f, time_f = None, None
    for f in fields:
        fl = f.lower()
        if "reportnumber" in fl or "callid" in fl:
            cid_f = f
        if "time_of_call" in fl or "time of call" in fl:
            time_f = f
    if cid_f is None:
        for f in fields:
            if f.startswith("USER_") and "report" in f.lower():
                cid_f = f
    if time_f is None:
        for f in fields:
            if f.startswith("USER_") and "time" in f.lower() and "call" in f.lower():
                time_f = f

    if not cid_f or not time_f:
        log(f"  ERROR: Cannot identify fields. cid={cid_f}, time={time_f}")
        sys.exit(1)

    log(f"  Call ID field: {cid_f}")
    log(f"  Time field:    {time_f}")
    log(f"  Range:         {GAP_CALLID_MIN} to {GAP_CALLID_MAX}")

    lookup = {}
    with arcpy.da.SearchCursor(GAP_TABLE, [cid_f, time_f]) as cur:
        for row in cur:
            cid = str(row[0]).strip() if row[0] else None
            tval = row[1]
            if not cid or not callid_in_gap_range(cid) or tval is None:
                continue
            if isinstance(tval, datetime):
                lookup[cid] = tval
            elif isinstance(tval, str):
                for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S",
                            "%Y-%m-%d %H:%M:%S.%f"):
                    try:
                        lookup[cid] = datetime.strptime(tval, fmt)
                        break
                    except ValueError:
                        continue

    log(f"  Lookup: {len(lookup)} Call IDs")
    for sid in list(lookup.keys())[:3]:
        log(f"  Sample: {sid} -> {lookup[sid]}")

    return lookup


# =============================================================================
# FIX BASELINE
# =============================================================================

def fix_baseline(lookup, live, sample_callids):
    log("")
    log("=" * 60)
    log("STEP 2: Scanning CFStable_GeocodeAddresses")
    log("=" * 60)

    if not arcpy.Exists(BASELINE_TABLE):
        log(f"  ERROR: {BASELINE_TABLE} not found")
        sys.exit(1)

    avail = resolve_fields(BASELINE_TABLE)
    if not schema_preflight_local(avail):
        sys.exit(1)

    total_records = int(arcpy.management.GetCount(BASELINE_TABLE)[0])
    log(f"  Total records: {total_records:,}")

    # Resolve actual field names
    fn = {k: avail.get(k) for k in [
        "callid", "calldate", "dispatchdate", "queuetime",
        "calldow", "calldownum", "callhour", "callmonth", "callyear",
        "dispatchtime", "responsetime"
    ]}

    # Build cursor field list
    read_fields = [fn["callid"], fn["calldate"]]
    ri = {"callid": 0, "calldate": 1}  # read indices

    for key in ("dispatchdate", "queuetime"):
        if fn[key]:
            read_fields.append(fn[key])
            ri[key] = len(read_fields) - 1

    update_fields = list(read_fields)
    wi = {}  # write indices
    for key in WRITE_FIELD_NAMES:
        if key in ("calldate",):
            wi[key] = ri["calldate"]
            continue
        actual = fn.get(key)
        if actual and actual not in update_fields:
            update_fields.append(actual)
        if actual:
            wi[key] = update_fields.index(actual)

    log(f"  Cursor fields: {update_fields}")

    # Snapshot + changes accumulators
    snapshot_records = []
    changes = []
    sample_rows = []  # for sample CSV

    counters = {
        "scanned": 0, "updated": 0, "already_correct": 0,
        "no_match": 0, "out_of_range_dispatch": 0
    }

    where = f"{fn['callid']} LIKE '26-%'"
    log(f"  WHERE: {where}")

    try:
        with arcpy.da.UpdateCursor(BASELINE_TABLE, update_fields,
                                    where_clause=where) as cur:
            for row in cur:
                counters["scanned"] += 1
                row = list(row)
                cid = str(row[ri["callid"]]).strip() if row[ri["callid"]] else None

                if not cid or not callid_in_gap_range(cid) or cid not in lookup:
                    counters["no_match"] += 1
                    continue

                real_dt = lookup[cid]
                current_dt = row[ri["calldate"]]

                if dates_match(current_dt, real_dt):
                    counters["already_correct"] += 1
                    continue

                # Capture BEFORE state for snapshot (keyed by OBJECTID not available
                # in this cursor, so we key by callid + field values)
                before = {"callid": cid}
                for key in WRITE_FIELD_NAMES:
                    if key in wi:
                        before[key] = str(row[wi[key]]) if row[wi[key]] is not None else None

                # We need OBJECTID for rollback — add it to cursor
                # Actually we can't add fields mid-cursor. Use a separate approach:
                # Store callid + all before values; rollback will match by callid.
                # (OBJECTID approach would require a separate cursor pass)

                # Update calldate
                row[ri["calldate"]] = real_dt

                # Derived fields in NY time
                real_local = as_local(real_dt)
                dow_name, dow_num = DOW_NAMES.get(
                    real_local.weekday(), ("Unknown", 0)
                )

                after = {"callid": cid}

                if "calldow" in wi:
                    row[wi["calldow"]] = dow_name
                if "calldownum" in wi:
                    row[wi["calldownum"]] = dow_num
                if "callhour" in wi:
                    row[wi["callhour"]] = real_local.hour
                if "callmonth" in wi:
                    row[wi["callmonth"]] = real_local.month
                if "callyear" in wi:
                    row[wi["callyear"]] = real_local.year

                # Dispatchtime via UTC delta
                if "dispatchdate" in ri and "dispatchtime" in wi:
                    dd = row[ri["dispatchdate"]]
                    if dd is not None and isinstance(dd, datetime):
                        dd_utc = as_local(dd).astimezone(UTC_TZ)
                        cd_utc = real_local.astimezone(UTC_TZ)
                        diff_min = (dd_utc - cd_utc).total_seconds() / 60.0

                        if 0 <= diff_min <= 1440:
                            row[wi["dispatchtime"]] = round(diff_min, 4)
                            if "queuetime" in ri and "responsetime" in wi:
                                qt = row[ri["queuetime"]]
                                if qt is not None:
                                    try:
                                        row[wi["responsetime"]] = round(
                                            diff_min + float(qt), 4)
                                    except (ValueError, TypeError):
                                        row[wi["responsetime"]] = None
                                else:
                                    row[wi["responsetime"]] = None
                        else:
                            counters["out_of_range_dispatch"] += 1
                            row[wi["dispatchtime"]] = None
                            if "responsetime" in wi:
                                row[wi["responsetime"]] = None
                    else:
                        row[wi["dispatchtime"]] = None
                        if "responsetime" in wi:
                            row[wi["responsetime"]] = None

                # Capture AFTER state
                for key in WRITE_FIELD_NAMES:
                    if key in wi:
                        after[key] = str(row[wi[key]]) if row[wi[key]] is not None else None

                snapshot_records.append(before)
                changes.append({"before": before, "after": after})

                # Sample CSV row
                if sample_callids and cid in sample_callids:
                    sample_rows.append({
                        "callid": cid,
                        "before_calldate": str(current_dt),
                        "after_calldate": str(real_dt),
                        "after_dow": dow_name,
                        "after_hour": real_local.hour,
                    })

                if live:
                    cur.updateRow(row)

                counters["updated"] += 1

                if counters["updated"] <= 5:
                    log(f"  {'[DRY] ' if not live else ''}UPDATE: {cid}  "
                        f"{current_dt} -> {real_dt}  "
                        f"DOW={dow_name}, Hour={real_local.hour}")

    except Exception as e:
        log(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    log(f"")
    log(f"  Scanned:          {counters['scanned']}")
    log(f"  Updated:          {counters['updated']}")
    log(f"  Already correct:  {counters['already_correct']}")
    log(f"  No match:         {counters['no_match']}")
    log(f"  OOR dispatch:     {counters['out_of_range_dispatch']}")

    # Write snapshot
    snapshot = {
        "created": TIMESTAMP,
        "script_version": "v4",
        "timezone": LOCAL_TZ_NAME,
        "table": BASELINE_TABLE,
        "mode": "live" if live else "dry_run",
        "record_count": len(snapshot_records),
        "records": snapshot_records,
    }
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, default=str)
    log(f"  Snapshot: {SNAPSHOT_FILE}")

    # Write changes
    with open(CHANGES_FILE, "w", encoding="utf-8") as fh:
        json.dump(changes, fh, indent=2, default=str)
    log(f"  Changes: {CHANGES_FILE}")

    # Write sample CSV
    if sample_rows:
        with open(SAMPLE_CSV, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=sample_rows[0].keys())
            writer.writeheader()
            writer.writerows(sample_rows)
        log(f"  Sample CSV: {SAMPLE_CSV}")

    return counters


# =============================================================================
# VERIFY
# =============================================================================

def verify(lookup, live, sample_callids):
    log("")
    log("=" * 60)
    log("STEP 3: Verification")
    log("=" * 60)

    if not live:
        log("  Skipping (dry run)")
        return

    avail = resolve_fields(BASELINE_TABLE)
    cid_name = avail.get("callid")
    cd_name = avail.get("calldate")

    ids_to_check = list(lookup.keys())[:10]
    if sample_callids:
        ids_to_check = list(set(ids_to_check + list(sample_callids)))

    where = "{} IN ({})".format(cid_name, ",".join(f"'{c}'" for c in ids_to_check))

    all_ok = True
    with arcpy.da.SearchCursor(BASELINE_TABLE, [cid_name, cd_name],
                                where_clause=where) as cur:
        for row in cur:
            cid = str(row[0]).strip()
            actual = row[1]
            expected = lookup.get(cid)
            if expected and not dates_match(actual, expected):
                log(f"  MISMATCH: {cid} = {actual}, expected {expected}")
                all_ok = False
            elif cid in (sample_callids or []):
                log(f"  SAMPLE OK: {cid} = {actual}")
            else:
                log(f"  OK: {cid} = {actual}")

    log("  All verified!" if all_ok else "  MISMATCHES found")


# =============================================================================
# ROLLBACK
# =============================================================================

def do_rollback(snapshot_path):
    log("=" * 60)
    log("ROLLBACK MODE")
    log("=" * 60)

    if snapshot_path is None:
        # Find most recent
        candidates = []
        for d in sorted(os.listdir(BASE_OUT_DIR), reverse=True):
            sp = os.path.join(BASE_OUT_DIR, d, "snapshot.json")
            if d.startswith("local_fix_") and os.path.exists(sp):
                candidates.append(sp)
        if not candidates:
            log("  No snapshots found")
            sys.exit(1)
        snapshot_path = candidates[0]

    if not os.path.exists(snapshot_path):
        log(f"  Snapshot not found: {snapshot_path}")
        sys.exit(1)

    with open(snapshot_path, "r", encoding="utf-8") as fh:
        snapshot = json.load(fh)

    log(f"  Snapshot: {snapshot.get('created')} v{snapshot.get('script_version')}")
    log(f"  Table: {snapshot.get('table')}")
    log(f"  Records: {snapshot.get('record_count')}")

    if snapshot.get("mode") == "dry_run":
        log("  WARNING: This snapshot was from a DRY RUN (no changes were made)")
        log("  Nothing to rollback.")
        return

    table = snapshot.get("table", BASELINE_TABLE)
    if not arcpy.Exists(table):
        log(f"  ERROR: {table} not found")
        sys.exit(1)

    avail = resolve_fields(table)
    cid_name = avail.get("callid")

    restored = 0
    failed = 0

    for rec in snapshot["records"]:
        cid = rec.get("callid")
        if not cid:
            continue

        # Build field list + values from snapshot
        field_vals = {}
        for key in WRITE_FIELD_NAMES:
            if key in rec and rec[key] is not None:
                actual_name = avail.get(key)
                if actual_name:
                    field_vals[actual_name] = rec[key]

        if not field_vals:
            continue

        # Parse calldate back to datetime if it's a string
        cd_actual = avail.get("calldate")
        if cd_actual and cd_actual in field_vals:
            val = field_vals[cd_actual]
            if isinstance(val, str) and val != "None":
                try:
                    field_vals[cd_actual] = datetime.strptime(
                        val.split(".")[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass

        # Parse numeric fields
        for nf in ("calldownum", "callhour", "callmonth", "callyear"):
            an = avail.get(nf)
            if an and an in field_vals:
                try:
                    field_vals[an] = int(float(field_vals[an]))
                except (ValueError, TypeError):
                    pass

        for nf in ("dispatchtime", "responsetime"):
            an = avail.get(nf)
            if an and an in field_vals:
                try:
                    field_vals[an] = float(field_vals[an])
                except (ValueError, TypeError):
                    field_vals[an] = None

        # Update via cursor
        update_flds = [cid_name] + list(field_vals.keys())
        where = f"{cid_name} = '{cid}'"
        try:
            with arcpy.da.UpdateCursor(table, update_flds,
                                        where_clause=where) as cur:
                for row in cur:
                    row = list(row)
                    for i, fn_key in enumerate(field_vals.keys()):
                        row[i + 1] = field_vals[fn_key]
                    cur.updateRow(row)
                    restored += 1
                    break
        except Exception as e:
            log(f"  ERROR restoring {cid}: {e}")
            failed += 1

    log(f"  Restored: {restored}")
    log(f"  Failed:   {failed}")

    # Write rollback report
    report = {
        "timestamp": TIMESTAMP,
        "snapshot_used": snapshot_path,
        "restored": restored,
        "failed": failed,
    }
    report_path = os.path.join(RUN_OUT_DIR, "rollback_report.json")
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    log(f"  Report: {report_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fix gap calldate in local baseline (v4)")
    parser.add_argument("--live", action="store_true",
                        help="Apply changes (required to write)")
    parser.add_argument("--rollback", nargs="?", const="AUTO", default=None,
                        help="Rollback from snapshot (optionally specify path)")
    parser.add_argument("--expected-updates", type=int, default=None,
                        help="Expected update count for audit assertion")
    parser.add_argument("--max-miss-rate", type=float, default=2.0,
                        help="Max allowed %% deviation from expected (default 2)")
    parser.add_argument("--sample-callids", type=str, default=None,
                        help="Comma-separated Call IDs for detailed before/after")
    args = parser.parse_args()

    sample_set = None
    if args.sample_callids:
        sample_set = set(c.strip() for c in args.sample_callids.split(","))

    # Rollback mode
    if args.rollback is not None:
        path = None if args.rollback == "AUTO" else args.rollback
        do_rollback(path)
        return

    live = args.live

    log("=" * 60)
    log(f"  FIX GAP CALLDATE — LOCAL BASELINE (v4)")
    log(f"  Mode:     {'LIVE' if live else 'DRY RUN'}")
    log(f"  Timezone: {LOCAL_TZ_NAME}")
    log(f"  Range:    {GAP_CALLID_MIN} to {GAP_CALLID_MAX}")
    log(f"  Output:   {RUN_OUT_DIR}")
    log("=" * 60)

    start = datetime.now()

    lookup = build_lookup()
    if not lookup:
        log("  Empty lookup. Nothing to do.")
        return

    counters = fix_baseline(lookup, live, sample_set)
    verify(lookup, live, sample_set)

    elapsed = (datetime.now() - start).total_seconds()

    # Audit assertions
    log("")
    log("=" * 60)
    log("AUDIT")
    log("=" * 60)

    log(f"  Lookup size:      {len(lookup)}")
    log(f"  Scanned:          {counters['scanned']}")
    log(f"  Matched:          {counters['updated'] + counters['already_correct']}")
    log(f"  Already correct:  {counters['already_correct']}")
    log(f"  Updates prepared: {counters['updated']}")

    exit_code = 0

    if args.expected_updates is not None:
        exp = args.expected_updates
        actual = counters["updated"]
        max_miss = exp * (args.max_miss_rate / 100.0)
        diff = abs(actual - exp)
        if diff > max_miss:
            log(f"  AUDIT FAIL: expected ~{exp} updates, got {actual} "
                f"(diff {diff} > {max_miss:.0f} allowed)")
            exit_code = 1
        else:
            log(f"  AUDIT PASS: {actual} updates vs {exp} expected "
                f"(within {args.max_miss_rate}%)")
    else:
        if counters["updated"] > 0 and \
                abs(counters["updated"] - len(lookup)) > len(lookup) * 0.1:
            log(f"  NOTE: {counters['updated']} updates vs {len(lookup)} "
                f"lookup entries — >10% difference, review")

    # Write summary
    summary = {
        "timestamp": TIMESTAMP,
        "script_version": "v4",
        "mode": "live" if live else "dry_run",
        "timezone": LOCAL_TZ_NAME,
        "gap_range": f"{GAP_CALLID_MIN} to {GAP_CALLID_MAX}",
        "lookup_size": len(lookup),
        "counters": counters,
        "duration_sec": round(elapsed, 1),
        "expected_updates": args.expected_updates,
        "audit_pass": exit_code == 0,
        "output_dir": RUN_OUT_DIR,
    }
    with open(SUMMARY_FILE, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)

    log(f"  Duration: {elapsed:.1f}s")
    log(f"  Output:   {RUN_OUT_DIR}")

    if not live:
        log("")
        log("  >>> DRY RUN complete. Re-run with --live to apply. <<<")
    else:
        log("")
        log("  >>> Local baseline fixed. Run fix_gap_calldate_online.py next. <<<")

    if _log_fh:
        _log_fh.close()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
