#!/usr/bin/env python3
"""
CAD Data Consolidation Script (2019 to 2026-01-29)
Prepares input for CAD_Data_Cleaning_Engine pipeline

This script consolidates:
- 7 yearly CAD files (2019-2025)
- 1 monthly file (2026-01-01 to 2026-01-29)

Output: Single CSV file ready for RMS backfill and ESRI export processing

Author: R. A. Carucci
Date: 2026-01-30
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import sys

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

# Source files configuration
YEARLY_FILES = [
    ("yearly/2019/2019_CAD_ALL.xlsx", 2019, 91217),
    ("yearly/2020/2020_CAD_ALL.xlsx", 2020, 89400),
    ("yearly/2021/2021_CAD_ALL.xlsx", 2021, 91477),
    ("yearly/2022/2022_CAD_ALL.xlsx", 2022, 105038),
    ("yearly/2023/2023_CAD_ALL.xlsx", 2023, 113179),
    ("yearly/2024/2024_CAD_ALL.xlsx", 2024, 110313),
    ("yearly/2025/2025_CAD_ALL.xlsx", 2025, 114065),
]

MONTHLY_FILE = ("monthly/2026/2026_01_01_to_2026_01_29_CAD_Export.xlsx", 2026, None)

# Date range filter
START_DATE = pd.Timestamp("2019-01-01")
END_DATE = pd.Timestamp("2026-01-29 23:59:59")


def create_directories():
    """Ensure required directories exist"""
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    logger.info(f"[OK] Output directory ready: {OUTPUT_PATH}")


def load_excel_file(file_path: Path, year: int, expected_count: int = None) -> pd.DataFrame:
    """
    Load Excel file with error handling and validation
    
    Args:
        file_path: Path to Excel file
        year: Year for this file
        expected_count: Expected record count (for verification)
    
    Returns:
        DataFrame with loaded data
    """
    logger.info(f"Loading {year}: {file_path.name}")
    
    if not file_path.exists():
        logger.error(f"✗ File not found: {file_path}")
        raise FileNotFoundError(f"Missing file: {file_path}")
    
    try:
        # Load Excel file
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Log file stats
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"  Size: {file_size_mb:.1f} MB")
        logger.info(f"  Rows: {len(df):,}")
        logger.info(f"  Columns: {len(df.columns)}")
        
        # Verify expected count
        if expected_count:
            deviation = abs(len(df) - expected_count) / expected_count * 100
            if deviation > 5:
                logger.warning(f"  ⚠ Record count deviation: {deviation:.1f}% from expected {expected_count:,}")
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


def filter_date_range(df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """
    Filter DataFrame to specified date range
    
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


def consolidate_cad_data():
    """Main consolidation process"""
    logger.info("=" * 80)
    logger.info("CAD DATA CONSOLIDATION: 2019-01-01 to 2026-01-29")
    logger.info("=" * 80)
    
    # Create directories
    create_directories()
    
    # Load all files
    all_dataframes = []
    total_records = 0
    
    logger.info("\n" + "-" * 80)
    logger.info("LOADING YEARLY FILES (2019-2025)")
    logger.info("-" * 80)
    
    for file_rel_path, year, expected_count in YEARLY_FILES:
        file_path = CAD_ROOT / file_rel_path
        try:
            df = load_excel_file(file_path, year, expected_count)
            df = filter_date_range(df, START_DATE, END_DATE)
            all_dataframes.append(df)
            total_records += len(df)
        except Exception as e:
            logger.error(f"Failed to process {year}: {e}")
            logger.info("Continuing with remaining files...")
    
    logger.info("\n" + "-" * 80)
    logger.info("LOADING MONTHLY FILE (2026-01-01 to 2026-01-29)")
    logger.info("-" * 80)
    
    file_rel_path, year, _ = MONTHLY_FILE
    file_path = CAD_ROOT / file_rel_path
    try:
        df = load_excel_file(file_path, year)
        df = filter_date_range(df, START_DATE, END_DATE)
        all_dataframes.append(df)
        total_records += len(df)
    except Exception as e:
        logger.error(f"Failed to process 2026 monthly file: {e}")
    
    # Check if we have any data
    if not all_dataframes:
        logger.error("[ERROR] No data loaded! Cannot continue.")
        sys.exit(1)
    
    logger.info("\n" + "-" * 80)
    logger.info("CONSOLIDATING DATA")
    logger.info("-" * 80)
    
    # Concatenate all dataframes
    logger.info(f"Merging {len(all_dataframes)} files...")
    consolidated = pd.concat(all_dataframes, ignore_index=True)
    
    logger.info(f"[OK] Consolidated total: {len(consolidated):,} records")
    
    # Final date range filter (in case any slipped through)
    consolidated = filter_date_range(consolidated, START_DATE, END_DATE)
    
    # Check for duplicates
    if 'ReportNumberNew' in consolidated.columns:
        unique_cases = consolidated['ReportNumberNew'].nunique()
        duplicates = len(consolidated) - unique_cases
        logger.info(f"Unique case numbers: {unique_cases:,}")
        if duplicates > 0:
            logger.info(f"Duplicate records (supplements/units): {duplicates:,}")
    
    # Export to CSV
    output_file = OUTPUT_PATH / f"2019_to_2026_01_29_CAD.csv"
    logger.info("\n" + "-" * 80)
    logger.info("EXPORTING TO CSV")
    logger.info("-" * 80)
    logger.info(f"Output file: {output_file}")
    
    consolidated.to_csv(output_file, index=False)
    
    output_size_mb = output_file.stat().st_size / (1024 * 1024)
    logger.info(f"[OK] Export complete: {output_size_mb:.1f} MB")
    
    # Generate summary
    logger.info("\n" + "=" * 80)
    logger.info("CONSOLIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total records: {len(consolidated):,}")
    logger.info(f"Date range: {consolidated['TimeOfCall'].min()} to {consolidated['TimeOfCall'].max()}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"File size: {output_size_mb:.1f} MB")
    
    if 'ReportNumberNew' in consolidated.columns:
        logger.info(f"Unique cases: {consolidated['ReportNumberNew'].nunique():,}")
    
    logger.info("\n[OK] Consolidation complete!")
    logger.info(f"[OK] Ready for CAD_Data_Cleaning_Engine processing")
    
    # Generate summary report
    summary_file = Path("outputs/consolidation/consolidation_summary.txt")
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("CAD DATA CONSOLIDATION SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Input Files: {len(all_dataframes)}\n")
        f.write(f"Total Records: {len(consolidated):,}\n")
        f.write(f"Date Range: {consolidated['TimeOfCall'].min()} to {consolidated['TimeOfCall'].max()}\n")
        f.write(f"Output File: {output_file}\n")
        f.write(f"File Size: {output_size_mb:.1f} MB\n")
        
        if 'ReportNumberNew' in consolidated.columns:
            f.write(f"Unique Cases: {consolidated['ReportNumberNew'].nunique():,}\n")
        
        f.write("\n" + "─" * 80 + "\n")
        f.write("SOURCE FILES:\n")
        f.write("─" * 80 + "\n")
        
        for file_rel_path, year, expected_count in YEARLY_FILES:
            f.write(f"  {year}: {file_rel_path}\n")
        
        file_rel_path, year, _ = MONTHLY_FILE
        f.write(f"  {year}: {file_rel_path}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("NEXT STEPS:\n")
        f.write("=" * 80 + "\n")
        f.write("1. Run CAD_Data_Cleaning_Engine pipeline:\n")
        f.write(f"   cd {CLEANING_ENGINE_ROOT}\n")
        f.write("   python scripts/enhanced_esri_output_generator.py\n\n")
        f.write("2. Validate output:\n")
        f.write("   python scripts/validation/validate_esri_polished_dataset.py\n\n")
        f.write("3. Copy results to cad_rms_data_quality project\n")
    
    logger.info(f"\n[OK] Summary report: {summary_file}")
    
    return output_file


if __name__ == "__main__":
    try:
        output_file = consolidate_cad_data()
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
