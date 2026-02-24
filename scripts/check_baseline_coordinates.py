#!/usr/bin/env python3
"""
Check that baseline (or any CAD Excel) has x/y (latitude/longitude or X_Coord/Y_Coord)
and report how many records have valid coordinates.

Usage:
  python scripts/check_baseline_coordinates.py
  python scripts/check_baseline_coordinates.py --baseline "path/to/file.xlsx"
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

PROCESSED_DATA_ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA")
DEFAULT_BASELINE = PROCESSED_DATA_ROOT / "ESRI_Polished" / "base" / "CAD_ESRI_Polished_Baseline.xlsx"


def main():
    parser = argparse.ArgumentParser(description="Report x/y (coordinate) presence in baseline Excel")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE, help="Path to baseline Excel")
    args = parser.parse_args()

    if not args.baseline.exists():
        print(f"[X] File not found: {args.baseline}", file=sys.stderr)
        return 1

    # Determine which columns exist
    cols = pd.read_excel(args.baseline, nrows=0).columns.tolist()
    has_lat_lon = "latitude" in cols and "longitude" in cols
    has_xy = "X_Coord" in cols and "Y_Coord" in cols

    if not has_lat_lon and not has_xy:
        print("[X] No coordinate columns found. Expected 'latitude'/'longitude' or 'X_Coord'/'Y_Coord'.")
        print(f"    Columns: {cols}")
        return 1

    if has_lat_lon:
        x_label, y_label = "longitude", "latitude"
    else:
        x_label, y_label = "X_Coord", "Y_Coord"
    use_cols = [c for c in [x_label, y_label] if c in cols]
    if len(use_cols) != 2:
        print("[X] Coordinate columns missing.", file=sys.stderr)
        return 1

    # Read only needed columns (minimal for speed)
    df = pd.read_excel(args.baseline, usecols=use_cols)
    total = len(df)

    # Numeric and non-null
    for c in [x_label, y_label]:
        if df[c].dtype == object:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    both = df[x_label].notna() & df[y_label].notna()
    valid = both & (df[x_label].astype(float).between(-180, 180)) & (df[y_label].astype(float).between(-90, 90))
    with_coords = valid.sum()
    missing = total - with_coords

    print(f"\nBaseline: {args.baseline.name}")
    print(f"Coordinate columns: {x_label}, {y_label}")
    print(f"Total records:     {total:,}")
    print(f"With valid x/y:    {with_coords:,} ({100 * with_coords / total:.2f}%)")
    print(f"Missing/invalid:   {missing:,}")
    print()
    if with_coords == total:
        print("[OK] All records have x/y.")
    elif with_coords > 0:
        print("[OK] Records with correct location data have x and y.")
    else:
        print("[X] No records have valid coordinates.")
        print("    Tip: This file may be a polished baseline without coordinates.")
        print("    For backfill with points, use a source that has latitude/longitude")
        print("    (e.g. CAD export Excel or geocoded cache with X_Coord/Y_Coord).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
