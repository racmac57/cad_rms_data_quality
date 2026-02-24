# Check Data & Fill Gaps Before Backfill

**When to do this:** When you want the dashboard to have **full historical coverage** (e.g. 2019–2026) and **as many points as possible** (no missing dates, coordinates filled where possible).

---

## 1. Check what’s missing (gap + coordinates)

**On RDP (after you have data in the layer):**  
Run the layer health script to see total count, date range, and geometry:

```powershell
cd "C:\HPD ESRI\04_Scripts"
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" check_layer_gap_and_geometry.py
```

This reports total records, min/max date, counts by year, and how many of a 1,000‑feature sample have X/Y. Use it **before** backfill to see current online state (e.g. 0 after truncate), or **after** a backfill to confirm coverage and geometry.

**Locally (on your baseline/source Excel):**  
- **Date range:** See `docs/BACKFILL_DATE_RANGE.md` – backfill should be 2019-01-01 through 2026-02-15 (or through yesterday).  
- **Date/gap analysis:** `scripts/backfill_gap_analysis.py` – finds duplicate/missing dates and gaps in your source.  
- **Coordinate presence:** `scripts/check_baseline_coordinates.py` – reports how many records have valid latitude/longitude (or X_Coord/Y_Coord).  
- **Address/coordinate readiness:** `scripts/cad_fulladdress2_qc.py` – classifies addresses (e.g. OK_STANDARD, MISSING_CITY_STATE, PO_BOX) so you know what can be geocoded.  
- **CAD gap analysis:** `scripts/CAD_Gap_Analysis.py` – if you use it for CAD-specific gap logic.

Run these against your **source** baseline or monthly exports (the file(s) you will later copy to RDP staging or use to build batches).

---

## 2. Fill gap data (dates) and coordinates

**Gap data (missing dates):**  
- Fix at the source: ensure consolidation and monthly exports include all required date ranges (see consolidation config and `backfill_gap_analysis.py` output).  
- If you use a **single baseline file** for staging, that file should already span the intended range (e.g. 2019–2026); any “gap” is then in the source ETL, not in the backfill script.

**Coordinates (X/Y):**  
- **Standard CAD export:** Many exports already have `longitude` and `latitude`. Use them as-is; `complete_backfill_simplified.py` will use them (or `X_Coord`/`Y_Coord` if that’s what’s present). Run `scripts/check_baseline_coordinates.py` to confirm how many records have valid x/y.  
- **If baseline has 0% coordinates:** The polished baseline Excel may not include lat/lon. Use a source that does (raw CAD export or geocoded cache) for staging.  
- **Missing or sparse coordinates:**  
  - **Geocoded cache:** Run `scripts/create_geocoding_cache.py` (with your baseline/source path and options) to produce a file with `X_Coord`/`Y_Coord` filled for geocodable addresses.  
  - **Single month (e.g. Dec 2025):** `scripts/geocode_december_2025_only.py` – if you only need one month geocoded for a test.  
- **Suppressed home addresses:** Run `scripts/normalize_fulladdress2_suppressed.py` to replace known “home” proxy values with `225 State Street, Hackensack, NJ, 07601` (use `--dry-run` first, then `--output` or `--in-place`).

Output of geocoding is an Excel (or similar) with **X_Coord** and **Y_Coord**. Copy that to RDP as your staging file (or use it to build batches). The backfill script accepts either `longitude`/`latitude` or `X_Coord`/`Y_Coord`.

---

## 3. Recommended order

| Step | Where | What |
|------|--------|------|
| 1 | Local | Run `backfill_gap_analysis.py` (and optionally `cad_fulladdress2_qc.py`, `CAD_Gap_Analysis.py`) on your source data to see gaps and address quality. |
| 2 | Local | Fix date gaps in consolidation/config if needed; run `create_geocoding_cache.py` (or geocode script) so the file you’ll use for backfill has coordinates. |
| 3 | Local | Deploy scripts to RDP (`Deploy-ToRDP-Simple.ps1`). |
| 4 | RDP | Put the **gap-filled, coordinate-rich** file in staging (or in batch folder). |
| 5 | RDP | Truncate (already done) then run backfill (`complete_backfill_simplified.py` or `Run-BackfillOnRDP.ps1`). |
| 6 | RDP | Run `check_layer_gap_and_geometry.py` and `monitor_dashboard_health.py`; confirm dashboard shows expected range and points. |

---

## 4. Do you have to fill gaps before every backfill?

- **No** – You can run backfill with whatever file you have in staging (e.g. one month, or a partial baseline). The dashboard will show that subset.  
- **Yes, for “complete” coverage** – To avoid missing dates and to maximize points, check the data and fill gap data and coordinates **before** the run that you consider your full historical load.

So: **check the data and fill gap data (and coordinates) when you want full coverage and maximum points;** then use that improved file as staging (or to build batches) and run the backfill.
