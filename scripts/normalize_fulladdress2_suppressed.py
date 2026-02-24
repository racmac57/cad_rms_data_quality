#!/usr/bin/env python3
"""
Normalize FullAddress2: replace suppressed/home proxy values with
225 State Street, Hackensack, NJ, 07601.

Reads baseline Excel, replaces exact matches (after strip), writes to a new file
unless --in-place (then overwrites with backup).

Usage:
  python scripts/normalize_fulladdress2_suppressed.py --dry-run
  python scripts/normalize_fulladdress2_suppressed.py --output "path/to/output.xlsx"
  python scripts/normalize_fulladdress2_suppressed.py --in-place
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

PROCESSED_DATA_ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA")
DEFAULT_BASELINE = PROCESSED_DATA_ROOT / "ESRI_Polished" / "base" / "CAD_ESRI_Polished_Baseline.xlsx"
REPLACEMENT = "225 State Street, Hackensack, NJ, 07601"

# Exact values to replace (after stripping). One per line.
ADDRESSES_TO_REPLACE = [
    "home & , Hackensack, NJ, 07601",
    "Home  & , Hackensack, NJ, 07601",
    "357 Home, Hackensack, NJ, 07601",
    "HOME. & , Hackensack, NJ, 07601",
    "Home   & , Hackensack, NJ, 07601",
    "Home Home, Hackensack, NJ, 07601",
    "225 Home, Hackensack, NJ, 07601",
    "50 Home, Hackensack, NJ, 07601",
    "Home",
    " & , Hackensack, NJ, 07601",
    "Home & Railroad Avenue North, Hackensack, NJ, 07601",
    "3 home, Hackensack, NJ, 07601",
    "Home & State St / Banta Pl, Hackensack, NJ, 07601",
    "home & home, Hackensack, NJ, 07601",
    "home & State Street, Hackensack, NJ, 07601",
    "home & Temple Avenue, Hackensack, NJ, 07601",
    "Home  & home, Hackensack, NJ, 07601",
    "123 Home, Hackensack, NJ, 07601",
    "home & Central Avenue, Hackensack, NJ, 07601",
    "Home & Home , Hackensack, NJ, 07601",
]


def main():
    parser = argparse.ArgumentParser(description="Replace suppressed FullAddress2 values with 225 State Street")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE, help="Input baseline Excel")
    parser.add_argument("--output", type=Path, help="Output Excel path (default: baseline with _normalized suffix)")
    parser.add_argument("--in-place", action="store_true", help="Overwrite baseline (create backup first)")
    parser.add_argument("--dry-run", action="store_true", help="Only report what would be changed")
    args = parser.parse_args()

    if not args.baseline.exists():
        print(f"[X] File not found: {args.baseline}", file=sys.stderr)
        return 1

    # Normalize lookup set (strip for match)
    replace_set = {s.strip() for s in ADDRESSES_TO_REPLACE if s.strip()}

    df = pd.read_excel(args.baseline)
    if "FullAddress2" not in df.columns:
        print("[X] No column 'FullAddress2' in file.", file=sys.stderr)
        return 1

    # String column, strip for comparison
    addr = df["FullAddress2"].astype("string").fillna("")
    stripped = addr.str.strip()
    mask = stripped.isin(replace_set)
    count = mask.sum()

    print(f"\nBaseline: {args.baseline.name}")
    print(f"Records to change (exact match): {count:,}")
    if count > 0:
        print(f"Replacement: \"{REPLACEMENT}\"")
        print("\nValues being replaced:")
        for v in sorted(stripped[mask].unique()):
            n = (stripped == v).sum()
            print(f"  [{n:,}] {v!r}")

    if args.dry_run:
        print("\n[DRY RUN] No file written.")
        return 0

    if count == 0:
        print("\nNo changes needed.")
        return 0

    df = df.copy()
    df.loc[mask, "FullAddress2"] = REPLACEMENT

    if args.in_place:
        backup = args.baseline.parent / f"{args.baseline.stem}_backup_before_normalize.xlsx"
        import shutil
        shutil.copy2(args.baseline, backup)
        print(f"\nBackup: {backup}")
        out_path = args.baseline
    else:
        out_path = args.output or args.baseline.parent / f"{args.baseline.stem}_normalized.xlsx"
        out_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_excel(out_path, index=False)
    print(f"Written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
