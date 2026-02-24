# Coordinate Column Fallback (X_Coord/Y_Coord vs longitude/latitude)

## Context

- **Dashboard:** [CallsForService](https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data) — must show points, not just "Total: 9672" with no geometry.
- **Gemini session:** `docs/chatlog/Gemini-HPD_ArcGIS_Pro_CAD_Backfill_Script_Patch` — Prompt A (geometry fix) and RDP issues with staging column names.

## Problem

- Staging Excel can be:
  - **Standard CAD export:** columns `longitude`, `latitude`.
  - **Geocoded cache:** columns `X_Coord`, `Y_Coord` (e.g. from `create_geocoding_cache.py`).
- The backfill script previously only used `longitude`/`latitude`. When staging was a geocoded file with only `X_Coord`/`Y_Coord`, all coordinates were effectively NULL → 0 points → dashboard showed count but no map.

## Fix (this repo)

In **Step 6** of `complete_backfill_simplified.py`:

1. **Detect columns:** List fields on the temp table after Table Select. Use `(longitude, latitude)` if both exist; otherwise use `(X_Coord, Y_Coord)` (X_Coord = longitude, Y_Coord = latitude for WGS84).
2. **Same logic:** Existing `safe_float` and XYTableToPoint logic unchanged; only the source field names are chosen dynamically.
3. **Fail-fast:** If point count is 0 after XYTableToPoint, the script raises a clear error instead of continuing and appending nothing.

So both standard exports and geocoded cache staging work without changing the staging file’s column names.

## RDP deployment

1. Deploy updated `complete_backfill_simplified.py` (e.g. `Deploy-ToRDP-Simple.ps1` or manual copy to `C:\HPD ESRI\04_Scripts\`).
2. Ensure staging is the intended source:  
   `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx`  
   with either `longitude`/`latitude` or `X_Coord`/`Y_Coord`.
3. If the current online layer has 9,672 rows with NULL geometry, **truncate then re-publish** so the new run replaces all rows with geometry (or follow your documented append/replace strategy).
4. Run backfill, then `monitor_dashboard_health.py` (expect exit 0) and confirm points on the dashboard.

## References

- Gemini chatlog: `docs/chatlog/Gemini-HPD_ArcGIS_Pro_CAD_Backfill_Script_Patch`
- Dashboard item: https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data
- Geometry fix (Step 10): append `TEMP_FC_3857` to online service — see `docs/APPLIED_GEOMETRY_FIX.md` and `patches/complete_backfill_simplified_geometry_fix.patch`
