# check_layer_gap_and_geometry.py
# Purpose: Report data gap (date range, counts by year) and X/Y (geometry) health for CallsForService layer.
# Run on RDP with: propy.bat "C:\HPD ESRI\04_Scripts\check_layer_gap_and_geometry.py"
# Author: R. A. Carucci
# Date: 2026-02-16

import json
import os
import sys
from datetime import datetime

from arcgis.gis import GIS
from arcgis.features import FeatureLayer

DEFAULT_LAYER_URL = "https://services1.arcgis.com/JYl0Hy0wQdiiV0qh/arcgis/rest/services/CallsForService_2153d1ef33a0414291a8eb54b938507b/FeatureServer/0"
OUT_DIR = r"C:\HPD ESRI\04_Scripts\_out"
SAMPLE_SIZE = 1000
YEARS = list(range(2019, 2027))  # 2019..2026


def has_xy(geom):
    if not geom:
        return False
    x = geom.get("x")
    y = geom.get("y")
    return x is not None and y is not None


def main():
    layer_url = DEFAULT_LAYER_URL
    out_dir = OUT_DIR
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        try:
            with open(sys.argv[1], "r", encoding="utf-8") as f:
                cfg = json.load(f)
            layer_url = (
                cfg.get("calls_for_service_layer_url")
                or cfg.get("paths", {}).get("calls_for_service_layer_url")
                or layer_url
            )
            out_dir = (
                cfg.get("monitor_out_dir")
                or cfg.get("paths", {}).get("reports_dir")
                or out_dir
            )
        except Exception:
            pass

    report = {
        "layer_url": layer_url,
        "total_count": None,
        "date_range": {"min": None, "max": None},
        "count_by_year": {},
        "geometry_sample": {"size": SAMPLE_SIZE, "with_xy": 0, "null_geom": 0},
    }

    print("\n" + "=" * 70)
    print("CallsForService: Data Gap & X/Y (Geometry) Check")
    print("=" * 70)
    print(f"Layer: {layer_url}\n")

    try:
        gis = GIS("pro")
        layer = FeatureLayer(layer_url, gis=gis)

        # Total count
        total = layer.query(where="1=1", return_count_only=True)
        report["total_count"] = int(total) if total is not None else None
        print(f"Total records: {report['total_count']}")

        # Date range (try calldate first; fallback to callyear)
        for order_asc in [True, False]:
            try:
                order = "calldate" if order_asc else "calldate DESC"
                fs = layer.query(
                    where="1=1",
                    out_fields="calldate",
                    return_geometry=False,
                    order_by_fields=order,
                    result_record_count=1,
                )
                if fs and fs.features:
                    val = fs.features[0].attributes.get("calldate")
                    if val:
                        key = "min" if order_asc else "max"
                        report["date_range"][key] = str(val)
            except Exception:
                pass
        if report["date_range"]["min"] or report["date_range"]["max"]:
            print(f"Date range: {report['date_range']['min']} to {report['date_range']['max']}")
        else:
            print("Date range: (calldate not available or empty)")

        # Count by year (callyear if available)
        print("\nCount by year:")
        for year in YEARS:
            try:
                c = layer.query(where=f"callyear = {year}", return_count_only=True)
                report["count_by_year"][str(year)] = int(c) if c is not None else 0
                print(f"  {year}: {report['count_by_year'][str(year)]:,}")
            except Exception:
                report["count_by_year"][str(year)] = None
                print(f"  {year}: (query failed)")

        # Geometry sample (X/Y presence)
        print(f"\nGeometry sample (n={SAMPLE_SIZE}):")
        fs = layer.query(
            where="1=1",
            out_fields="OBJECTID",
            return_geometry=True,
            result_record_count=SAMPLE_SIZE,
        )
        feats = fs.features if fs else []
        with_xy = sum(1 for f in feats if has_xy(getattr(f, "geometry", None)))
        null_geom = len(feats) - with_xy
        report["geometry_sample"]["with_xy"] = with_xy
        report["geometry_sample"]["null_geom"] = null_geom
        pct = (with_xy / len(feats) * 100.0) if feats else 0
        print(f"  With X/Y: {with_xy} ({pct:.1f}%)")
        print(f"  Null/missing geometry: {null_geom}")

        # Summary
        print("\n" + "=" * 70)
        if report["total_count"] == 0:
            print("No records in layer.")
        elif null_geom > len(feats) * 0.01:
            print("WARNING: More than 1% of sampled features have NULL geometry (no X/Y).")
        else:
            print("Geometry looks OK (sample has X/Y).")
        print("=" * 70 + "\n")

    except Exception as e:
        report["error"] = str(e)
        print(f"ERROR: {e}")
        raise

    # Write report
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"layer_gap_geometry_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Report: {out_path}")


if __name__ == "__main__":
    main()
