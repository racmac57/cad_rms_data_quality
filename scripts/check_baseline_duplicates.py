#!/usr/bin/env python3
"""
Quick check: total rows vs unique ReportNumberNew in a baseline Excel.
Multiple rows per case is normal (e.g. multiple units/responses per call).
"""

import sys
from pathlib import Path

import pandas as pd

DEFAULT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx")


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    df = pd.read_excel(path, usecols=["ReportNumberNew"])
    total = len(df)
    unique = df["ReportNumberNew"].nunique()
    dup_rows = total - unique
    print(f"File: {path.name}")
    print(f"  Total rows:           {total:,}")
    print(f"  Unique ReportNumberNew: {unique:,}")
    print(f"  Rows with duplicate case ID: {dup_rows:,}")
    if unique > 0:
        print(f"  (Multiple rows per case is normal for CAD data.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
