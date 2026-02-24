# How to Tell If Deploy-ToRDP-Simple.ps1 Worked

## 1. PowerShell exit and console output

- If the script **completed without throwing**, it succeeded. It does not use `exit 0`; it just ends after "Deployment Complete".
- If it **hit an error** (e.g. "Cannot access RDP scripts directory", "ERROR copying"), it would have stopped with an error and possibly exit codes 2 or 3.

## 2. Check the latest deploy log

Logs are written to:

`<repo>\deploy_logs\Deploy_YYYYMMDD_HHMMSS.log`

**Success looks like:**

- `[OK] RDP scripts directory accessible`
- `[OK] RDP docs directory accessible`
- `[OK] Backup complete:` (unless you used `-NoBackup`)
- Many lines like `Deployed: <filename>`
- `[OK] Deployed N scripts to: \\HPD2022LAWSOFT\C$\HPD ESRI\04_Scripts`
- `[OK] Deployed 3 docs to: ...`
- `Deployment finished at ...`
- `Log file: ...`

**Quick check (PowerShell):** Run from any directory by using the **full path** to the repo (not `.\deploy_logs`, which is relative to your current folder):

```powershell
$repo = "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
$logDir = Join-Path $repo "deploy_logs"
$latest = Get-ChildItem $logDir -Filter "Deploy_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latest.FullName -Tail 15
```

If the last lines show "Deployment finished" and "Deployed N scripts", the run succeeded.

## 3. Verify on the RDP server (optional)

If you can open the server (e.g. `\\HPD2022LAWSOFT\C$\HPD ESRI\04_Scripts`):

- Check that **complete_backfill_simplified.py** (and other scripts) have a **Last modified** time matching when you ran the deploy.
- Check that **SUMMARY.md**, **README.md**, **CHANGELOG.md** exist under `C:\HPD ESRI\` and were updated.

## 4. Dry-run first (recommended)

To see what *would* be deployed without copying anything:

```powershell
.\Deploy-ToRDP-Simple.ps1 -DryRun
```

You should see `[DRY-RUN] Would deploy N files` and no errors. Then run without `-DryRun` to do the real deploy.

---

## Checking data gap and X/Y on the CallsForService layer

After deployment you can run (on the RDP server, with ArcGIS Pro / Pro Python):

```powershell
"C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "C:\HPD ESRI\04_Scripts\check_layer_gap_and_geometry.py"
```

This script reports:

- **Total record count**
- **Date range** (min/max `calldate` when available)
- **Count by year** (2019–2026) using `callyear`
- **Geometry sample**: how many of 1,000 sampled features have X/Y (valid point geometry)

The report is also written to `C:\HPD ESRI\04_Scripts\_out\layer_gap_geometry_YYYYMMDD_HHMMSS.json`.
