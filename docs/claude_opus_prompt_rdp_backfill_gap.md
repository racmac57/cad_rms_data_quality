Below are A (timezone-hardening) and B (local WHERE clause hardening) as “drop-in patches” you can hand to Opus, plus a single prompt that lists the issues + asks Opus to fold the edits in cleanly.

A) Timezone-hardening (America/New_York) — for Opus to fold in
A1) Patch for fix_gap_calldate_online.py

Goal: stop relying on OS timezone (dt.timestamp() / datetime.fromtimestamp() on naive datetimes). Force America/New_York for local datetimes, convert to UTC epoch ms for AGOL, and convert AGOL epoch ms back to NY time for derived fields / logging.

Tell Opus to:

Add ZoneInfo + constants near imports

Replace datetime_to_epoch_ms() and epoch_ms_to_datetime()

Update compute_derived_fields() to:

compute DOW/hour/month/year in NY

compute dispatchtime using UTC vs UTC (handles DST cleanly)

null out dispatchtime/responsetime when out-of-range (don’t “skip”)

Use this replacement block:

# --- ADD near imports (top of file) ---

from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

LOCAL_TZ_NAME = "America/New_York"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME) if ZoneInfo else datetime.now().astimezone().tzinfo
UTC_TZ = timezone.utc

def as_local(dt: datetime) -> datetime:
    """
    Treat naive datetimes as LOCAL_TZ (America/New_York), and normalize aware
    datetimes into LOCAL_TZ.
    """
    if dt is None:
        return None
    if not isinstance(dt, datetime):
        raise TypeError(f"Expected datetime, got {type(dt).__name__}")
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(LOCAL_TZ)

def datetime_to_epoch_ms(dt):
    """Convert datetime -> epoch ms (UTC) for AGOL. Naive assumed LOCAL_TZ."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        dt_local = as_local(dt)
        dt_utc = dt_local.astimezone(UTC_TZ)
        return int(dt_utc.timestamp() *1000)
    # pass-through numeric-ish
    try:
        return int(float(dt)* 1000) if dt else None
    except (ValueError, TypeError):
        return None

def epoch_ms_to_datetime(epoch_ms, tz=LOCAL_TZ):
    """Convert AGOL epoch ms (UTC) -> tz-aware datetime in tz (default LOCAL_TZ)."""
    if epoch_ms is None:
        return None
    try:
        dt_utc = datetime.fromtimestamp(epoch_ms / 1000, tz=UTC_TZ)
        return dt_utc.astimezone(tz)
    except (ValueError, TypeError, OSError):
        return None

def compute_derived_fields(calldate_dt, dispatchdate_epoch_ms, queuetime_val):
    """
    Compute derived fields from corrected calldate.
    - Derived date parts computed in LOCAL_TZ (America/New_York)
    - dispatchtime computed using UTC deltas (DST-safe)
    - Out-of-range dispatch/responsetime => None (prevents stale metrics)
    """
    result = {}
    if calldate_dt is None:
        return result

    calldate_local = as_local(calldate_dt)

    # Date attributes from calldate (LOCAL)
    dow_name, dow_num = DOW_NAMES.get(calldate_local.weekday(), ("Unknown", 0))
    result["calldow"] = dow_name
    result["calldownum"] = dow_num
    result["callhour"] = calldate_local.hour
    result["callmonth"] = calldate_local.month
    result["callyear"] = calldate_local.year

    # dispatchtime/responsetime
    result["dispatchtime"] = None
    result["responsetime"] = None

    if dispatchdate_epoch_ms is None:
        return result

    dispatch_utc = datetime.fromtimestamp(dispatchdate_epoch_ms / 1000, tz=UTC_TZ)
    calldate_utc = calldate_local.astimezone(UTC_TZ)

    diff_min = (dispatch_utc - calldate_utc).total_seconds() / 60.0

    # sanity: 0..1440 minutes
    if not (0 <= diff_min <= 1440):
        log.warning(f"  Dispatchtime {diff_min:.1f} min out of range -> NULL")
        return result

    result["dispatchtime"] = round(diff_min, 4)

    if queuetime_val is not None:
        try:
            result["responsetime"] = round(diff_min + float(queuetime_val), 4)
        except (ValueError, TypeError):
            result["responsetime"] = None

    return result

Optional (but recommended) small tweak in logging: in build_updates(), use real_local = as_local(real_dt) for display consistency.

A2) Patch for probe_gap_record.py

Goal: make the probe a real detector:

show NY epoch ms (correct)

show system epoch ms (what naive timestamp() will do)

if they differ, warn: “your machine TZ is not Eastern; stop.”

Ask Opus to add helper functions + compare epochs.

Drop-in snippet:

# --- ADD near imports ---

from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

LOCAL_TZ_NAME = "America/New_York"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME) if ZoneInfo else datetime.now().astimezone().tzinfo
UTC_TZ = timezone.utc

def as_local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(LOCAL_TZ)

def ny_epoch_ms(dt: datetime) -> int:
    return int(as_local(dt).astimezone(UTC_TZ).timestamp() * 1000)

def ny_from_epoch_ms(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=UTC_TZ).astimezone(LOCAL_TZ)

Then replace the “round-trip drift” section with:

    section("2. EPOCH CONVERSION CHECK (NY vs SYSTEM)")

    system_epoch_ms = int(EXPECTED_REAL_DT.timestamp() * 1000)
    expected_epoch_ms = ny_epoch_ms(EXPECTED_REAL_DT)

    print(f"  EXPECTED_REAL_DT (naive):   {EXPECTED_REAL_DT}")
    print(f"  System epoch ms (naive ts): {system_epoch_ms}")
    print(f"  NY epoch ms (forced NY):    {expected_epoch_ms}")

    if system_epoch_ms != expected_epoch_ms:
        delta_sec = (system_epoch_ms - expected_epoch_ms) / 1000.0
        print(f"  WARNING: System TZ mismatch. Δ={delta_sec:+.1f}s")
        print("  STOP: Fix machine timezone or use forced-NY conversion everywhere.")

    rt = ny_from_epoch_ms(expected_epoch_ms)
    drift = abs((rt.replace(tzinfo=None) - EXPECTED_REAL_DT).total_seconds())
    print(f"  NY roundtrip:               {rt}")
    print(f"  Drift (NY roundtrip):       {drift:.3f}s")

B) Local script WHERE clause hardening — for Opus to fold in (fix_gap_calldate_local.py)

Problem: WHERE callid >= '26-011288' AND callid <= '26-014999' is lexicographic; if any callids are oddly formatted (missing zero padding), they can be excluded from the cursor entirely.

Fix: broaden the cursor filter to “all 2026 calls”, then rely on callid_in_gap_range() (already numeric-based) to do the true bounding.

Replace the where = ... line with:

where = f"{callid_name} LIKE '26-%'"

Everything else stays the same (since you already enforce callid_in_gap_range() inside the loop).

Below are A (timezone-hardening) and B (local WHERE clause hardening) as “drop-in patches” you can hand to Opus, plus a single prompt that lists the issues + asks Opus to fold the edits in cleanly.

A) Timezone-hardening (America/New_York) — for Opus to fold in
A1) Patch for fix_gap_calldate_online.py

Goal: stop relying on OS timezone (dt.timestamp() / datetime.fromtimestamp() on naive datetimes). Force America/New_York for local datetimes, convert to UTC epoch ms for AGOL, and convert AGOL epoch ms back to NY time for derived fields / logging.

Tell Opus to:

Add ZoneInfo + constants near imports

Replace datetime_to_epoch_ms() and epoch_ms_to_datetime()

Update compute_derived_fields() to:

compute DOW/hour/month/year in NY

compute dispatchtime using UTC vs UTC (handles DST cleanly)

null out dispatchtime/responsetime when out-of-range (don’t “skip”)

Use this replacement block:

# --- ADD near imports (top of file) ---
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

LOCAL_TZ_NAME = "America/New_York"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME) if ZoneInfo else datetime.now().astimezone().tzinfo
UTC_TZ = timezone.utc


def as_local(dt: datetime) -> datetime:
    """
    Treat naive datetimes as LOCAL_TZ (America/New_York), and normalize aware
    datetimes into LOCAL_TZ.
    """
    if dt is None:
        return None
    if not isinstance(dt, datetime):
        raise TypeError(f"Expected datetime, got {type(dt).__name__}")
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(LOCAL_TZ)


def datetime_to_epoch_ms(dt):
    """Convert datetime -> epoch ms (UTC) for AGOL. Naive assumed LOCAL_TZ."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        dt_local = as_local(dt)
        dt_utc = dt_local.astimezone(UTC_TZ)
        return int(dt_utc.timestamp() * 1000)
    # pass-through numeric-ish
    try:
        return int(float(dt) * 1000) if dt else None
    except (ValueError, TypeError):
        return None


def epoch_ms_to_datetime(epoch_ms, tz=LOCAL_TZ):
    """Convert AGOL epoch ms (UTC) -> tz-aware datetime in tz (default LOCAL_TZ)."""
    if epoch_ms is None:
        return None
    try:
        dt_utc = datetime.fromtimestamp(epoch_ms / 1000, tz=UTC_TZ)
        return dt_utc.astimezone(tz)
    except (ValueError, TypeError, OSError):
        return None


def compute_derived_fields(calldate_dt, dispatchdate_epoch_ms, queuetime_val):
    """
    Compute derived fields from corrected calldate.
    - Derived date parts computed in LOCAL_TZ (America/New_York)
    - dispatchtime computed using UTC deltas (DST-safe)
    - Out-of-range dispatch/responsetime => None (prevents stale metrics)
    """
    result = {}
    if calldate_dt is None:
        return result

    calldate_local = as_local(calldate_dt)

    # Date attributes from calldate (LOCAL)
    dow_name, dow_num = DOW_NAMES.get(calldate_local.weekday(), ("Unknown", 0))
    result["calldow"] = dow_name
    result["calldownum"] = dow_num
    result["callhour"] = calldate_local.hour
    result["callmonth"] = calldate_local.month
    result["callyear"] = calldate_local.year

    # dispatchtime/responsetime
    result["dispatchtime"] = None
    result["responsetime"] = None

    if dispatchdate_epoch_ms is None:
        return result

    dispatch_utc = datetime.fromtimestamp(dispatchdate_epoch_ms / 1000, tz=UTC_TZ)
    calldate_utc = calldate_local.astimezone(UTC_TZ)

    diff_min = (dispatch_utc - calldate_utc).total_seconds() / 60.0

    # sanity: 0..1440 minutes
    if not (0 <= diff_min <= 1440):
        log.warning(f"  Dispatchtime {diff_min:.1f} min out of range -> NULL")
        return result

    result["dispatchtime"] = round(diff_min, 4)

    if queuetime_val is not None:
        try:
            result["responsetime"] = round(diff_min + float(queuetime_val), 4)
        except (ValueError, TypeError):
            result["responsetime"] = None

    return result


Optional (but recommended) small tweak in logging: in build_updates(), use real_local = as_local(real_dt) for display consistency.

A2) Patch for probe_gap_record.py

Goal: make the probe a real detector:

show NY epoch ms (correct)

show system epoch ms (what naive timestamp() will do)

if they differ, warn: “your machine TZ is not Eastern; stop.”

Ask Opus to add helper functions + compare epochs.

Drop-in snippet:

# --- ADD near imports ---
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

LOCAL_TZ_NAME = "America/New_York"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME) if ZoneInfo else datetime.now().astimezone().tzinfo
UTC_TZ = timezone.utc


def as_local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(LOCAL_TZ)


def ny_epoch_ms(dt: datetime) -> int:
    return int(as_local(dt).astimezone(UTC_TZ).timestamp() * 1000)


def ny_from_epoch_ms(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=UTC_TZ).astimezone(LOCAL_TZ)


Then replace the “round-trip drift” section with:

    section("2. EPOCH CONVERSION CHECK (NY vs SYSTEM)")

    system_epoch_ms = int(EXPECTED_REAL_DT.timestamp() * 1000)
    expected_epoch_ms = ny_epoch_ms(EXPECTED_REAL_DT)

    print(f"  EXPECTED_REAL_DT (naive):   {EXPECTED_REAL_DT}")
    print(f"  System epoch ms (naive ts): {system_epoch_ms}")
    print(f"  NY epoch ms (forced NY):    {expected_epoch_ms}")

    if system_epoch_ms != expected_epoch_ms:
        delta_sec = (system_epoch_ms - expected_epoch_ms) / 1000.0
        print(f"  WARNING: System TZ mismatch. Δ={delta_sec:+.1f}s")
        print("  STOP: Fix machine timezone or use forced-NY conversion everywhere.")

    rt = ny_from_epoch_ms(expected_epoch_ms)
    drift = abs((rt.replace(tzinfo=None) - EXPECTED_REAL_DT).total_seconds())
    print(f"  NY roundtrip:               {rt}")
    print(f"  Drift (NY roundtrip):       {drift:.3f}s")

B) Local script WHERE clause hardening — for Opus to fold in (fix_gap_calldate_local.py)

Problem: WHERE callid >= '26-011288' AND callid <= '26-014999' is lexicographic; if any callids are oddly formatted (missing zero padding), they can be excluded from the cursor entirely.

Fix: broaden the cursor filter to “all 2026 calls”, then rely on callid_in_gap_range() (already numeric-based) to do the true bounding.

Replace the where = ... line with:

where = f"{callid_name} LIKE '26-%'"


Everything else stays the same (since you already enforce callid_in_gap_range() inside the loop).

Prompt to send Opus (copy/paste)

Use this to get Opus to fold everything in cleanly:

You previously generated: probe_gap_record.py, fix_gap_calldate_local.py, fix_gap_calldate_online.py. Please apply the following improvements and output updated full scripts.

Issues found + required changes

Timezone hardening (critical): Both the probe and online updater still rely on OS timezone behavior for naive datetimes via dt.timestamp() / datetime.fromtimestamp(). This can shift times if the RDP box isn’t Eastern.

Implement forced timezone handling using ZoneInfo("America/New_York").

For conversions: treat naive local datetimes as NY time → convert to UTC epoch ms for AGOL. Convert AGOL epoch ms (UTC) back to NY timezone-aware datetimes for display / derived fields.

Add helper as_local() and new conversion helpers in BOTH probe + online scripts.

Probe drift check isn’t meaningful as written: “epoch round-trip drift” always returns ~0 in whatever the current system timezone is.

Change the probe to compare system epoch ms (naive .timestamp()) vs NY epoch ms (forced NY).

If they differ, print a loud WARNING and instruct to STOP.

Online derived fields / response metrics consistency: Ensure compute_derived_fields() computes DOW/hour/month/year in NY time, and computes dispatchtime using UTC deltas (DST-safe). If dispatchtime is out of [0,1440], set dispatchtime/responsetime = None (do not “skip” leaving stale values).

Local cursor WHERE clause fragility: WHERE callid >= '26-011288' AND callid <= '26-014999' is lexicographic and may miss non-zero-padded callids.

Replace it with WHERE callid LIKE '26-%' and rely on existing numeric callid_in_gap_range() filter to do the real bounding.

Acceptance criteria

Probe prints system tz offsets and prints both epoch values; warns if mismatch.

Online dry-run shows sample before/after datetimes matching expected NY times; no offsets.

Online derived fields (hour, DOW, etc.) match NY time; dispatch/responsetime get nulled if out-of-range.

Local script still updates only gap range, and no missed records due to lexicographic WHERE.

Please fold these edits in and return updated scripts.
