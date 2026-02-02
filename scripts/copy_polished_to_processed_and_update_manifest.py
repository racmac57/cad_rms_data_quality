#!/usr/bin/env python3
"""
Copy latest CAD ESRI polished file to 13_PROCESSED_DATA and update manifest.json.

Use after:
  1. Running consolidate_cad_2019_2026.py (incremental or full)
  2. Running CAD_Data_Cleaning_Engine (enhanced_esri_output_generator.py)

This script copies the polished Excel from the cleaning engine output (or a given path)
to 13_PROCESSED_DATA/ESRI_Polished/incremental/YYYY_MM_DD_append/ and updates
manifest.json so copy_consolidated_dataset_to_server.ps1 and ArcGIS workflow use the new file.

Usage:
  python scripts/copy_polished_to_processed_and_update_manifest.py
  python scripts/copy_polished_to_processed_and_update_manifest.py --source "C:\path\to\CAD_ESRI_POLISHED_*.xlsx"
  python scripts/copy_polished_to_processed_and_update_manifest.py --dry-run

Author: R. A. Carucci
Date: 2026-02-02
"""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "consolidation_sources.yaml"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Default: latest .xlsx in CAD_Data_Cleaning_Engine/data/03_final
CLEANING_ENGINE_03_FINAL = Path(
    r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final"
)
PROCESSED_ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA")
MANIFEST_PATH = PROCESSED_ROOT / "manifest.json"
INCREMENTAL_DIR = PROCESSED_ROOT / "ESRI_Polished" / "incremental"


def load_config():
    if not CONFIG_PATH.exists():
        return {}
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
        return {}


def find_latest_polished(source_path: Path = None) -> Path:
    """Return path to polished Excel: from argument or latest in 03_final."""
    if source_path and source_path.exists():
        return source_path
    if not CLEANING_ENGINE_03_FINAL.exists():
        raise FileNotFoundError(
            f"Cleaning engine output dir not found: {CLEANING_ENGINE_03_FINAL}"
        )
    xlsx_files = list(CLEANING_ENGINE_03_FINAL.glob("*.xlsx"))
    if not xlsx_files:
        raise FileNotFoundError(
            f"No .xlsx files in {CLEANING_ENGINE_03_FINAL}"
        )
    # Most recently modified
    latest = max(xlsx_files, key=lambda p: p.stat().st_mtime)
    return latest


def get_excel_metrics(file_path: Path) -> dict:
    """Read record count, unique cases, and date range from polished Excel (one read)."""
    date_start = "2019-01-01"
    date_end = "2026-01-30"
    record_count = 0
    unique_cases = 0
    try:
        # One read: get header to pick time/id columns, then read only those columns
        head = pd.read_excel(file_path, engine="openpyxl", nrows=0)
        time_col = None
        for c in ["Time of Call", "TimeOfCall"]:
            if c in head.columns:
                time_col = c
                break
        id_col = "ReportNumberNew" if "ReportNumberNew" in head.columns else "Report Number New"
        if id_col not in head.columns:
            id_col = head.columns[0]  # fallback
        cols = [c for c in [time_col, id_col] if c and c in head.columns]
        if not cols:
            cols = list(head.columns[:2])
        df = pd.read_excel(file_path, engine="openpyxl", usecols=cols)
        record_count = len(df)
        if id_col in df.columns:
            unique_cases = int(df[id_col].dropna().nunique())
        else:
            unique_cases = record_count
        if time_col and time_col in df.columns:
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
            valid = df[time_col].dropna()
            if len(valid) > 0:
                date_start = str(valid.min().date())
                date_end = str(valid.max().date())
    except Exception as e:
        logger.warning("Could not read Excel metrics: %s", e)
    return {
        "record_count": record_count,
        "unique_cases": unique_cases,
        "date_range": {"start": date_start, "end": date_end},
    }


def ensure_processed_dirs():
    INCREMENTAL_DIR.mkdir(parents=True, exist_ok=True)


def run_copy_and_manifest(source_path: Path = None, dry_run: bool = False):
    source = find_latest_polished(source_path)
    logger.info("Source polished file: %s", source)

    metrics = get_excel_metrics(source)
    logger.info(
        "  Records: %s, Unique cases: %s, Date range: %s to %s",
        metrics["record_count"],
        metrics["unique_cases"],
        metrics["date_range"]["start"],
        metrics["date_range"]["end"],
    )

    run_date = datetime.now().strftime("%Y_%m_%d")
    folder_name = f"{run_date}_append"
    dest_dir = INCREMENTAL_DIR / folder_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / source.name

    if dry_run:
        logger.info("[DRY RUN] Would copy to: %s", dest_file)
        logger.info("[DRY RUN] Would update manifest.json")
        return

    ensure_processed_dirs()
    shutil.copy2(source, dest_file)
    logger.info("Copied to: %s", dest_file)

    # Update manifest
    rel_path = f"ESRI_Polished/incremental/{folder_name}/{dest_file.name}"
    full_path = str(dest_file.resolve())
    new_latest = {
        "path": rel_path,
        "full_path": full_path,
        "date_range": metrics["date_range"],
        "record_count": metrics["record_count"],
        "unique_cases": metrics["unique_cases"],
        "file_size_bytes": dest_file.stat().st_size,
        "checksum_sha256": None,
        "run_type": "incremental",
        "created": datetime.now().isoformat(),
    }

    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {
            "schema_version": "1.0",
            "last_updated": None,
            "description": "Registry of CAD ESRI polished datasets for ArcGIS Pro import",
            "latest": None,
            "baseline": {},
            "history": [],
            "directories": {
                "base": "ESRI_Polished/base",
                "incremental": "ESRI_Polished/incremental",
                "full_rebuild": "ESRI_Polished/full_rebuild",
                "archive": "archive",
            },
        }

    manifest["latest"] = new_latest
    manifest["last_updated"] = datetime.now().isoformat()
    if "history" not in manifest:
        manifest["history"] = []
    manifest["history"].append({
        "path": rel_path,
        "date": run_date,
        "run_type": "incremental",
        "record_count": metrics["record_count"],
        "notes": f"Incremental append run {run_date}",
    })

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info("Updated manifest: %s", MANIFEST_PATH)
    logger.info("Latest file: %s", rel_path)


def main():
    parser = argparse.ArgumentParser(
        description="Copy polished CAD dataset to 13_PROCESSED_DATA and update manifest"
    )
    parser.add_argument(
        "--source", "-s",
        type=Path,
        default=None,
        help="Path to polished Excel (default: latest in CAD_Data_Cleaning_Engine/data/03_final)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not copy or write manifest")
    args = parser.parse_args()
    try:
        run_copy_and_manifest(source_path=args.source, dry_run=args.dry_run)
    except Exception as e:
        logger.error("%s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
