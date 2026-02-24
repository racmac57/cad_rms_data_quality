# Review: Gemini's RDP Command for December 2025 Geocoding

**Reviewed against:** `scripts/create_geocoding_cache.py` (with `--locator` and RDP NJ_Geocode support).

---

## Verdict: **Correct and ready to use**

Gemini's PowerShell command matches our script's CLI and RDP paths. A few clarifications below.

---

## Command (use as-is on RDP)

```powershell
cd "C:\HPD ESRI\04_Scripts"

& "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" create_geocoding_cache.py `
  --input "C:\HPD ESRI\03_Data\CAD\Backfill\2025_12_CAD_Data.xlsx" `
  --output-dir "C:\HPD ESRI\03_Data\CAD\Backfill\cached" `
  --output-name "2025_12_CAD_GEO_CACHED.xlsx" `
  --locator "C:\HPD ESRI\NJ_Geocode\NJ_Geocode.loc"
```

- **Script:** All four arguments (`--input`, `--output-dir`, `--output-name`, `--locator`) are implemented and behave as described.
- **Locator:** We use the `.loc` path; the `.loz` is the data index and is used automatically by ArcPy.
- **Output:** The script adds `latitude` and `longitude` columns (from X_Coord/Y_Coord) so the cached file is ready for the backfill pipeline.

---

## Input filename: which December file?

- **On RDP Backfill folder (prior sessions):** The file has been saved as **`2025_12_CAD_Data.xlsx`** at `C:\HPD ESRI\03_Data\CAD\Backfill\` (see chatlog/docs).
- **If you copied from OneDrive monthly export:** The name may be **`2025_12_CAD.xlsx`** (repo convention for `05_EXPORTS\_CAD\monthly\2025\`).

**Action:** Before running, confirm which file exists (or copy your December export into Backfill and use that path):

```powershell
Get-ChildItem "C:\HPD ESRI\03_Data\CAD\Backfill\*2025*12*.xlsx"
```

If the file is named `2025_12_CAD.xlsx`, change the `--input` path to:

`"C:\HPD ESRI\03_Data\CAD\Backfill\2025_12_CAD.xlsx"`.

---

## Why it fits the 30-minute window

1. **Single-month input** keeps record count low (~6K–10K); with the **local** NJ locator (no internet), runtime should be on the order of minutes, not tens of minutes.
2. **`--locator`** forces use of `NJ_Geocode.loc`, avoiding World Geocoding Service timeouts.
3. **`--output-name`** writes a dedicated file so the main baseline cache is not overwritten.

---

## Verification checklist (from Gemini) — endorsed

- **Input file:** Confirm the December `.xlsx` exists in Backfill (and use the correct filename in `--input`).
- **Locator:** Use the `.loc` path; no need to pass the `.loz`.
- **Console:** You should see: `Using local locator: C:\HPD ESRI\NJ_Geocode\NJ_Geocode.loc`.

---

## If you get "Address field mapping" / 99999 errors

The script uses **"Address OR Intersection"** for local `.loc` and maps your table’s address column (e.g. **FullAddress2**) to it. If the NJ locator expects a different input role:

1. **Quick workaround:** Omit `--locator` so the script uses the World Geocoding Service (requires internet on RDP). Same command without the last line:
   ```powershell
   & "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" create_geocoding_cache.py `
     --input "C:\HPD ESRI\03_Data\CAD\Backfill\2025_12_CAD_Data.xlsx" `
     --output-dir "C:\HPD ESRI\03_Data\CAD\Backfill\cached" `
     --output-name "2025_12_CAD_GEO_CACHED.xlsx"
   ```
2. **Permanent fix:** We could add an optional `--address-fields` (or similar) to override the `in_address_fields` string for the NJ locator; that can be done if you hit this error.

---

## Summary

- **Use Gemini’s command as-is** after confirming the December input path/filename.
- **RDP paths and `--locator`** are correct and match our implementation.
- **Verification steps and fallback** (drop `--locator` to use World) are sound.
