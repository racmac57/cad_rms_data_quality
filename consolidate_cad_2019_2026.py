#!/usr/bin/env python3
"""
CAD Data Consolidation Script (2019 to 2026-01-30)
Prepares input for CAD_Data_Cleaning_Engine pipeline

This script consolidates:
- 7 yearly CAD files (2019-2025)
- 1 monthly file (2026-01-01 to 2026-01-30)

Performance Optimizations (v1.2.3):
- Parallel Excel loading with ThreadPoolExecutor
- Chunked reading for large files (>50MB)
- Memory-efficient dtype optimization
- Baseline + incremental append mode

Output: Single CSV file ready for RMS backfill and ESRI export processing

Reports are written to: consolidation/reports/YYYY_MM_DD_consolidation/

Author: R. A. Carucci
Date: 2026-01-30
Updated: 2026-02-01 - Reports reorganization (Milestone 2)
Updated: 2026-02-01 - Speed optimizations (Milestone 4)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import sys
import json
import yaml
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/consolidate_2019_2026.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
CAD_ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD")
OUTPUT_PATH = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\01_raw")
CLEANING_ENGINE_ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine")
CONFIG_PATH = Path("config/consolidation_sources.yaml")

# Source files configuration (fallback if config not loaded)
YEARLY_FILES = [
    ("yearly/2019/2019_CAD_ALL.xlsx", 2019, 91217),
    ("yearly/2020/2020_CAD_ALL.xlsx", 2020, 89400),
    ("yearly/2021/2021_CAD_ALL.xlsx", 2021, 91477),
    ("yearly/2022/2022_CAD_ALL.xlsx", 2022, 105038),
    ("yearly/2023/2023_CAD_ALL.xlsx", 2023, 113179),
    ("yearly/2024/2024_CAD_ALL.xlsx", 2024, 110313),
    ("yearly/2025/2025_CAD_ALL.xlsx", 2025, 114065),
]

# MONTHLY_FILE = ("monthly/2026/2026_01_01_to_2026_01_30_CAD_Export.xlsx", 2026, None)
# NOTE: Monthly files now loaded from config (2026_01_CAD.xlsx, 2026_02_CAD.xlsx)

# Date range filter
START_DATE = pd.Timestamp("2019-01-01")
END_DATE = pd.Timestamp("2026-02-28 23:59:59")  # Extended to include all of February 2026


# ============================================================================
# CONFIGURATION LOADING
# ============================================================================

def load_config(config_path: Path = CONFIG_PATH) -> Dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to YAML config file

    Returns:
        Configuration dictionary
    """
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"[OK] Loaded config: {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


# ============================================================================
# DIRECTORY SETUP
# ============================================================================

def create_directories():
    """Ensure required directories exist"""
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    logger.info(f"[OK] Output directory ready: {OUTPUT_PATH}")


def get_report_directory(run_type: str = "consolidation") -> Path:
    """
    Generate run-specific report directory with timestamp.

    Args:
        run_type: "consolidation", "incremental", or "full"

    Returns:
        Path to report directory (created if not exists)
    """
    timestamp = datetime.now().strftime("%Y_%m_%d")
    report_dir = Path(f"consolidation/reports/{timestamp}_{run_type}")
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def update_latest_pointer(report_dir: Path, metrics: dict):
    """
    Update latest.json to point to current run.

    Args:
        report_dir: Path to current run's report directory
        metrics: Dictionary with run metrics (record_count, date_range, etc.)
    """
    latest_file = Path("consolidation/reports/latest.json")
    latest_data = {
        "latest_run": str(report_dir.name),
        "timestamp": datetime.now().isoformat(),
        "path": str(report_dir),
        "record_count": metrics.get("record_count"),
        "unique_cases": metrics.get("unique_cases"),
        "date_range": metrics.get("date_range"),
        "output_file": metrics.get("output_file"),
        "mode": metrics.get("mode", "full")
    }
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(latest_data, f, indent=2)
    logger.info(f"[OK] Updated latest.json -> {report_dir.name}")


# ============================================================================
# MEMORY OPTIMIZATION
# ============================================================================

def optimize_dtypes(df: pd.DataFrame, config: Dict = None) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting types.

    Typical memory reduction: 40-60% for CAD datasets.

    Args:
        df: Input DataFrame
        config: Configuration dictionary with memory_optimization settings

    Returns:
        Optimized DataFrame
    """
    if config is None:
        config = {}

    perf_config = config.get('performance', {}).get('memory_optimization', {})
    use_categories = perf_config.get('use_categories', True)
    downcast_numeric = perf_config.get('downcast_numeric', True)

    mem_before = df.memory_usage(deep=True).sum() / 1024**2
    logger.info(f"  Memory before optimization: {mem_before:.1f} MB")

    for col in df.columns:
        col_type = df[col].dtype

        # Downcast integers
        if downcast_numeric and col_type in ['int64', 'int32']:
            df[col] = pd.to_numeric(df[col], downcast='integer')

        # Downcast floats
        elif downcast_numeric and col_type in ['float64']:
            df[col] = pd.to_numeric(df[col], downcast='float')

        # Convert low-cardinality strings to categorical
        elif use_categories and col_type == 'object':
            num_unique = df[col].nunique()
            num_total = len(df[col])

            # If less than 5% unique values, convert to categorical
            if num_total > 0 and num_unique / num_total < 0.05:
                df[col] = df[col].astype('category')

    mem_after = df.memory_usage(deep=True).sum() / 1024**2
    reduction = (1 - mem_after / mem_before) * 100 if mem_before > 0 else 0
    logger.info(f"  Memory after optimization: {mem_after:.1f} MB ({reduction:.1f}% reduction)")

    return df


# ============================================================================
# CHUNKED READING FOR LARGE FILES
# ============================================================================

def load_excel_chunked(file_path: Path, chunk_size: int = 100000) -> pd.DataFrame:
    """
    Load large Excel files in chunks to reduce memory pressure.
    Uses openpyxl read_only mode for better performance.

    Args:
        file_path: Path to Excel file
        chunk_size: Number of rows per chunk

    Returns:
        Complete DataFrame
    """
    from openpyxl import load_workbook

    # Check file size - only use chunked for large files
    file_size_mb = file_path.stat().st_size / (1024 * 1024)

    if file_size_mb < 50:
        # Small file - use standard read
        return pd.read_excel(file_path, engine='openpyxl')

    logger.info(f"  Using chunked read for {file_size_mb:.1f} MB file")

    # Use read_only mode for large files
    wb = load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active

    # Get headers from first row
    rows_iter = ws.rows
    header_row = next(rows_iter)
    headers = [cell.value for cell in header_row]

    chunks = []
    chunk_rows = []

    for row in rows_iter:
        chunk_rows.append([cell.value for cell in row])

        if len(chunk_rows) >= chunk_size:
            chunk_df = pd.DataFrame(chunk_rows, columns=headers)
            chunks.append(chunk_df)
            logger.info(f"    Processed chunk {len(chunks)}: {len(chunk_df):,} rows")
            chunk_rows = []

    # Final chunk
    if chunk_rows:
        chunk_df = pd.DataFrame(chunk_rows, columns=headers)
        chunks.append(chunk_df)

    wb.close()

    result = pd.concat(chunks, ignore_index=True)
    logger.info(f"  Chunked load complete: {len(result):,} total rows")
    return result


# ============================================================================
# FILE LOADING (SINGLE FILE)
# ============================================================================

def load_excel_file(file_path: Path, year: int, expected_count: int = None,
                    config: Dict = None) -> pd.DataFrame:
    """
    Load Excel file with error handling and validation.

    Args:
        file_path: Path to Excel file
        year: Year for this file
        expected_count: Expected record count (for verification)
        config: Configuration dictionary

    Returns:
        DataFrame with loaded data
    """
    logger.info(f"Loading {year}: {file_path.name}")

    if not file_path.exists():
        logger.error(f"[ERROR] File not found: {file_path}")
        raise FileNotFoundError(f"Missing file: {file_path}")

    try:
        # Check file size for chunked reading decision
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"  Size: {file_size_mb:.1f} MB")

        # Get chunked reading settings from config
        perf_config = (config or {}).get('performance', {}).get('chunked_reading', {})
        threshold_mb = perf_config.get('threshold_mb', 50)
        chunk_size = perf_config.get('chunk_size', 100000)
        use_chunked = perf_config.get('enabled', True) and file_size_mb >= threshold_mb

        # Load Excel file (chunked or standard)
        if use_chunked:
            df = load_excel_chunked(file_path, chunk_size)
        else:
            df = pd.read_excel(file_path, engine='openpyxl')

        logger.info(f"  Rows: {len(df):,}")
        logger.info(f"  Columns: {len(df.columns)}")

        # Verify expected count
        if expected_count:
            deviation = abs(len(df) - expected_count) / expected_count * 100
            if deviation > 5:
                logger.warning(f"  [WARN] Record count deviation: {deviation:.1f}% from expected {expected_count:,}")
            else:
                logger.info(f"  [OK] Record count within 5% of expected {expected_count:,}")

        # Check for TimeOfCall column
        if 'TimeOfCall' not in df.columns and 'Time of Call' not in df.columns:
            logger.error(f"[ERROR] Missing TimeOfCall column in {file_path.name}")
            logger.info(f"  Available columns: {', '.join(df.columns[:10])}...")
            raise ValueError("TimeOfCall column not found")

        # Standardize TimeOfCall column name
        if 'Time of Call' in df.columns:
            df = df.rename(columns={'Time of Call': 'TimeOfCall'})

        logger.info(f"[OK] Successfully loaded {year}: {len(df):,} records")
        return df

    except Exception as e:
        logger.error(f"[ERROR] Error loading {file_path.name}: {str(e)}")
        raise


# ============================================================================
# PARALLEL LOADING
# ============================================================================

def load_files_parallel(file_configs: List[Tuple[str, int, Optional[int]]],
                        config: Dict = None) -> List[Tuple[int, pd.DataFrame]]:
    """
    Load multiple Excel files in parallel using ThreadPoolExecutor.

    Args:
        file_configs: List of (file_path, year, expected_count) tuples
        config: Configuration dictionary

    Returns:
        List of (year, DataFrame) tuples sorted by year
    """
    perf_config = (config or {}).get('performance', {}).get('parallel_loading', {})
    max_workers = perf_config.get('max_workers', min(8, os.cpu_count() or 4))
    parallel_enabled = perf_config.get('enabled', True)

    if not parallel_enabled or len(file_configs) <= 1:
        # Sequential loading
        results = []
        for path, year, expected in file_configs:
            file_path = Path(CAD_ROOT / path) if not Path(path).is_absolute() else Path(path)
            df = load_excel_file(file_path, year, expected, config)
            results.append((year, df))
        return results

    logger.info(f"[PARALLEL] Loading {len(file_configs)} files with {max_workers} workers")
    results = []
    errors = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all load tasks
        future_to_file = {}
        for path, year, expected in file_configs:
            file_path = Path(CAD_ROOT / path) if not Path(path).is_absolute() else Path(path)
            future = executor.submit(load_excel_file, file_path, year, expected, config)
            future_to_file[future] = (path, year)

        # Collect results as they complete
        for future in as_completed(future_to_file):
            path, year = future_to_file[future]
            try:
                df = future.result()
                results.append((year, df))
                logger.info(f"[PARALLEL] Completed {year}: {len(df):,} records")
            except Exception as e:
                logger.error(f"[PARALLEL] Failed {year}: {e}")
                errors.append((year, str(e)))

    if errors:
        logger.warning(f"[PARALLEL] {len(errors)} files failed to load")

    # Sort by year and return
    results.sort(key=lambda x: x[0])
    return results


# ============================================================================
# DATE FILTERING
# ============================================================================

def filter_date_range(df: pd.DataFrame, start_date: pd.Timestamp,
                      end_date: pd.Timestamp) -> pd.DataFrame:
    """
    Filter DataFrame to specified date range.

    Args:
        df: Input DataFrame
        start_date: Start of date range
        end_date: End of date range

    Returns:
        Filtered DataFrame
    """
    original_count = len(df)

    # Parse TimeOfCall to datetime
    df['TimeOfCall'] = pd.to_datetime(df['TimeOfCall'], errors='coerce')

    # Count invalid dates
    invalid_dates = df['TimeOfCall'].isna().sum()
    if invalid_dates > 0:
        logger.warning(f"  [WARN] Found {invalid_dates:,} records with invalid TimeOfCall")

    # Filter date range
    df = df[(df['TimeOfCall'] >= start_date) & (df['TimeOfCall'] <= end_date)]

    filtered_count = len(df)
    removed = original_count - filtered_count

    if removed > 0:
        logger.info(f"  Filtered: {removed:,} records outside date range")

    logger.info(f"  Kept: {filtered_count:,} records within {start_date.date()} to {end_date.date()}")

    return df


# ============================================================================
# BASELINE + INCREMENTAL MODE
# ============================================================================

def run_incremental_consolidation(config: Dict) -> Tuple[pd.DataFrame, str]:
    """
    Run incremental consolidation: load baseline + append new monthly data.

    This avoids re-reading 7 years of data for each run.

    Args:
        config: Configuration dictionary with baseline settings

    Returns:
        Tuple of (consolidated DataFrame, run_type string)
    """
    baseline_config = config.get('baseline', {})
    incremental_config = config.get('incremental', {})

    baseline_path = Path(baseline_config.get('path', ''))
    expected_records = baseline_config.get('record_count', 0)
    baseline_end_date = baseline_config.get('date_range', {}).get('end', '2026-01-30')

    logger.info("=" * 80)
    logger.info("INCREMENTAL MODE: Loading baseline + new data")
    logger.info("=" * 80)

    # Step 1: Load baseline polished file
    logger.info(f"\n[Step 1] Loading baseline file...")
    logger.info(f"  Path: {baseline_path}")

    if not baseline_path.exists():
        logger.error(f"[ERROR] Baseline file not found: {baseline_path}")
        logger.info("Falling back to full consolidation mode")
        return None, "full"

    start_time = time.time()
    baseline_df = pd.read_excel(baseline_path, engine='openpyxl')
    load_time = time.time() - start_time

    # Standardize TimeOfCall column name (ESRI polished uses 'Time of Call')
    if 'Time of Call' in baseline_df.columns and 'TimeOfCall' not in baseline_df.columns:
        baseline_df = baseline_df.rename(columns={'Time of Call': 'TimeOfCall'})
        logger.info("  Standardized 'Time of Call' -> 'TimeOfCall'")

    # Ensure TimeOfCall is datetime
    if 'TimeOfCall' in baseline_df.columns:
        baseline_df['TimeOfCall'] = pd.to_datetime(baseline_df['TimeOfCall'], errors='coerce')

    logger.info(f"  Loaded: {len(baseline_df):,} records in {load_time:.1f}s")
    logger.info(f"  Expected: {expected_records:,} records")

    if abs(len(baseline_df) - expected_records) > 100:
        logger.warning(f"  [WARN] Record count mismatch: got {len(baseline_df):,}, expected {expected_records:,}")

    # Step 2: Identify monthly files to append (from config or directory)
    logger.info(f"\n[Step 2] Resolving monthly files (Jan: exclude already-in-baseline; Feb: from 2026-02-01)...")

    baseline_end = pd.Timestamp(baseline_end_date)
    feb_start = pd.Timestamp("2026-02-01 00:00:00")

    # Baseline IDs for filtering January (avoid re-adding records already in baseline)
    id_col = 'ReportNumberNew'
    if 'Report Number New' in baseline_df.columns and id_col not in baseline_df.columns:
        baseline_df = baseline_df.rename(columns={'Report Number New': id_col})
    baseline_ids = set()
    if id_col in baseline_df.columns:
        baseline_ids = set(baseline_df[id_col].dropna().astype(str).str.strip())
        logger.info(f"  Baseline has {len(baseline_ids):,} unique case IDs for dedup")

    # Resolve monthly file list from config (sources.monthly) or directory
    # In incremental mode only use 2026 monthly files (baseline already has through 2026-01-30)
    monthly_configs = config.get('sources', {}).get('monthly', [])
    new_monthly_files = []
    for item in monthly_configs:
        path_val = item.get('path') if isinstance(item, dict) else item
        if path_val and ("2026" in str(path_val)):
            p = Path(path_val)
            if p.exists():
                new_monthly_files.append((p, item.get('month', '') if isinstance(item, dict) else ''))
            else:
                logger.warning(f"  Config monthly file not found: {p}")
    if not new_monthly_files and (CAD_ROOT / "monthly" / "2026").exists():
        for f in (CAD_ROOT / "monthly" / "2026").glob("*.xlsx"):
            # Skip legacy filename pattern if it exists
            if "2026_01_01_to" in f.name or "CAD_Export" in f.name:
                continue
            new_monthly_files.append((f, ''))

    if not new_monthly_files:
        logger.info("  No new monthly files found")
        return baseline_df, "baseline_only"

    # Step 3: Load and filter each monthly file (Jan: not in baseline; Feb: on or after 2026-02-01)
    logger.info(f"\n[Step 3] Loading and filtering {len(new_monthly_files)} monthly file(s)...")

    new_dfs = []
    for file_path, month_key in new_monthly_files:
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            if 'Time of Call' in df.columns:
                df = df.rename(columns={'Time of Call': 'TimeOfCall'})
            if 'Report Number New' in df.columns and id_col not in df.columns:
                df = df.rename(columns={'Report Number New': id_col})
            df['TimeOfCall'] = pd.to_datetime(df['TimeOfCall'], errors='coerce')

            is_jan = '2026-01' in month_key or '2026_01' in file_path.name
            if is_jan:
                # January: keep only records NOT already in baseline (by case ID)
                if id_col in df.columns and baseline_ids:
                    before = len(df)
                    df = df[~df[id_col].astype(str).str.strip().isin(baseline_ids)]
                    logger.info(f"  {file_path.name}: {before:,} -> {len(df):,} after excluding baseline IDs")
                else:
                    logger.info(f"  {file_path.name}: {len(df):,} records (no baseline ID filter)")
            else:
                # February or later: keep only records on or after 2026-02-01
                before = len(df)
                df = df[df['TimeOfCall'] >= feb_start]
                logger.info(f"  {file_path.name}: {before:,} -> {len(df):,} from 2026-02-01 onward")

            if len(df) > 0:
                new_dfs.append(df)
        except Exception as e:
            logger.error(f"  Failed to load {file_path.name}: {e}")

    if not new_dfs:
        logger.info("  No new records found in monthly files")
        return baseline_df, "baseline_only"

    # Step 4: Concatenate baseline + new records
    logger.info(f"\n[Step 4] Merging baseline with new data...")

    new_combined = pd.concat(new_dfs, ignore_index=True)
    logger.info(f"  New records to add: {len(new_combined):,}")

    # Ensure column alignment
    common_cols = list(set(baseline_df.columns) & set(new_combined.columns))
    baseline_df = baseline_df[common_cols]
    new_combined = new_combined[common_cols]

    combined = pd.concat([baseline_df, new_combined], ignore_index=True)
    logger.info(f"  Combined total: {len(combined):,} records")

    # Step 5: Deduplicate if needed
    dedup_strategy = incremental_config.get('dedup_strategy', 'keep_latest')
    if 'ReportNumberNew' in combined.columns:
        before_dedup = len(combined)
        if dedup_strategy == 'keep_latest':
            combined = combined.sort_values('TimeOfCall', ascending=False)
            combined = combined.drop_duplicates(subset=['ReportNumberNew'], keep='first')
        elif dedup_strategy == 'keep_first':
            combined = combined.drop_duplicates(subset=['ReportNumberNew'], keep='first')
        # 'keep_all_supplements' keeps all records (no dedup)

        after_dedup = len(combined)
        if before_dedup != after_dedup:
            logger.info(f"  Deduplication ({dedup_strategy}): {before_dedup:,} -> {after_dedup:,}")

    return combined, "incremental"


# ============================================================================
# FULL CONSOLIDATION (ORIGINAL MODE)
# ============================================================================

def run_full_consolidation(config: Dict) -> Tuple[pd.DataFrame, str]:
    """
    Run full consolidation: load all yearly + monthly files.

    Args:
        config: Configuration dictionary (REQUIRED - contains monthly file paths)

    Returns:
        Tuple of (consolidated DataFrame, run_type string)
        
    Raises:
        ValueError: If config is None or missing required structure
    """
    if config is None or not config:
        raise ValueError(
            "Configuration is required for full consolidation. "
            "Monthly files from config.yaml are needed to include 2026 data. "
            f"Config file must exist at: {CONFIG_PATH}"
        )
    
    logger.info("=" * 80)
    logger.info("FULL MODE: Loading all source files")
    logger.info("=" * 80)

    # Create file configs list
    file_configs = [(path, year, expected) for path, year, expected in YEARLY_FILES]
    
    # Load monthly files from config (2026 monthly exports) - REQUIRED for 2026 data
    # Config is guaranteed to be non-empty dict by check above
    if config.get('sources', {}).get('monthly'):
        monthly_configs = config.get('sources', {}).get('monthly', [])
        for item in monthly_configs:
            if isinstance(item, dict):
                path = item.get('path', '')
            else:
                path = item
            
            if path and Path(path).exists():
                # Use 2026 as year for monthly files
                file_configs.append((path, 2026, None))
                logger.info(f"  Added monthly file: {Path(path).name}")
            elif path:
                logger.warning(f"  Monthly file not found: {path}")

    # Load files (parallel or sequential based on config)
    logger.info(f"\n[Step 1] Loading {len(file_configs)} source files...")
    start_time = time.time()

    loaded_files = load_files_parallel(file_configs, config)
    load_time = time.time() - start_time
    logger.info(f"[OK] Loaded {len(loaded_files)} files in {load_time:.1f}s")

    # Apply date filtering
    logger.info(f"\n[Step 2] Filtering date range...")
    all_dataframes = []
    for year, df in loaded_files:
        df = filter_date_range(df, START_DATE, END_DATE)
        all_dataframes.append(df)

    # Concatenate all dataframes
    logger.info(f"\n[Step 3] Concatenating {len(all_dataframes)} DataFrames...")
    consolidated = pd.concat(all_dataframes, ignore_index=True)
    logger.info(f"[OK] Consolidated total: {len(consolidated):,} records")

    # Final date range filter
    consolidated = filter_date_range(consolidated, START_DATE, END_DATE)

    return consolidated, "full"


# ============================================================================
# MAIN CONSOLIDATION FUNCTION
# ============================================================================

def consolidate_cad_data(force_full: bool = False):
    """
    Main consolidation process.

    Automatically chooses between incremental and full mode based on config.

    Args:
        force_full: Force full consolidation even if incremental is enabled
    """
    start_time = time.time()

    logger.info("=" * 80)
    logger.info("CAD DATA CONSOLIDATION: 2019-01-01 to 2026-01-30")
    logger.info("Version: 1.2.3 (Speed Optimizations)")
    logger.info("=" * 80)

    # Create directories
    create_directories()

    # Load configuration
    config = load_config()

    # Determine run mode
    baseline_enabled = config.get('baseline', {}).get('enabled', False)
    incremental_enabled = config.get('incremental', {}).get('enabled', False)
    baseline_path = Path(config.get('baseline', {}).get('path', ''))

    use_incremental = (
        not force_full and
        baseline_enabled and
        incremental_enabled and
        baseline_path.exists()
    )

    if use_incremental:
        logger.info("\n[MODE] Incremental mode enabled")
        consolidated, run_type = run_incremental_consolidation(config)
        if consolidated is None:
            logger.info("[MODE] Falling back to full consolidation")
            consolidated, run_type = run_full_consolidation(config)
    else:
        if force_full:
            logger.info("\n[MODE] Full mode (forced)")
        else:
            logger.info("\n[MODE] Full mode (incremental not configured or baseline missing)")
        consolidated, run_type = run_full_consolidation(config)

    # Check if we have any data
    if consolidated is None or len(consolidated) == 0:
        logger.error("[ERROR] No data consolidated! Cannot continue.")
        sys.exit(1)

    # Apply memory optimization
    logger.info("\n" + "-" * 80)
    logger.info("OPTIMIZING MEMORY")
    logger.info("-" * 80)
    consolidated = optimize_dtypes(consolidated, config)

    # Check for duplicates
    unique_cases = None
    if 'ReportNumberNew' in consolidated.columns:
        unique_cases = consolidated['ReportNumberNew'].nunique()
        duplicates = len(consolidated) - unique_cases
        logger.info(f"Unique case numbers: {unique_cases:,}")
        if duplicates > 0:
            logger.info(f"Duplicate records (supplements/units): {duplicates:,}")

    # Export to CSV
    output_file = OUTPUT_PATH / f"2019_to_2026_01_30_CAD.csv"
    logger.info("\n" + "-" * 80)
    logger.info("EXPORTING TO CSV")
    logger.info("-" * 80)
    logger.info(f"Output file: {output_file}")

    consolidated.to_csv(output_file, index=False)

    output_size_mb = output_file.stat().st_size / (1024 * 1024)
    logger.info(f"[OK] Export complete: {output_size_mb:.1f} MB")

    # Calculate timing
    total_time = time.time() - start_time

    # Standardize TimeOfCall column name if needed
    if 'Time of Call' in consolidated.columns and 'TimeOfCall' not in consolidated.columns:
        consolidated = consolidated.rename(columns={'Time of Call': 'TimeOfCall'})

    # Ensure TimeOfCall is datetime
    if 'TimeOfCall' in consolidated.columns:
        consolidated['TimeOfCall'] = pd.to_datetime(consolidated['TimeOfCall'], errors='coerce')

    # Generate summary
    logger.info("\n" + "=" * 80)
    logger.info("CONSOLIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Mode: {run_type}")
    logger.info(f"Total records: {len(consolidated):,}")

    # Get date column (handle both names)
    date_col = 'TimeOfCall' if 'TimeOfCall' in consolidated.columns else 'Time of Call'
    if date_col in consolidated.columns:
        logger.info(f"Date range: {consolidated[date_col].min()} to {consolidated[date_col].max()}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"File size: {output_size_mb:.1f} MB")
    logger.info(f"Processing time: {total_time:.1f} seconds")

    if unique_cases:
        logger.info(f"Unique cases: {unique_cases:,}")

    logger.info("\n[OK] Consolidation complete!")
    logger.info(f"[OK] Ready for CAD_Data_Cleaning_Engine processing")

    # Create run-specific report directory
    report_dir = get_report_directory(run_type)
    logger.info(f"\n[OK] Report directory: {report_dir}")

    # Prepare metrics for reports
    date_col = 'TimeOfCall' if 'TimeOfCall' in consolidated.columns else 'Time of Call'
    if date_col in consolidated.columns:
        date_min = str(consolidated[date_col].min())
        date_max = str(consolidated[date_col].max())
    else:
        date_min = "N/A"
        date_max = "N/A"

    metrics = {
        "record_count": len(consolidated),
        "unique_cases": unique_cases,
        "date_range": {"start": date_min, "end": date_max},
        "output_file": str(output_file),
        "file_size_mb": round(output_size_mb, 2),
        "mode": run_type,
        "processing_time_seconds": round(total_time, 1),
        "generated": datetime.now().isoformat()
    }

    # Generate summary report (text)
    summary_file = report_dir / "consolidation_summary.txt"

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CAD DATA CONSOLIDATION SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Report Directory: {report_dir}\n")
        f.write(f"Mode: {run_type}\n\n")
        f.write(f"Total Records: {len(consolidated):,}\n")
        f.write(f"Date Range: {date_min} to {date_max}\n")
        f.write(f"Output File: {output_file}\n")
        f.write(f"File Size: {output_size_mb:.1f} MB\n")
        f.write(f"Processing Time: {total_time:.1f} seconds\n")

        if unique_cases:
            f.write(f"Unique Cases: {unique_cases:,}\n")

        f.write("\n" + "-" * 80 + "\n")
        f.write("PERFORMANCE SETTINGS:\n")
        f.write("-" * 80 + "\n")
        perf = config.get('performance', {})
        f.write(f"  Parallel Loading: {perf.get('parallel_loading', {}).get('enabled', False)}\n")
        f.write(f"  Max Workers: {perf.get('parallel_loading', {}).get('max_workers', 'N/A')}\n")
        f.write(f"  Chunked Reading: {perf.get('chunked_reading', {}).get('enabled', False)}\n")
        f.write(f"  Memory Optimization: {perf.get('memory_optimization', {}).get('use_categories', False)}\n")

        f.write("\n" + "-" * 80 + "\n")
        f.write("SOURCE FILES:\n")
        f.write("-" * 80 + "\n")

        for file_rel_path, year, expected_count in YEARLY_FILES:
            f.write(f"  {year}: {file_rel_path}\n")

        # Monthly files loaded from config
        f.write(f"  2026: Monthly files from config (2026_01_CAD.xlsx, 2026_02_CAD.xlsx)\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("NEXT STEPS:\n")
        f.write("=" * 80 + "\n")
        f.write("1. Run CAD_Data_Cleaning_Engine pipeline:\n")
        f.write(f"   cd {CLEANING_ENGINE_ROOT}\n")
        f.write("   python scripts/enhanced_esri_output_generator.py\n\n")
        f.write("2. Validate output:\n")
        f.write("   python scripts/validation/validate_esri_polished_dataset.py\n\n")
        f.write("3. Copy results to cad_rms_data_quality project\n")

    logger.info(f"[OK] Summary report: {summary_file}")

    # Generate JSON metrics file
    metrics_file = report_dir / "consolidation_metrics.json"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"[OK] Metrics JSON: {metrics_file}")

    # Update latest.json pointer
    update_latest_pointer(report_dir, metrics)

    return output_file


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CAD Data Consolidation (2019-2026)")
    parser.add_argument('--full', action='store_true',
                        help='Force full consolidation (ignore baseline/incremental settings)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without executing')

    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        config = load_config()
        baseline_enabled = config.get('baseline', {}).get('enabled', False)
        incremental_enabled = config.get('incremental', {}).get('enabled', False)
        baseline_path = Path(config.get('baseline', {}).get('path', ''))

        logger.info(f"  Baseline enabled: {baseline_enabled}")
        logger.info(f"  Incremental enabled: {incremental_enabled}")
        logger.info(f"  Baseline exists: {baseline_path.exists()}")
        logger.info(f"  Would use mode: {'incremental' if baseline_enabled and incremental_enabled and baseline_path.exists() else 'full'}")
        sys.exit(0)

    try:
        output_file = consolidate_cad_data(force_full=args.full)
        logger.info("\n" + "=" * 80)
        logger.info("[SUCCESS] CONSOLIDATION COMPLETE")
        logger.info("=" * 80)
        sys.exit(0)

    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("[FAILED] CONSOLIDATION FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
