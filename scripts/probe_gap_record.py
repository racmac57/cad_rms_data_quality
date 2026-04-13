# 🕒 2026-02-16-22-00-00
# cad_rms_data_quality/probe_gap_record.py
# Author: R. A. Carucci
# Purpose: One-record probe to verify timezone behavior and field values
#          before running the gap calldate fix scripts. READ-ONLY.
#          v4: Supports --sample-callids for multi-record probing.

"""
=============================================================================
PROBE GAP RECORD — TIMEZONE & FIELD VERIFICATION (v4)
=============================================================================
Queries known gap record(s) from both local and online sources.
Compares system-naive epoch vs forced-NY epoch to detect timezone mismatch.

USAGE:
  propy.bat probe_gap_record.py
  propy.bat probe_gap_record.py --sample-callids 26-011297,26-011300,26-012500
=============================================================================
"""

import arcpy
import os
import sys
import argparse
from datetime import datetime, timezone
import time as _time

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


def ny_epoch_ms(dt):
    return int(as_local(dt).astimezone(UTC_TZ).timestamp() * 1000)


def ny_from_epoch_ms(ms):
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=UTC_TZ).astimezone(LOCAL_TZ)


# =============================================================================
# CONFIG
# =============================================================================

GDB = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.gdb"
GAP_TABLE = os.path.join(GDB, "gap_for_append_v2")
ONLINE_SERVICE = (
    "https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/"
    "CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0"
)
DEFAULT_PROBE = "26-011297"
EXPECTED_REAL_DT = datetime(2026, 2, 3, 10, 14, 14)

DIV = "=" * 60


def section(title):
    print(f"\n{DIV}")
    print(f"  {title}")
    print(DIV)


def find_fields(table):
    """Auto-detect callid and time fields."""
    fields = [f.name for f in arcpy.ListFields(table)]
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
    return cid_f, time_f, fields


def probe_local(callid, cid_field, time_field):
    """Query local gap table for a single Call ID."""
    print(f"\n  --- LOCAL: {callid} ---")
    found = False
    with arcpy.da.SearchCursor(
        GAP_TABLE, [cid_field, time_field],
        where_clause=f"{cid_field} = '{callid}'"
    ) as cur:
        for row in cur:
            found = True
            local_dt = row[1]
            print(f"  Raw value:        {local_dt}")
            print(f"  Type:             {type(local_dt).__name__}")
            if isinstance(local_dt, datetime):
                local_ny = as_local(local_dt)
                epoch = ny_epoch_ms(local_dt)
                print(f"  As NY time:       {local_ny}")
                print(f"  NY epoch ms:      {epoch}")
    if not found:
        print(f"  NOT FOUND in gap_for_append_v2")


def probe_online(callids, fl):
    """Query online layer for Call IDs."""
    where = "callid IN ({})".format(",".join(f"'{c}'" for c in callids))
    try:
        result = fl.query(
            where=where,
            out_fields="OBJECTID,callid,calldate,dispatchdate,"
                       "calldow,calldownum,callhour,callmonth,callyear,"
                       "dispatchtime,queuetime,responsetime",
            return_geometry=False
        )
    except Exception as e:
        print(f"  Query failed: {e}")
        return

    if not result.features:
        print(f"  No matching records found online")
        return

    for f in result.features:
        a = f.attributes
        cid = a.get("callid", "?")
        print(f"\n  --- ONLINE: {cid} (OID {a.get('OBJECTID')}) ---")
        cd_epoch = a.get("calldate")
        cd_ny = ny_from_epoch_ms(cd_epoch)
        dd_epoch = a.get("dispatchdate")
        dd_ny = ny_from_epoch_ms(dd_epoch)
        print(f"  calldate epoch:   {cd_epoch}")
        print(f"  calldate (NY):    {cd_ny}")
        print(f"  dispatchdate:     {dd_epoch} -> {dd_ny}")
        print(f"  calldow:          {a.get('calldow')}")
        print(f"  calldownum:       {a.get('calldownum')}")
        print(f"  callhour:         {a.get('callhour')}")
        print(f"  callmonth:        {a.get('callmonth')}")
        print(f"  callyear:         {a.get('callyear')}")
        print(f"  dispatchtime:     {a.get('dispatchtime')}")
        print(f"  queuetime:        {a.get('queuetime')}")
        print(f"  responsetime:     {a.get('responsetime')}")

    dupes = {}
    for f in result.features:
        c = f.attributes.get("callid", "")
        dupes[c] = dupes.get(c, 0) + 1
    for c, n in dupes.items():
        if n > 1:
            print(f"\n  *** DUPLICATE: {c} has {n} records online ***")


def main():
    parser = argparse.ArgumentParser(description="Probe gap record(s)")
    parser.add_argument("--sample-callids", type=str, default=DEFAULT_PROBE,
                        help="Comma-separated Call IDs to probe")
    args = parser.parse_args()

    callids = [c.strip() for c in args.sample_callids.split(",") if c.strip()]

    print(DIV)
    print(f"  PROBE GAP RECORD (v4)")
    print(f"  Probing: {', '.join(callids)}")
    print(f"  Timestamp: {datetime.now()}")
    print(DIV)

    # ─── 1. TIMEZONE ───
    section("1. SYSTEM TIMEZONE")

    tz_name = _time.tzname
    utc_std = -(_time.timezone / 3600)
    utc_dst = -(_time.altzone / 3600) if _time.daylight else utc_std
    dst_now = bool(_time.daylight and _time.localtime().tm_isdst)

    print(f"  Timezone name:    {tz_name}")
    print(f"  UTC offset (std): {utc_std:+.0f} hours")
    print(f"  UTC offset (DST): {utc_dst:+.0f} hours")
    print(f"  DST active now:   {dst_now}")
    print(f"  Forced LOCAL_TZ:  {LOCAL_TZ_NAME}")

    if utc_std in (-5.0,) and utc_dst in (-4.0,):
        print(f"  System TZ:        Eastern CONFIRMED")
    else:
        print(f"  System TZ:        *** NOT Eastern — forced-NY active ***")

    # ─── 2. EPOCH CHECK ───
    section("2. EPOCH CONVERSION CHECK (NY vs SYSTEM)")

    system_epoch = int(EXPECTED_REAL_DT.timestamp() * 1000)
    ny_epoch = ny_epoch_ms(EXPECTED_REAL_DT)

    print(f"  EXPECTED_REAL_DT (naive):   {EXPECTED_REAL_DT}")
    print(f"  System epoch ms (naive ts): {system_epoch}")
    print(f"  NY epoch ms (forced NY):    {ny_epoch}")

    if system_epoch != ny_epoch:
        delta = (system_epoch - ny_epoch) / 1000.0
        print(f"  *** WARNING: System TZ mismatch! Delta = {delta:+.1f}s ***")
        print(f"  Scripts use forced-NY so this is handled, but verify")
        print(f"  that CAD source datetimes represent Eastern time.")
    else:
        print(f"  System and NY epochs MATCH")

    rt = ny_from_epoch_ms(ny_epoch)
    drift = abs((rt.replace(tzinfo=None) - EXPECTED_REAL_DT).total_seconds())
    print(f"  NY round-trip:              {rt}")
    print(f"  Drift:                      {drift:.3f}s")

    if drift > 1.0:
        print(f"  *** FAIL: {drift:.1f}s drift — DO NOT PROCEED ***")
        sys.exit(1)
    else:
        print(f"  Status:                     PASS")

    # ─── 3. LOCAL ───
    section("3. LOCAL: gap_for_append_v2")

    if not arcpy.Exists(GAP_TABLE):
        print(f"  ERROR: {GAP_TABLE} not found")
    else:
        cid_f, time_f, fields = find_fields(GAP_TABLE)
        print(f"  Fields: {fields}")
        print(f"  Call ID field: {cid_f}")
        print(f"  Time field:    {time_f}")
        if cid_f and time_f:
            for cid in callids:
                probe_local(cid, cid_f, time_f)

    # ─── 4. ONLINE ───
    section("4. ONLINE: ArcGIS Online Feature Layer")

    try:
        from arcgis.gis import GIS
        from arcgis.features import FeatureLayer

        gis = GIS("pro")
        print(f"  Connected as: {gis.properties.user.username}")
        fl = FeatureLayer(ONLINE_SERVICE, gis=gis)
        probe_online(callids, fl)
    except Exception as e:
        print(f"  ERROR: {e}")

    # ─── 5. SUMMARY ───
    section("5. NEXT STEPS")

    ny_dt = as_local(EXPECTED_REAL_DT)
    print(f"  If all looks correct, proceed with:")
    print(f"    1. propy.bat fix_gap_calldate_local.py               (dry run)")
    print(f"    2. propy.bat fix_gap_calldate_local.py --live         (apply)")
    print(f"    3. propy.bat fix_gap_calldate_online.py               (dry run)")
    print(f"    4. propy.bat fix_gap_calldate_online.py --live        (apply)")
    print(DIV)


if __name__ == "__main__":
    main()
