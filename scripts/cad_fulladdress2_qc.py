"""
cad_fulladdress2_qc.py
Purpose
- Audit FullAddress2 quality for Esri geocoding readiness
- Group and rank error types for batch correction
- Run a temporal continuity check (missing days, low volume days)

Inputs
- Excel or CSV with at least these fields:
  - FullAddress2
  - Time_Of_Call

Outputs (written to OUT_DIR)
- address_qc_error_groups.csv
- address_qc_top_values_by_error.csv
- temporal_qc_daily_counts.csv
- temporal_qc_missing_days.csv
- temporal_qc_low_volume_days.csv
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


# -----------------------
# USER SETTINGS
# -----------------------
INPUT_PATH = r"C:\path\to\CAD_ESRI_Polished_Baseline_20190101_20260203.xlsx"
INPUT_TYPE = "excel"  # "excel" or "csv"
SHEET_NAME = "Sheet1"  # excel only

ADDRESS_COL = "FullAddress2"
DATETIME_COL = "Time_Of_Call"

START_DATE = "2019-01-01"
LOW_VOLUME_THRESHOLD = 50

# CSV chunk size (ignored for excel)
CHUNK_SIZE = 250_000

# Example limit per error type
TOP_VALUES_PER_ERROR = 50

# HQ proxy used for suppressed home lunch events
HQ_PROXY_LIST = [
    "225 STATE ST, HACKENSACK, NJ, 07601",
    "225 STATE STREET, HACKENSACK, NJ, 07601",
    "225 STATE ST HACKENSACK NJ 07601",
    "225 STATE STREET HACKENSACK NJ 07601",
]

OUT_DIR = Path(r"C:\path\to\qc_outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------
# REGEX (heuristics)
# -----------------------
RE_ZIP = re.compile(r"\b\d{5}(?:-\d{4})?\b")
RE_CITY_STATE = re.compile(r",\s*[A-Za-z][A-Za-z \.\-']+\s*,\s*[A-Z]{2}\b")
RE_STATE = re.compile(r"\b[A-Z]{2}\b")
RE_HOUSENUM = re.compile(r"^\s*\d+[A-Z]?\b")
RE_POBOX = re.compile(r"\bP\.?\s*O\.?\s*BOX\b|\bPO\s*BOX\b", re.IGNORECASE)

# Intersections: accepts both "&" and "and"
RE_INTERSECTION = re.compile(r"\b.+\s+(&|and)\s+.+\b", re.IGNORECASE)


def normalize_addr_series(s: pd.Series) -> pd.Series:
    out = s.astype("string").fillna("").str.strip()
    out = out.str.replace(r"\s+", " ", regex=True)
    return out


def classify_addresses(addr: pd.Series) -> pd.Series:
    a = normalize_addr_series(addr)
    upper = a.str.upper()

    is_blank = a.eq("")
    is_pobox = a.str.contains(RE_POBOX, na=False)

    # HQ proxy detection
    hq_upper = set([x.upper() for x in HQ_PROXY_LIST])
    is_hq_proxy = upper.isin(hq_upper)

    has_zip = a.str.contains(RE_ZIP, na=False)
    has_city_state = a.str.contains(RE_CITY_STATE, na=False)
    has_state = a.str.contains(RE_STATE, na=False)
    has_housenum = a.str.contains(RE_HOUSENUM, na=False)
    is_intersection = a.str.contains(RE_INTERSECTION, na=False)

    miss_zip = ~has_zip
    miss_city_state = ~has_city_state

    # Note
    # City/state detection uses commas: "..., City, ST ..."
    # If you store "City ST" without commas, add a second pattern.

    out = np.select(
        [
            is_blank,
            is_pobox,
            is_hq_proxy,
            is_intersection & ~has_state,
            is_intersection & has_state,
            ~is_intersection & ~has_housenum,
            ~is_intersection & has_housenum & miss_city_state,
            ~is_intersection & has_housenum & ~miss_city_state & miss_zip,
        ],
        [
            "NULL_OR_BLANK",
            "PO_BOX",
            "SUPPRESSED_HOME_PROXY_HQ",
            "INTERSECTION_MISSING_STATE",
            "OK_INTERSECTION",
            "MISSING_HOUSENUM",
            "MISSING_CITY_STATE",
            "MISSING_ZIP",
        ],
        default="OK_STANDARD",
    )

    return pd.Series(out, index=addr.index, dtype="string")


def read_iter() -> pd.DataFrame:
    if INPUT_TYPE.lower() == "csv":
        for chunk in pd.read_csv(
            INPUT_PATH,
            usecols=[ADDRESS_COL, DATETIME_COL],
            dtype={ADDRESS_COL: "string"},
            chunksize=CHUNK_SIZE,
            low_memory=True,
        ):
            yield chunk
        return

    if INPUT_TYPE.lower() == "excel":
        df = pd.read_excel(INPUT_PATH, sheet_name=SHEET_NAME, usecols=[ADDRESS_COL, DATETIME_COL])
        yield df
        return

    raise ValueError("INPUT_TYPE must be 'csv' or 'excel'")


def main() -> None:
    error_counts: Dict[str, int] = {}
    top_values: Dict[str, Dict[str, int]] = {}
    day_counts: Dict[pd.Timestamp, int] = {}

    total_rows = 0

    for chunk in read_iter():
        total_rows += len(chunk)

        # Temporal
        dtv = pd.to_datetime(chunk[DATETIME_COL], errors="coerce")
        day = dtv.dt.floor("D")

        vc_day = day.value_counts(dropna=True)
        for k, v in vc_day.items():
            day_counts[k] = day_counts.get(k, 0) + int(v)

        # Address QC
        etype = classify_addresses(chunk[ADDRESS_COL])
        vc_err = etype.value_counts(dropna=False)

        for k, v in vc_err.items():
            error_counts[k] = error_counts.get(k, 0) + int(v)

        # Top values per error type (ranked)
        tmp = pd.DataFrame(
            {
                "etype": etype,
                "addr": normalize_addr_series(chunk[ADDRESS_COL]).str.upper(),
            }
        )

        for k in vc_err.index.tolist():
            if k.startswith("OK_"):
                continue

            if k not in top_values:
                top_values[k] = {}

            vc_vals = tmp.loc[tmp["etype"].eq(k), "addr"].value_counts(dropna=False)

            for addr_val, cnt in vc_vals.items():
                if addr_val == "":
                    continue
                top_values[k][addr_val] = top_values[k].get(addr_val, 0) + int(cnt)

    # Output 1: error groups
    df_groups = (
        pd.DataFrame({"ErrorType": list(error_counts.keys()), "Count": list(error_counts.values())})
        .sort_values(["Count", "ErrorType"], ascending=[False, True])
        .reset_index(drop=True)
    )
    df_groups.to_csv(OUT_DIR / "address_qc_error_groups.csv", index=False)

    # Output 2: ranked top address strings per error type
    rows: List[Dict[str, object]] = []
    for et, d in top_values.items():
        ranked = sorted(d.items(), key=lambda x: x[1], reverse=True)[:TOP_VALUES_PER_ERROR]
        for addr_val, cnt in ranked:
            rows.append({"ErrorType": et, "Count": cnt, "AddressValue": addr_val})
    pd.DataFrame(rows).to_csv(OUT_DIR / "address_qc_top_values_by_error.csv", index=False)

    # Temporal continuity outputs
    if len(day_counts) == 0:
        raise RuntimeError("No valid dates parsed from DATETIME_COL")

    min_day = pd.to_datetime(START_DATE)
    max_day = max(day_counts.keys())
    ref = pd.date_range(min_day, max_day, freq="D")

    df_daily = pd.DataFrame({"Date": ref})
    df_daily["Count"] = df_daily["Date"].map(day_counts).fillna(0).astype(int)

    df_daily.to_csv(OUT_DIR / "temporal_qc_daily_counts.csv", index=False)

    df_missing = df_daily.loc[df_daily["Count"].eq(0)].copy()
    df_missing.to_csv(OUT_DIR / "temporal_qc_missing_days.csv", index=False)

    df_low = df_daily.loc[(df_daily["Count"].gt(0)) & (df_daily["Count"].lt(LOW_VOLUME_THRESHOLD))].copy()
    df_low.to_csv(OUT_DIR / "temporal_qc_low_volume_days.csv", index=False)

    # Console summary
    print("Rows scanned:", total_rows)
    print("Max date:", max_day.date())
    print("Missing days:", len(df_missing))
    print("Low volume days (<{}):".format(LOW_VOLUME_THRESHOLD), len(df_low))
    print("Output folder:", str(OUT_DIR))


if __name__ == "__main__":
    main()
