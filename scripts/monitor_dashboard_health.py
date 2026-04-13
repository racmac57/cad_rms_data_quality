# monitor_dashboard_health.py
# Created: 2026-02-15
# Purpose: Validate CallsForService hosted layer health (count, WKID, geometry presence)
# Author: R. A. Carucci
#
# Post-publish validation gate: Ensures geometry and spatial reference are correct
# before allowing publish workflow to complete successfully.
#
# Exit codes:
#   0 = OK (all checks passed)
#   2 = Geometry check failed (>1% missing geometry)
#   3 = WKID mismatch (not 3857 or 102100)
#   4 = Query/connection failure

import json
import os
import sys
import datetime as _dt  # Use module ref to avoid shadowing by ArcGIS/deps

# ArcGIS API for Python (import after datetime to avoid namespace issues)
from arcgis.gis import GIS
from arcgis.features import FeatureLayer


# ----------------------------
# CONFIG DEFAULTS (can override via args or config.json)
# ----------------------------
DEFAULT_LAYER_URL = "https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0"
EXPECTED_WKIDS_OK = {3857, 102100}  # accept either as Web Mercator Aux Sphere
SAMPLE_SIZE = 1000
MAX_NULL_GEOM_PCT = 1.0  # fail if >1% of sample has missing geometry

# Where to write JSON reports on the RDP server
DEFAULT_OUT_DIR = r"C:\HPD ESRI\04_Scripts\_out"


def safe_int(v):
    """Convert value to int safely, return None on failure."""
    try:
        return int(v)
    except Exception:
        return None


def load_config_if_present(config_path: str) -> dict:
    """Load config.json if path provided, return empty dict on error."""
    if not config_path:
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_layer_wkid(layer: FeatureLayer):
    """Extract WKID from layer properties, try common locations."""
    props = layer.properties
    for path in [
        ("spatialReference", "wkid"),
        ("extent", "spatialReference", "wkid"),
    ]:
        try:
            cur = props
            for k in path:
                cur = cur.get(k)
            wkid = safe_int(cur)
            if wkid:
                return wkid
        except Exception:
            pass
    return None


def is_missing_point_geometry(geom: dict) -> bool:
    """Check if point geometry is NULL/missing (no x/y coordinates)."""
    if not geom:
        return True
    # For point geometry, expect x/y
    x = geom.get("x", None)
    y = geom.get("y", None)
    return x is None or y is None


def ensure_dir(p: str):
    """Create directory if it doesn't exist."""
    os.makedirs(p, exist_ok=True)


def write_report(out_dir: str, report: dict) -> str:
    """Write JSON report with timestamp, return output path."""
    ensure_dir(out_dir)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"monitor_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return out_path


def main():
    # Optional arg: config path (so PS1 can pass $ConfigPath)
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    cfg = load_config_if_present(config_path)

    # Load settings (config overrides defaults)
    layer_url = (
        cfg.get("calls_for_service_layer_url")
        or cfg.get("paths", {}).get("calls_for_service_layer_url")
        or DEFAULT_LAYER_URL
    )

    out_dir = (
        cfg.get("monitor_out_dir")
        or cfg.get("paths", {}).get("reports_dir")
        or DEFAULT_OUT_DIR
    )

    expected_wkids = set(cfg.get("expected_wkids_ok", [])) or EXPECTED_WKIDS_OK
    sample_size = int(cfg.get("monitor_sample_size", SAMPLE_SIZE))
    max_null_pct = float(cfg.get("monitor_max_null_geom_pct", MAX_NULL_GEOM_PCT))

    # Initialize report
    report = {
        "timestamp_est": _dt.datetime.now().isoformat(),
        "layer_url": layer_url,
        "expected_wkids_ok": sorted(list(expected_wkids)),
        "sample_size": sample_size,
        "max_null_geom_pct": max_null_pct,
        "status": "started",
    }

    print(f"\n{'='*70}")
    print("CallsForService Dashboard Health Monitor")
    print(f"{'='*70}")
    print(f"Layer URL: {layer_url}")
    print(f"Sample size: {sample_size}")
    print(f"Max null geometry allowed: {max_null_pct}%")
    print(f"Expected WKIDs: {sorted(expected_wkids)}")
    print("")

    try:
        # Connect to ArcGIS Pro
        print("Connecting to ArcGIS Pro...")
        try:
            gis = GIS("pro")
            print("[OK] Connected via GIS('pro')")
        except Exception as e:
            print(f"[WARN] GIS('pro') failed: {e}")
            print("Trying GIS('home') fallback...")
            gis = GIS("home")
            print("[OK] Connected via GIS('home')")

        # Get layer
        print(f"\nQuerying layer...")
        layer = FeatureLayer(layer_url, gis=gis)

        # Check 1: Total record count
        print("  Checking record count...")
        total = layer.query(where="1=1", return_count_only=True)
        report["total_count"] = int(total) if total is not None else None
        print(f"  [OK] Total records: {report['total_count']}")

        # Check 2: WKID
        print("  Checking spatial reference (WKID)...")
        wkid = get_layer_wkid(layer)
        report["wkid"] = wkid
        print(f"  [OK] WKID: {wkid}")

        # Check 3: Sample geometry presence
        print(f"  Sampling {sample_size} features for geometry check...")
        fs = layer.query(
            where="1=1",
            out_fields="OBJECTID",
            return_geometry=True,
            result_record_count=sample_size,
        )

        feats = fs.features if fs else []
        effective_sample = len(feats)
        report["effective_sample"] = effective_sample
        print(f"  [OK] Retrieved {effective_sample} features")

        # Count missing geometry
        null_geom = 0
        for f in feats:
            geom = getattr(f, "geometry", None)
            if is_missing_point_geometry(geom):
                null_geom += 1

        null_pct = (null_geom / effective_sample * 100.0) if effective_sample else 100.0
        report["null_geom_count"] = null_geom
        report["null_geom_pct"] = round(null_pct, 3)
        print(f"  [OK] Null geometry: {null_geom}/{effective_sample} ({null_pct:.2f}%)")

        # Decision logic
        print("\nValidation Results:")
        print(f"{'='*70}")
        
        if wkid is None or wkid not in expected_wkids:
            report["status"] = "fail_wkid"
            report["exit_code"] = 3
            print(f"[FAIL] WKID mismatch: got {wkid}, expected {sorted(expected_wkids)}")
            print(f"Exit code: 3")
        elif null_pct > max_null_pct:
            report["status"] = "fail_geometry"
            report["exit_code"] = 2
            print(f"[FAIL] Geometry check failed: {null_pct:.2f}% missing (max allowed: {max_null_pct}%)")
            print(f"Exit code: 2")
        else:
            report["status"] = "ok"
            report["exit_code"] = 0
            print(f"[OK] All checks passed")
            print(f"  - WKID: {wkid} (valid)")
            print(f"  - Geometry: {null_pct:.2f}% missing (within {max_null_pct}% threshold)")
            print(f"Exit code: 0")

    except Exception as e:
        report["status"] = "fail_exception"
        report["error"] = str(e)
        report["exit_code"] = 4
        print(f"\n[ERROR] Exception during validation:")
        print(f"  {str(e)}")
        print(f"Exit code: 4")

    # Write report
    print(f"\n{'='*70}")
    out_path = write_report(out_dir, report)
    print(f"Report written: {out_path}")
    print(f"{'='*70}\n")

    # Exit with appropriate code
    exit_code = int(report["exit_code"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
