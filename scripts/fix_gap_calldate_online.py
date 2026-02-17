# 🕒 2026-02-16-22-15-00
# cad_rms_data_quality/fix_gap_calldate_online.py
# Author: R. A. Carucci
# Purpose: Surgical update of gap record calldates on ArcGIS Online
#          CallsForService layer using real dates from gap_for_append_v2.
#          v4: --live guardrail, output artifacts, audit assertions,
#          sample-callids post-update re-query, enhanced duplicate reporting.
#          All timezone conversions forced to America/New_York.

"""
=============================================================================
FIX GAP CALLDATE — SURGICAL ONLINE UPDATE (v4)
=============================================================================

MODES:
  propy.bat fix_gap_calldate_online.py                          # dry run
  propy.bat fix_gap_calldate_online.py --live                   # apply
  propy.bat fix_gap_calldate_online.py --rollback [snapshot]    # undo
  propy.bat fix_gap_calldate_online.py --expected-updates 2680
  propy.bat fix_gap_calldate_online.py --sample-callids 26-011297,26-011300

All patches retained: forced America/New_York, min/max enforcement,
schema preflight, duplicate detection, out-of-range dispatch -> NULL.
=============================================================================
"""

import arcpy
import os
import sys
import csv
import json
import logging
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
    """Treat naive datetimes as NY; normalize aware datetimes to NY."""
    if dt is None:
        return None
    if not isinstance(dt, datetime):
        raise TypeError(f"Expected datetime, got {type(dt).__name__}")
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(LOCAL_TZ)


def datetime_to_epoch_ms(dt):
    """datetime -> UTC epoch ms for AGOL. Naive assumed NY."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return int(as_local(dt).astimezone(UTC_TZ).timestamp() * 1000)
    try:
        return int(float(dt) * 1000) if dt else None
    except (ValueError, TypeError):
        return None


def epoch_ms_to_datetime(epoch_ms, tz=None):
    """AGOL epoch ms (UTC) -> tz-aware datetime (default NY)."""
    if tz is None:
        tz = LOCAL_TZ
    if epoch_ms is None:
        return None
    try:
        return datetime.fromtimestamp(epoch_ms / 1000, tz=UTC_TZ).astimezone(tz)
    except (ValueError, TypeError, OSError):
        return None


# =============================================================================
# CONFIG
# =============================================================================

GDB = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb"
GAP_TABLE = os.path.join(GDB, "gap_for_append_v2")
ONLINE_SERVICE = (
    "https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/"
    "CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0"
)

BASE_OUT_DIR = r"C:\HPD ESRI\04_Scripts\_out"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BATCH_SIZE = 200

GAP_CALLID_PREFIX = "26-"
GAP_CALLID_MIN = "26-011288"
GAP_CALLID_MAX = "26-014999"

QUERY_FIELDS = [
    "OBJECTID", "callid", "calldate",
    "dispatchdate", "queuetime",
    "calldow", "calldownum", "callhour", "callmonth", "callyear",
    "dispatchtime", "responsetime"
]

WRITE_FIELDS = [
    "calldate", "calldow", "calldownum", "callhour", "callmonth",
    "callyear", "dispatchtime", "responsetime"
]

DOW_NAMES = {
    0: ("Monday", 2), 1: ("Tuesday", 3), 2: ("Wednesday", 4),
    3: ("Thursday", 5), 4: ("Friday", 6), 5: ("Saturday", 7),
    6: ("Sunday", 1),
}

# =============================================================================
# OUTPUT DIR
# =============================================================================

RUN_OUT_DIR = os.path.join(BASE_OUT_DIR, f"online_fix_{TIMESTAMP}")
os.makedirs(RUN_OUT_DIR, exist_ok=True)

LOG_FILE = os.path.join(RUN_OUT_DIR, "fix.log")
SNAPSHOT_FILE = os.path.join(RUN_OUT_DIR, "snapshot.json")
CHANGES_FILE = os.path.join(RUN_OUT_DIR, "changes.json")
SUMMARY_FILE = os.path.join(RUN_OUT_DIR, "summary.json")
SAMPLE_CSV = os.path.join(RUN_OUT_DIR, "sample_before_after.csv")

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)


# =============================================================================
# HELPERS
# =============================================================================

def callid_in_gap_range(callid):
    if not callid or not callid.startswith(GAP_CALLID_PREFIX):
        return False
    try:
        num = int(callid.split("-", 1)[1].lstrip("0") or "0")
        lo = int(GAP_CALLID_MIN.split("-", 1)[1].lstrip("0") or "0")
        hi = int(GAP_CALLID_MAX.split("-", 1)[1].lstrip("0") or "0")
        return lo <= num <= hi
    except (ValueError, IndexError):
        return False


def compute_derived_fields(calldate_dt, dispatchdate_epoch_ms, queuetime_val):
    """
    Derived fields in NY time. dispatchtime via UTC delta (DST-safe).
    Out-of-range -> None.
    """
    result = {}
    if calldate_dt is None:
        return result

    cd_local = as_local(calldate_dt)
    dow_name, dow_num = DOW_NAMES.get(cd_local.weekday(), ("Unknown", 0))
    result["calldow"] = dow_name
    result["calldownum"] = dow_num
    result["callhour"] = cd_local.hour
    result["callmonth"] = cd_local.month
    result["callyear"] = cd_local.year

    result["dispatchtime"] = None
    result["responsetime"] = None

    if dispatchdate_epoch_ms is None:
        return result

    try:
        dispatch_utc = datetime.fromtimestamp(
            dispatchdate_epoch_ms / 1000, tz=UTC_TZ)
        calldate_utc = cd_local.astimezone(UTC_TZ)
        diff_min = (dispatch_utc - calldate_utc).total_seconds() / 60.0
    except (ValueError, TypeError, OSError):
        return result

    if not (0 <= diff_min <= 1440):
        log.warning(f"  dispatchtime {diff_min:.1f} min out of range -> NULL")
        return result

    result["dispatchtime"] = round(diff_min, 4)
    if queuetime_val is not None:
        try:
            result["responsetime"] = round(diff_min + float(queuetime_val), 4)
        except (ValueError, TypeError):
            result["responsetime"] = None

    return result


# =============================================================================
# TIMEZONE VERIFICATION
# =============================================================================

def log_timezone_info():
    import time as _time

    log.info("-" * 50)
    log.info("TIMEZONE VERIFICATION")
    log.info("-" * 50)

    tz_name = _time.tzname
    utc_std = -(_time.timezone / 3600)
    utc_dst = -(_time.altzone / 3600) if _time.daylight else utc_std

    log.info(f"  System timezone:  {tz_name}")
    log.info(f"  UTC offset:       std={utc_std:+.0f}h  dst={utc_dst:+.0f}h")
    log.info(f"  Forced LOCAL_TZ:  {LOCAL_TZ_NAME}")

    probe_dt = datetime(2026, 2, 3, 10, 14, 14)
    sys_epoch = int(probe_dt.timestamp() * 1000)
    ny_epoch = datetime_to_epoch_ms(probe_dt)
    rt = epoch_ms_to_datetime(ny_epoch)

    log.info(f"  Probe:            {probe_dt}")
    log.info(f"  System epoch ms:  {sys_epoch}")
    log.info(f"  NY epoch ms:      {ny_epoch}")

    if sys_epoch != ny_epoch:
        delta = (sys_epoch - ny_epoch) / 1000.0
        log.warning(f"  System/NY mismatch: {delta:+.1f}s (forced-NY handles this)")
    else:
        log.info(f"  System/NY match:  YES")

    drift = abs((rt.replace(tzinfo=None) - probe_dt).total_seconds())
    log.info(f"  NY round-trip:    {rt}  drift={drift:.3f}s")

    if drift > 1.0:
        log.error(f"  DRIFT {drift:.1f}s — STOP")
        return False

    log.info("-" * 50)
    return True


# =============================================================================
# SCHEMA PREFLIGHT
# =============================================================================

def schema_preflight(fl):
    log.info("-" * 50)
    log.info("SCHEMA PREFLIGHT")
    log.info("-" * 50)

    try:
        layer_fields = {f["name"].lower(): f for f in fl.properties.fields}
    except Exception as e:
        log.error(f"  Cannot read schema: {e}")
        return False

    missing_r = [f for f in QUERY_FIELDS if f.lower() not in layer_fields]
    missing_w = [f for f in WRITE_FIELDS if f.lower() not in layer_fields]

    if missing_r:
        log.error(f"  MISSING READ FIELDS: {missing_r}")
        log.error(f"  Available: {sorted(layer_fields.keys())}")
        return False
    if missing_w:
        log.error(f"  MISSING WRITE FIELDS: {missing_w}")
        return False

    cd_type = layer_fields.get("calldate", {}).get("type", "?")
    if "Date" in cd_type or "esriFieldTypeDate" in cd_type:
        log.info(f"  calldate type: {cd_type} (OK)")
    else:
        log.warning(f"  calldate type: {cd_type} — expected Date")

    log.info(f"  All {len(QUERY_FIELDS)} read / {len(WRITE_FIELDS)} write fields present")
    log.info("-" * 50)
    return True


# =============================================================================
# STEP 1: BUILD LOOKUP
# =============================================================================

def build_lookup():
    log.info("=" * 70)
    log.info("STEP 1: Building lookup from gap_for_append_v2")
    log.info("=" * 70)

    if not arcpy.Exists(GAP_TABLE):
        log.error(f"  NOT FOUND: {GAP_TABLE}")
        sys.exit(1)

    fields = [f.name for f in arcpy.ListFields(GAP_TABLE)]
    log.info(f"  Fields: {fields}")

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
        log.error(f"  Cannot find fields. cid={cid_f}, time={time_f}")
        sys.exit(1)

    log.info(f"  Call ID field: {cid_f}")
    log.info(f"  Time field:    {time_f}")
    log.info(f"  Range:         {GAP_CALLID_MIN} to {GAP_CALLID_MAX}")

    lookup = {}
    null_ct = 0
    oor_ct = 0

    with arcpy.da.SearchCursor(GAP_TABLE, [cid_f, time_f]) as cur:
        for row in cur:
            cid = row[0]
            tval = row[1]
            if cid is None:
                null_ct += 1
                continue
            cid = str(cid).strip()
            if not callid_in_gap_range(cid):
                oor_ct += 1
                continue
            if tval is None:
                null_ct += 1
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

    log.info(f"  Lookup: {len(lookup)} Call IDs")
    if null_ct:
        log.warning(f"  Skipped NULL/unparseable: {null_ct}")
    if oor_ct:
        log.info(f"  Skipped out-of-range: {oor_ct}")
    for sid in list(lookup.keys())[:5]:
        log.info(f"  Sample: {sid} -> {lookup[sid]}")

    return lookup


# =============================================================================
# STEP 2: CONNECT + PREFLIGHT + QUERY
# =============================================================================

def query_online_gap_records(lookup):
    log.info("")
    log.info("=" * 70)
    log.info("STEP 2: Connecting to ArcGIS Online")
    log.info("=" * 70)

    from arcgis.gis import GIS
    from arcgis.features import FeatureLayer

    try:
        gis = GIS("pro")
        log.info(f"  Connected as: {gis.properties.user.username}")
    except Exception as e:
        log.error(f"  Connection failed: {e}")
        sys.exit(1)

    fl = FeatureLayer(ONLINE_SERVICE, gis=gis)

    if not schema_preflight(fl):
        log.error("  Schema preflight FAILED. Aborting.")
        sys.exit(1)

    total = fl.query(where="1=1", return_count_only=True)
    log.info(f"  Online layer total: {total:,}")

    log.info("  Querying gap records...")
    gap_ids = list(lookup.keys())
    all_features = []
    chunk_size = 50

    for i in range(0, len(gap_ids), chunk_size):
        chunk = gap_ids[i:i + chunk_size]
        where = "callid IN ({})".format(",".join(f"'{c}'" for c in chunk))
        try:
            result = fl.query(
                where=where,
                out_fields=",".join(QUERY_FIELDS),
                return_geometry=False
            )
            all_features.extend(result.features)
            log.info(
                f"  Chunk {i // chunk_size + 1}/"
                f"{(len(gap_ids) + chunk_size - 1) // chunk_size}: "
                f"{len(result.features)} features"
            )
        except Exception as e:
            log.error(f"  Query failed at index {i}: {e}")
            sys.exit(1)

    log.info(f"  Total gap features found: {len(all_features)}")

    if not all_features:
        log.error("  No matching gap records found online!")
        sys.exit(1)

    # Enhanced duplicate detection
    cid_counts = {}
    for f in all_features:
        c = f.attributes.get("callid", "")
        cid_counts[c] = cid_counts.get(c, 0) + 1

    dupes = {k: v for k, v in cid_counts.items() if v > 1}
    if dupes:
        max_dupe = max(dupes.values())
        log.warning(f"  DUPLICATES: {len(dupes)} Call IDs appear >1 time")
        log.warning(f"  Max duplicates for a single callid: {max_dupe}")
        log.warning(f"  Total extra records: {sum(v - 1 for v in dupes.values())}")
        log.warning(f"  Top 10 duplicate callids:")
        for cid, cnt in sorted(dupes.items(), key=lambda x: -x[1])[:10]:
            log.warning(f"    {cid}: {cnt} records")
        log.warning(f"  All duplicates will be updated (expected for multi-unit calls)")

    unique = len(cid_counts)
    if unique != len(lookup):
        log.warning(f"  COUNT: {len(lookup)} in lookup, {unique} unique online, "
                     f"{len(all_features)} total features")

    return fl, all_features, dupes


# =============================================================================
# STEP 3: SAVE SNAPSHOT
# =============================================================================

def save_snapshot(all_features, live):
    log.info("")
    log.info("=" * 70)
    log.info("STEP 3: Saving pre-update snapshot")
    log.info("=" * 70)

    snapshot = {
        "created": TIMESTAMP,
        "script_version": "v4",
        "timezone": LOCAL_TZ_NAME,
        "mode": "live" if live else "dry_run",
        "online_service": ONLINE_SERVICE,
        "gap_range": f"{GAP_CALLID_MIN} to {GAP_CALLID_MAX}",
        "record_count": len(all_features),
        "records": []
    }

    for f in all_features:
        a = f.attributes
        snapshot["records"].append({
            "OBJECTID": a.get("OBJECTID"),
            "callid": a.get("callid"),
            "calldate": a.get("calldate"),
            "dispatchdate": a.get("dispatchdate"),
            "queuetime": a.get("queuetime"),
            "calldow": a.get("calldow"),
            "calldownum": a.get("calldownum"),
            "callhour": a.get("callhour"),
            "callmonth": a.get("callmonth"),
            "callyear": a.get("callyear"),
            "dispatchtime": a.get("dispatchtime"),
            "responsetime": a.get("responsetime"),
        })

    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, default=str)

    log.info(f"  Saved: {SNAPSHOT_FILE}")
    log.info(f"  Records: {len(snapshot['records'])}")
    log.info(f"  *** KEEP THIS FILE — rollback data ***")

    return snapshot


# =============================================================================
# STEP 4: BUILD UPDATES
# =============================================================================

def build_updates(all_features, lookup, sample_callids):
    log.info("")
    log.info("=" * 70)
    log.info("STEP 4: Building update payloads")
    log.info("=" * 70)

    updates = []
    changes = []
    sample_rows = []
    counters = {
        "no_match": 0, "already_correct": 0,
        "out_of_range_dispatch": 0
    }

    for f in all_features:
        attrs = f.attributes
        oid = attrs["OBJECTID"]
        callid = attrs.get("callid", "")

        if callid not in lookup:
            counters["no_match"] += 1
            continue

        real_dt = lookup[callid]
        real_epoch = datetime_to_epoch_ms(real_dt)
        cur_epoch = attrs.get("calldate")

        # Skip if already correct
        if cur_epoch is not None and real_epoch is not None:
            if abs(cur_epoch - real_epoch) / 1000 < 1.0:
                counters["already_correct"] += 1
                continue

        # Before state
        before = {k: attrs.get(k) for k in
                  ["OBJECTID", "callid"] + WRITE_FIELDS}

        # Build update
        update_attrs = {"OBJECTID": oid, "calldate": real_epoch}
        derived = compute_derived_fields(
            real_dt, attrs.get("dispatchdate"), attrs.get("queuetime"))
        if derived.get("dispatchtime") is None and attrs.get("dispatchdate"):
            counters["out_of_range_dispatch"] += 1
        update_attrs.update(derived)
        updates.append({"attributes": update_attrs})

        # After state
        after = dict(update_attrs)
        changes.append({"before": before, "after": after})

        # Sample tracking
        if sample_callids and callid in sample_callids:
            cur_ny = epoch_ms_to_datetime(cur_epoch)
            real_local = as_local(real_dt)
            sample_rows.append({
                "callid": callid,
                "OBJECTID": oid,
                "before_calldate_epoch": cur_epoch,
                "before_calldate_ny": str(cur_ny),
                "after_calldate_epoch": real_epoch,
                "after_calldate_ny": str(real_local),
                "after_dow": derived.get("calldow", ""),
                "after_hour": derived.get("callhour", ""),
                "after_dispatchtime": derived.get("dispatchtime", ""),
                "after_responsetime": derived.get("responsetime", ""),
            })

        # Log first few
        if len(updates) <= 5:
            cur_display = epoch_ms_to_datetime(cur_epoch)
            real_local = as_local(real_dt)
            log.info(
                f"  {callid} (OID {oid}): {cur_display} -> {real_local}  "
                f"DOW={derived.get('calldow', '?')}, "
                f"Hr={derived.get('callhour', '?')}, "
                f"disp={derived.get('dispatchtime', 'NULL')} min"
            )

    log.info(f"  Updates to apply: {len(updates)}")
    log.info(f"  Already correct:  {counters['already_correct']}")
    if counters["no_match"]:
        log.warning(f"  No lookup match:  {counters['no_match']}")
    if counters["out_of_range_dispatch"]:
        log.info(f"  OOR dispatch->NULL: {counters['out_of_range_dispatch']}")

    # Write changes artifact
    with open(CHANGES_FILE, "w", encoding="utf-8") as fh:
        json.dump(changes, fh, indent=2, default=str)
    log.info(f"  Changes file: {CHANGES_FILE}")

    # Write sample CSV
    if sample_rows:
        with open(SAMPLE_CSV, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=sample_rows[0].keys())
            writer.writeheader()
            writer.writerows(sample_rows)
        log.info(f"  Sample CSV: {SAMPLE_CSV}")

    return updates, counters


# =============================================================================
# STEP 5: APPLY UPDATES
# =============================================================================

def apply_updates(fl, updates, live):
    log.info("")
    log.info("=" * 70)
    if not live:
        log.info("STEP 5: DRY RUN — no changes will be made")
        log.info("=" * 70)
        num_b = (len(updates) + BATCH_SIZE - 1) // BATCH_SIZE
        log.info(f"  Would update {len(updates)} records in {num_b} batches")
        log.info(f"  Re-run with --live to apply.")
        return {"succeeded": 0, "failed": 0, "attempted": 0}
    else:
        log.info("STEP 5: APPLYING UPDATES TO AGOL (LIVE)")
        log.info("=" * 70)

    total_ok = 0
    total_fail = 0
    failed_oids = []
    num_b = (len(updates) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(updates), BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = updates[i:i + BATCH_SIZE]

        try:
            result = fl.edit_features(updates=batch)
            ur = result.get("updateResults", [])
            b_ok = sum(1 for r in ur if r.get("success"))
            b_fail = sum(1 for r in ur if not r.get("success"))
            total_ok += b_ok
            total_fail += b_fail

            if b_fail:
                for r in ur:
                    if not r.get("success"):
                        failed_oids.append(r.get("objectId"))
                        log.error(
                            f"  Failed OID {r.get('objectId')}: "
                            f"{r.get('error', {}).get('description', '?')}")

            log.info(
                f"  Batch {batch_num}/{num_b}: {b_ok} OK, {b_fail} fail "
                f"(running: {total_ok}/{len(updates)})")

        except Exception as e:
            log.error(f"  Batch {batch_num} EXCEPTION: {e}")
            total_fail += len(batch)
            failed_oids.extend(u["attributes"]["OBJECTID"] for u in batch)
            log.warning("  Continuing with next batch...")

    log.info(f"  RESULTS: {total_ok} OK, {total_fail} failed / {len(updates)} total")
    if failed_oids:
        log.error(f"  Failed OIDs: {failed_oids[:20]}")

    return {
        "succeeded": total_ok,
        "failed": total_fail,
        "attempted": len(updates),
        "failed_oids": failed_oids[:50],
    }


# =============================================================================
# STEP 6: VERIFY + SAMPLE RE-QUERY
# =============================================================================

def verify_updates(fl, lookup, live, sample_callids):
    log.info("")
    log.info("=" * 70)
    log.info("STEP 6: Post-update verification")
    log.info("=" * 70)

    if not live:
        log.info("  Skipping (dry run)")
        return

    # Build list of IDs to check: first 10 + any sample callids
    ids = list(lookup.keys())[:10]
    if sample_callids:
        ids = list(set(ids) | sample_callids)

    where = "callid IN ({})".format(",".join(f"'{c}'" for c in ids))

    try:
        result = fl.query(
            where=where,
            out_fields="OBJECTID,callid,calldate,calldow,calldownum,"
                       "callhour,callmonth,callyear,dispatchtime,responsetime",
            return_geometry=False
        )
    except Exception as e:
        log.error(f"  Verification query failed: {e}")
        return

    all_ok = True
    for f in result.features:
        a = f.attributes
        cid = a.get("callid", "")
        online_epoch = a.get("calldate")
        expected_dt = lookup.get(cid)
        if not expected_dt:
            continue

        expected_epoch = datetime_to_epoch_ms(expected_dt)
        online_ny = epoch_ms_to_datetime(online_epoch)
        expected_ny = as_local(expected_dt)

        if online_epoch is not None and expected_epoch is not None:
            diff = abs(online_epoch - expected_epoch) / 1000
            status = "OK" if diff < 1.0 else "MISMATCH"
            if status == "MISMATCH":
                all_ok = False
        else:
            status = "NULL"
            all_ok = False

        is_sample = sample_callids and cid in sample_callids
        prefix = "  SAMPLE" if is_sample else "  "

        log.info(
            f"{prefix} {cid} [{status}]: "
            f"online={online_ny}, expected={expected_ny}  "
            f"dow={a.get('calldow')}, hr={a.get('callhour')}, "
            f"yr={a.get('callyear')}, disp={a.get('dispatchtime')}, "
            f"resp={a.get('responsetime')}"
        )

    log.info("  All verified!" if all_ok else "  MISMATCHES found — review log")


# =============================================================================
# ROLLBACK
# =============================================================================

def do_rollback(snapshot_path):
    log.info("=" * 70)
    log.info("ROLLBACK MODE")
    log.info("=" * 70)

    if snapshot_path is None:
        # Find most recent
        candidates = []
        for d in sorted(os.listdir(BASE_OUT_DIR), reverse=True):
            sp = os.path.join(BASE_OUT_DIR, d, "snapshot.json")
            if d.startswith("online_fix_") and os.path.exists(sp):
                candidates.append(sp)
        if not candidates:
            log.error("  No online snapshots found")
            sys.exit(1)
        snapshot_path = candidates[0]

    if not os.path.exists(snapshot_path):
        log.error(f"  Snapshot not found: {snapshot_path}")
        sys.exit(1)

    with open(snapshot_path, "r", encoding="utf-8") as fh:
        snapshot = json.load(fh)

    log.info(f"  Snapshot: {snapshot.get('created')} "
             f"v{snapshot.get('script_version')}")
    log.info(f"  Records: {snapshot.get('record_count')}")

    if snapshot.get("mode") == "dry_run":
        log.warning("  Snapshot was from DRY RUN — no changes to revert")
        return

    from arcgis.gis import GIS
    from arcgis.features import FeatureLayer

    gis = GIS("pro")
    fl = FeatureLayer(ONLINE_SERVICE, gis=gis)

    updates = []
    for rec in snapshot["records"]:
        updates.append({"attributes": {
            "OBJECTID": rec["OBJECTID"],
            "calldate": rec["calldate"],
            "calldow": rec["calldow"],
            "calldownum": rec["calldownum"],
            "callhour": rec["callhour"],
            "callmonth": rec["callmonth"],
            "callyear": rec["callyear"],
            "dispatchtime": rec["dispatchtime"],
            "responsetime": rec["responsetime"],
        }})

    log.info(f"  Pushing {len(updates)} rollback updates...")

    total_ok = 0
    total_fail = 0
    for i in range(0, len(updates), BATCH_SIZE):
        batch = updates[i:i + BATCH_SIZE]
        try:
            result = fl.edit_features(updates=batch)
            b_ok = sum(1 for r in result.get("updateResults", [])
                       if r.get("success"))
            b_fail = len(batch) - b_ok
            total_ok += b_ok
            total_fail += b_fail
            log.info(f"  Batch {i // BATCH_SIZE + 1}: {b_ok} restored, "
                     f"{b_fail} failed")
        except Exception as e:
            log.error(f"  Batch {i // BATCH_SIZE + 1} EXCEPTION: {e}")
            total_fail += len(batch)

    log.info(f"  ROLLBACK COMPLETE: {total_ok} restored, {total_fail} failed "
             f"/ {len(updates)} total")

    # Rollback report
    report = {
        "timestamp": TIMESTAMP,
        "snapshot_used": snapshot_path,
        "restored": total_ok,
        "failed": total_fail,
    }
    report_path = os.path.join(RUN_OUT_DIR, "rollback_report.json")
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    log.info(f"  Report: {report_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fix gap calldate on AGOL (v4)")
    parser.add_argument("--live", action="store_true",
                        help="Apply changes (required to write)")
    parser.add_argument("--rollback", nargs="?", const="AUTO", default=None,
                        help="Rollback from snapshot (optionally specify path)")
    parser.add_argument("--expected-updates", type=int, default=None,
                        help="Expected update count for audit assertion")
    parser.add_argument("--max-miss-rate", type=float, default=2.0,
                        help="Max allowed %% deviation from expected (default 2)")
    parser.add_argument("--sample-callids", type=str, default=None,
                        help="Comma-separated Call IDs for detailed tracking")
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

    log.info("=" * 70)
    log.info("  FIX GAP CALLDATE — ONLINE (v4)")
    log.info(f"  Mode:     {'LIVE' if live else 'DRY RUN'}")
    log.info(f"  Timezone: {LOCAL_TZ_NAME}")
    log.info(f"  Range:    {GAP_CALLID_MIN} to {GAP_CALLID_MAX}")
    log.info(f"  Output:   {RUN_OUT_DIR}")
    log.info("=" * 70)

    start = datetime.now()

    # Timezone check
    if not log_timezone_info():
        log.error("  Timezone check FAILED.")
        sys.exit(1)

    # Step 1
    lookup = build_lookup()
    if not lookup:
        log.error("  Empty lookup. Aborting.")
        sys.exit(1)

    # Step 2
    fl, all_features, dupes = query_online_gap_records(lookup)

    # Step 3
    save_snapshot(all_features, live)

    # Step 4
    updates, build_counters = build_updates(all_features, lookup, sample_set)
    if not updates:
        log.info("  No updates needed — all correct!")
        return

    # Step 5
    apply_result = apply_updates(fl, updates, live)

    # Step 6
    verify_updates(fl, lookup, live, sample_set)

    elapsed = (datetime.now() - start).total_seconds()

    # =================================================================
    # AUDIT
    # =================================================================
    log.info("")
    log.info("=" * 70)
    log.info("AUDIT")
    log.info("=" * 70)

    log.info(f"  Lookup size:       {len(lookup)}")
    log.info(f"  Features matched:  {len(all_features)}")
    log.info(f"  Unique callids:    {len(all_features) - sum(v - 1 for v in dupes.values()) if dupes else len(all_features)}")
    log.info(f"  Duplicate callids: {len(dupes)}")
    log.info(f"  Already correct:   {build_counters['already_correct']}")
    log.info(f"  Updates prepared:  {len(updates)}")
    if live:
        log.info(f"  Updates succeeded: {apply_result['succeeded']}")
        log.info(f"  Updates failed:    {apply_result['failed']}")

    exit_code = 0

    if args.expected_updates is not None:
        exp = args.expected_updates
        actual = len(updates)
        max_miss = exp * (args.max_miss_rate / 100.0)
        diff = abs(actual - exp)
        if diff > max_miss:
            log.error(
                f"  AUDIT FAIL: expected ~{exp} updates, got {actual} "
                f"(diff {diff} > {max_miss:.0f} allowed)")
            exit_code = 1
        else:
            log.info(
                f"  AUDIT PASS: {actual} updates vs {exp} expected "
                f"(within {args.max_miss_rate}%)")
    else:
        if len(updates) > 0 and abs(len(updates) - len(lookup)) > len(lookup) * 0.1:
            log.warning(
                f"  NOTE: {len(updates)} updates vs {len(lookup)} lookup "
                f"entries — >10% diff, review")

    if live and apply_result["failed"] > 0:
        log.error(f"  {apply_result['failed']} records FAILED to update")
        exit_code = 1

    # Write summary artifact
    summary = {
        "timestamp": TIMESTAMP,
        "script_version": "v4",
        "mode": "live" if live else "dry_run",
        "timezone": LOCAL_TZ_NAME,
        "gap_range": f"{GAP_CALLID_MIN} to {GAP_CALLID_MAX}",
        "online_service": ONLINE_SERVICE,
        "lookup_size": len(lookup),
        "features_matched": len(all_features),
        "duplicates": len(dupes),
        "already_correct": build_counters["already_correct"],
        "updates_prepared": len(updates),
        "updates_succeeded": apply_result.get("succeeded", 0),
        "updates_failed": apply_result.get("failed", 0),
        "oor_dispatch_nulled": build_counters["out_of_range_dispatch"],
        "expected_updates": args.expected_updates,
        "audit_pass": exit_code == 0,
        "duration_sec": round(elapsed, 1),
        "output_dir": RUN_OUT_DIR,
    }
    with open(SUMMARY_FILE, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)

    log.info(f"  Duration:  {elapsed:.1f}s")
    log.info(f"  Output:    {RUN_OUT_DIR}")

    if not live:
        log.info("")
        log.info("  >>> DRY RUN complete. Re-run with --live to apply. <<<")
    else:
        log.info("")
        log.info("  >>> To rollback: propy.bat fix_gap_calldate_online.py --rollback <<<")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
