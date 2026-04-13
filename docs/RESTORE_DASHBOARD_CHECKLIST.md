# Restore CallsForService Dashboard (Blank Table / 0 Records)

**Dashboard:** [CallsForService](https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data)

## Why you see 9,672 records but blank table / 0 on dashboard

The hosted layer has **9,672 rows** but **no valid geometry** (X/Y is NULL). ArcGIS often shows:
- Item page: total count (9,672) but table view blank or no map
- Dashboard: 0 records (widgets may filter to “features with geometry” or fail to draw)

**Fix:** Clear the bad data and re-publish **with** geometry using the updated backfill script.

---

## Prerequisites (before running on RDP)

1. **Deploy latest scripts.** Run `Deploy-ToRDP-Simple.ps1` from the repo so RDP has:
   - `truncate_online_layer.py` with **UTF-8 log encoding** (fixes crash on ✅/❌ emoji on Windows)
   - `complete_backfill_simplified.py` with coordinate fallback (longitude/latitude or X_Coord/Y_Coord) and Step 10 geometry fix

2. **Staging file must have coordinates.** One of:
   - **Standard CAD export:** columns `longitude`, `latitude`
   - **Geocoded cache:** columns `X_Coord`, `Y_Coord` (e.g. December 2025 geocoded file)

3. **Staging path on RDP:**  
   `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx`  
   Copy your chosen source (with coords) there and ensure the sheet name matches what the script expects (usually first sheet / `Sheet1$`).

4. **(Optional) Fill gap data and ensure X/Y.** If your historical source is missing dates or coordinates, run your gap-fill and geocoding (e.g. `create_geocoding_cache.py` or polished baseline with longitude/latitude or X_Coord/Y_Coord) so the file you put in staging has **all records with valid x and y**. Then deploy that file (or a copy) to RDP staging so the backfill publishes only rows with geometry.

---

## Steps on RDP (in order)

All commands below are run **on the RDP server** (HPD2022LAWSOFT), in a session where ArcGIS Pro is available (e.g. use **propy.bat** for Python).

### 1. Truncate the online layer (clear the 9,672 bad rows)

**Option A – PowerShell helper (on RDP):**
```powershell
cd "C:\HPD ESRI\04_Scripts"
.\Run-TruncateOnRDP.ps1
```

**Option B – Direct Python (on RDP):**
```powershell
cd "C:\HPD ESRI\04_Scripts"
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" truncate_online_layer.py
```

When prompted, type **exactly** (case-sensitive):
- `TRUNCATE`
- Your Windows username (e.g. the one shown in the prompt)
- `DELETE ALL RECORDS`

After a short wait you should see “TRUNCATE COMPLETED SUCCESSFULLY” and the layer will have 0 records.

### 2. Run the backfill (publish with geometry)

**Option A – All-in-one (truncate + backfill + health check) on RDP:**
```powershell
cd "C:\HPD ESRI\04_Scripts"
.\Run-BackfillOnRDP.ps1
```
You will be prompted for the three truncate confirmations at the start; then backfill and monitor run automatically.

**Option B – Backfill only** (after truncate already done):
```powershell
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" complete_backfill_simplified.py
```

- The script reads from `_STAGING\ESRI_CADExport.xlsx`, builds points from longitude/latitude or X_Coord/Y_Coord, and appends the **feature class with geometry** to the online service.
- If it reports “Using coordinate columns: X_Coord, Y_Coord” or “longitude, latitude”, coordinates were detected.
- If it errors with “No point features created” or “No coordinate columns found”, fix the staging file (see Prerequisites).

### 3. Verify health (optional but recommended)

```powershell
& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" monitor_dashboard_health.py
echo $LASTEXITCODE
```

- **Exit code 0** = geometry and WKID OK.
- **Exit code 2** = too many NULL geometries (investigate staging/script).
- **Exit code 3** = WKID mismatch.
- **Exit code 4** = connection/query error.

### 4. Check the dashboard

Open:  
https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2#data  

- **Data** tab: table should show rows and attributes.
- **Visualization** / map: points should draw.
- Your dashboard app: record count and map should show the new data.

---

## If something fails

- **Truncate crashes with `UnicodeEncodeError: 'charmap' codec can't encode character`**  
  The script was writing emoji (✅/❌) to the log file with Windows default encoding. Deploy the latest `truncate_online_layer.py` (it now opens the log file with `encoding="utf-8"`) and run truncate again.

- **“No coordinate columns found”**  
  Staging Excel doesn’t have `longitude`/`latitude` or `X_Coord`/`Y_Coord`. Add those columns or use a source that has them (e.g. geocoded cache).

- **“No point features created”**  
  Coordinate columns exist but values are empty or non-numeric. Check a few rows in Excel; fix or use a different source file.

- **Table still blank / dashboard still 0 after backfill**  
  Run `monitor_dashboard_health.py` and check the JSON report in `C:\HPD ESRI\04_Scripts\_out\`. If null geometry count is high, the append may have failed or the wrong source was used; re-check staging and run truncate + backfill again.

- **Truncate says “permission denied”**  
  You must be the layer owner or an org admin in ArcGIS Online to truncate the hosted feature layer.

---

## Summary

| Step | Script | Purpose |
|------|--------|---------|
| 1 | `truncate_online_layer.py` | Remove the 9,672 rows with no geometry |
| 2 | `complete_backfill_simplified.py` | Publish from staging **with** point geometry |
| 3 | `monitor_dashboard_health.py` | Confirm geometry and WKID |
| 4 | Open dashboard URL | Confirm table and map show data |
