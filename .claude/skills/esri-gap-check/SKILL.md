---
name: esri-gap-check
description: Generate a ready-to-paste ArcPy script (for the ArcGIS Pro Python window) that queries the AGOL Calls For Service feature service for missing days in a given lookback window and reports the last 7 days of daily volumes.
disable-model-invocation: true
argument-hint: [days | --from YYYY-MM-DD --to YYYY-MM-DD]
allowed-tools: Read
---

# ESRI Gap Check -- AGOL CallsForService Missing-Days Report

Emit an ArcPy script that queries the AGOL `CallsForService` feature service over a
date window, finds any dates with 0 calls, and shows recent daily volumes.

## Trigger

`/esri-gap-check $ARGUMENTS` or "generate gap check".

- `$ARGUMENTS` may be:
  - empty           => default lookback of 60 days
  - bare integer N  => lookback of N days ending today
  - `--from YYYY-MM-DD --to YYYY-MM-DD` => explicit inclusive window

Invocation patterns:
```
/esri-gap-check
/esri-gap-check 60
/esri-gap-check --from 2026-02-01 --to 2026-04-13
```

## Key Constants

```
AGOL service : https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0
Expected daily volume : ~190-265 calls/day for Hackensack (flag anything < 50)
```

## Output -- ArcPy Script (paste into ArcGIS Pro Python window)

Parse `$ARGUMENTS` into a `$FROM`/`$TO` window (YYYY-MM-DD), then emit this as a
fenced `python` block with those two values substituted:

```python
# === AGOL CallsForService Gap Check: $FROM .. $TO ===
import arcpy
from datetime import datetime, timedelta
from collections import Counter

SERVICE = (
    "https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/"
    "CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0"
)
FROM = datetime.strptime("$FROM", "%Y-%m-%d").date()
TO   = datetime.strptime("$TO",   "%Y-%m-%d").date()

where = (
    f"calldate >= DATE '{FROM.isoformat()}' AND "
    f"calldate <  DATE '{(TO + timedelta(days=1)).isoformat()}'"
)

counts = Counter()
with arcpy.da.SearchCursor(SERVICE, ["calldate"], where_clause=where) as cur:
    for (d,) in cur:
        if d is None:
            continue
        counts[d.date() if hasattr(d, "date") else d] += 1

# Build full date range
all_days = []
cur_day = FROM
while cur_day <= TO:
    all_days.append(cur_day)
    cur_day += timedelta(days=1)

gaps     = [d for d in all_days if counts.get(d, 0) == 0]
low_days = [d for d in all_days if 0 < counts.get(d, 0) < 50]

total = sum(counts.values())
print(f"Window : {FROM} .. {TO}  ({len(all_days)} days)")
print(f"Total records in window: {total:,}")
print(f"Expected ~190-265/day for Hackensack. Flagging days < 50.")
print()

if gaps:
    print(f"GAPS (days with 0 calls): {len(gaps)}")
    for d in gaps:
        print(f"  {d}")
else:
    print("No gap days found.")

if low_days:
    print()
    print(f"LOW-VOLUME days (1-49 calls):")
    for d in low_days:
        print(f"  {d}  count={counts[d]}")

print()
print("Last 7 days of window:")
for d in all_days[-7:]:
    print(f"  {d}  count={counts.get(d, 0)}")
```

## Notes

- The script uses `arcpy.da.SearchCursor` against the hosted service — requires an
  active ArcGIS Pro session signed in to the HPD AGOL org.
- Gap days are days with **zero** records; low-volume days (<50) are surfaced
  separately because they often indicate a partial publish rather than a full gap.
- Hackensack's normal daily volume is roughly 180-280 CFS. A day below 50 almost
  always means the publish run truncated early or the source file had a partial
  date.
- For use right after `esri-backfill`: default the window to cover the backfilled
  month plus a 7-day buffer on each side.
