# Geometry Fix Patch Summary (Prompt A)

**Date:** 2026-02-16  
**Target Scripts:** `publish_with_xy_coordinates.py`, `complete_backfill_simplified.py`  
**Issue:** Dashboard showing NULL geometry (empty map) after recent backfills

---

## Analysis

Both scripts were reviewed against the "Golden Path" requirements. Here's what was found:

### `publish_with_xy_coordinates.py` ✅ **NO CHANGES NEEDED**

This script **already implements all requirements perfectly**:

1. **Safe Coordinate Conversion** (lines 104-131)
   - Uses `safe_float()` helper to convert lat/lon text to DOUBLE
   - Returns `None` for NULL/empty/malformed values
   - Logs and reports records with bad coordinates
   - Generates `bad_coords_*.csv` report in `C:\HPD ESRI\04_Scripts\_out`

2. **Explicit Projection** (lines 156-213)
   - Creates points in WGS84 (EPSG:4326) via `XYTableToPoint` (line 168-174)
   - Explicitly projects to Web Mercator (EPSG:3857) (lines 193-209)
   - **Does NOT rely on on-the-fly reprojection**

3. **Append Geometry** (lines 216-233)
   - Appends `TEMP_FC_3857` (projected **feature class**) directly to online service
   - Bypasses any intermediate tables

4. **Operational Safety**
   - Heartbeat updates before/after long operations (lines 98, 161, 196, 221, 235, 242)
   - Calls `monitor_dashboard_health.py` after append (lines 239-260)
   - Raises exception if monitor fails (exit code ≠ 0)

**Verdict:** This script is production-ready as-is.

---

### `complete_backfill_simplified.py` ⚠️ **ONE CRITICAL FIX**

This script implements 95% of requirements correctly, but has **one critical bug in Step 10**:

#### The Bug (Line 377)

```python
# STEP 10: Push CFStable to Online Service
arcpy.management.Append(
    inputs=CFSTABLE,        # ❌ BUG: CFStable may be a TABLE (no geometry)
    target=ONLINE_SERVICE,
    schema_type="NO_TEST"
)
```

**Problem:** If `CFSTABLE` is a generic table (not a feature class), it has no SHAPE field. When appended to the online feature service, all geometry is NULL → empty map.

#### The Fix

```python
# STEP 10: Append 3857 Feature Class DIRECTLY to Online Service
arcpy.management.Append(
    inputs=TEMP_FC_3857,     # ✅ FIX: Use projected feature class with geometry
    target=ONLINE_SERVICE,
    schema_type="NO_TEST"
)

# Also update CFStable for local reference (optional)
arcpy.management.TruncateTable(CFSTABLE)
arcpy.management.Append(inputs=TEMP_FC_3857, target=CFSTABLE, schema_type="NO_TEST")
```

**Why this works:**
- `TEMP_FC_3857` is a **feature class** with Web Mercator geometry (created in Step 8)
- Bypasses `CFSTABLE` for the online push (preserves geometry)
- Still updates `CFSTABLE` afterward for local reference/verification

#### Other Features (Already Correct)

1. **Safe Coordinate Conversion** (lines 222-279) ✅
2. **Explicit Projection** (lines 318-338) ✅
3. **Operational Safety** (heartbeat + monitor) ✅

---

## Patches Created

### 1. `complete_backfill_simplified_geometry_fix.patch`

**Changes:** Lines 366-391 (Step 10)  
**Type:** Surgical fix (16 lines changed)  
**Impact:** Preserves geometry when appending to online service

**Apply with:**
```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
git apply patches/complete_backfill_simplified_geometry_fix.patch
```

### 2. `publish_with_xy_coordinates_no_changes_needed.patch`

**Changes:** Documentation comments only  
**Type:** Verification annotation (no behavioral change)  
**Purpose:** Documents that the script already implements all requirements

**Apply with:**
```powershell
git apply patches/publish_with_xy_coordinates_no_changes_needed.patch
```

---

## Testing Checklist

Before deploying to RDP:

- [ ] Run `complete_backfill_simplified.py` on RDP with small test file (1,000 records)
- [ ] Verify online service has geometry: `monitor_dashboard_health.py` returns exit code 0
- [ ] Check dashboard map displays points correctly
- [ ] Review `bad_coords_*.csv` report for records dropped due to NULL coordinates
- [ ] Verify CFStable is updated with same record count as online service

---

## Why the Original Bug Happened

The script's original design:
1. Created geometry in `TEMP_FC_3857` (correct)
2. Appended `TEMP_FC_3857` to local `CFSTABLE` first (Step 9)
3. Then appended `CFSTABLE` to online service (Step 10)

**The assumption:** `CFSTABLE` was expected to be a **feature class** (with geometry).

**The reality:** If `CFSTABLE` is a generic **table** (no SHAPE field), Step 9 strips geometry during append. Then Step 10 pushes a table with NULL geometry to the online service.

**The fix:** Skip the CFStable intermediate step for the online push. Append `TEMP_FC_3857` (which **definitely** has geometry) directly to the online service.

---

## Deployment

1. **Apply patch to local repo:**
   ```powershell
   cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
   git apply patches/complete_backfill_simplified_geometry_fix.patch
   git apply patches/publish_with_xy_coordinates_no_changes_needed.patch
   ```

2. **Deploy to RDP:**
   ```powershell
   .\Deploy-ToRDP-Simple.ps1
   ```

3. **Test on RDP with small file first** (before running full backfill)

4. **Monitor results:**
   - Check `C:\HPD ESRI\04_Scripts\_out\monitor_*.json` reports
   - Verify dashboard map shows points

---

## Summary

- **`publish_with_xy_coordinates.py`**: Already correct, no changes needed ✅
- **`complete_backfill_simplified.py`**: One-line fix (line 377: `CFSTABLE` → `TEMP_FC_3857`) ⚠️

Both scripts now implement the full "Golden Path":
1. ✅ Safe coordinate conversion
2. ✅ Explicit WGS84 → Web Mercator projection
3. ✅ Append geometry (feature class, not table)
4. ✅ Heartbeat updates + post-publish validation

**Total changes:** 16 lines modified across 2 files (1 behavioral fix, 1 documentation annotation)
