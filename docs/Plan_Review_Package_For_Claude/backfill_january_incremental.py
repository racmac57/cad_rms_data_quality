"""
Incremental Backfill Script - Add January 17-30, 2026 data
Adds missing 14 days to existing ESRI polished file

Author: R. A. Carucci
Date: 2026-01-31
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
EXISTING_ESRI_FILE = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final\CAD_ESRI_POLISHED_20260131_004142.xlsx")
MONTHLY_FILE = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\monthly\2026\2026_01_01_to_2026_01_30_CAD_Export.xlsx")
OUTPUT_DIR = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\CAD_Data_Cleaning_Engine\data\03_final")
RMS_FILE = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\monthly\2026\2026_01_01_to_2026_01_30_RMS_Export.xlsx")

# Date cutoff
CUTOFF_DATE = pd.Timestamp("2026-01-17 00:00:00")

def load_existing_esri():
    """Load existing ESRI polished file"""
    logger.info(f"Loading existing ESRI file: {EXISTING_ESRI_FILE.name}")
    df = pd.read_excel(EXISTING_ESRI_FILE)
    logger.info(f"Loaded {len(df):,} existing records")
    return df

def extract_new_records():
    """Extract records from 01-17 to 01-30"""
    logger.info(f"Loading monthly file: {MONTHLY_FILE.name}")
    df = pd.read_excel(MONTHLY_FILE)
    logger.info(f"Loaded {len(df):,} records from monthly file")
    
    # Parse date
    df['Time of Call'] = pd.to_datetime(df['Time of Call'], errors='coerce')
    
    # Filter for new records only (after 01-16)
    new_records = df[df['Time of Call'] >= CUTOFF_DATE].copy()
    logger.info(f"Extracted {len(new_records):,} new records (01-17 to 01-30)")
    
    return new_records

def apply_column_mapping(df):
    """Map column names to ESRI schema"""
    column_map = {
        'Time of Call': 'TimeOfCall',
        'How Reported': 'HowReported',
        'Time Dispatched': 'TimeDispatched',
        'Time Out': 'TimeOut',
        'Time In': 'TimeIn',
        'Time Spent': 'TimeSpent',
        'Time Response': 'TimeResponse',
        'Response Type': 'ResponseType'
    }
    
    df = df.rename(columns=column_map)
    return df

def backfill_from_rms(df):
    """Apply RMS backfill for missing PDZone and Grid"""
    logger.info("Applying RMS backfill...")
    
    if not RMS_FILE.exists():
        logger.warning(f"RMS file not found: {RMS_FILE}")
        return df
    
    try:
        rms = pd.read_excel(RMS_FILE)
        logger.info(f"Loaded {len(rms):,} RMS records")
        
        # Count missing values before backfill
        missing_zone = df['PDZone'].isna().sum()
        missing_grid = df['Grid'].isna().sum()
        logger.info(f"Missing before backfill: {missing_zone} PDZone, {missing_grid} Grid")
        
        # Merge on ReportNumberNew (CAD) to CaseNumber (RMS)
        rms_lookup = rms[['CaseNumber', 'Zone', 'Grid']].rename(columns={
            'CaseNumber': 'ReportNumberNew',
            'Zone': 'RMS_Zone',
            'Grid': 'RMS_Grid'
        })
        
        df = df.merge(rms_lookup, on='ReportNumberNew', how='left')
        
        # Backfill
        df['PDZone'] = df['PDZone'].fillna(df['RMS_Zone'])
        df['Grid'] = df['Grid'].fillna(df['RMS_Grid'])
        
        # Drop temporary columns
        df = df.drop(columns=['RMS_Zone', 'RMS_Grid'], errors='ignore')
        
        # Count filled
        filled_zone = missing_zone - df['PDZone'].isna().sum()
        filled_grid = missing_grid - df['Grid'].isna().sum()
        logger.info(f"Backfilled: {filled_zone} PDZone, {filled_grid} Grid values")
        
    except Exception as e:
        logger.warning(f"RMS backfill failed: {e}")
    
    return df

def normalize_fields(df):
    """Apply basic normalization"""
    logger.info("Applying field normalization...")
    
    # Normalize HowReported
    how_reported_map = {
        '911': '911',
        '9-1-1': '911',
        '91-1': '911',
        'Radio': 'Radio',
        'R': 'Radio',
        'Phone': 'Phone',
        'P': 'Phone',
        'Walk-In': 'Walk-In',
        'Self-Initiated': 'Self-Initiated',
        'Alarm': 'Alarm'
    }
    
    if 'HowReported' in df.columns:
        df['HowReported'] = df['HowReported'].map(how_reported_map).fillna(df['HowReported'])
    
    # Normalize Disposition
    disposition_map = {
        'A': 'Arrest',
        'Arrest': 'Arrest',
        'C': 'Completed',
        'Completed': 'Completed',
        'GOA': 'Gone on Arrival',
        'Gone on Arrival': 'Gone on Arrival',
        'NAA': 'No Action',
        'No Action': 'No Action',
        'R': 'Report',
        'Report': 'Report',
        'U': 'Unfounded',
        'Unfounded': 'Unfounded',
        'W': 'Warning',
        'Warning': 'Warning'
    }
    
    if 'Disposition' in df.columns:
        df['Disposition'] = df['Disposition'].map(disposition_map).fillna(df['Disposition'])
    
    logger.info("Normalization complete")
    return df

def merge_and_deduplicate(existing_df, new_df):
    """Merge new records with existing and deduplicate"""
    logger.info("Merging datasets...")
    
    # Combine
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    logger.info(f"Combined total: {len(combined):,} records")
    
    # Deduplicate by ReportNumberNew
    before_dedup = len(combined)
    combined = combined.drop_duplicates(subset=['ReportNumberNew'], keep='last')
    after_dedup = len(combined)
    
    if before_dedup > after_dedup:
        logger.info(f"Removed {before_dedup - after_dedup:,} duplicate records")
    
    # Sort by TimeOfCall
    combined = combined.sort_values('TimeOfCall', ascending=True)
    
    logger.info(f"Final dataset: {len(combined):,} records")
    return combined

def main():
    """Main execution"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.info("=" * 80)
    logger.info("INCREMENTAL BACKFILL: January 17-30, 2026")
    logger.info("=" * 80)
    
    try:
        # Step 1: Load existing ESRI file
        existing_df = load_existing_esri()
        
        # Step 2: Extract new records from monthly file
        new_df = extract_new_records()
        
        if len(new_df) == 0:
            logger.warning("No new records to add!")
            return
        
        # Step 3: Apply column mapping
        new_df = apply_column_mapping(new_df)
        
        # Step 4: Apply RMS backfill
        new_df = backfill_from_rms(new_df)
        
        # Step 5: Normalize fields
        new_df = normalize_fields(new_df)
        
        # Step 6: Merge and deduplicate
        final_df = merge_and_deduplicate(existing_df, new_df)
        
        # Step 7: Save output
        output_file = OUTPUT_DIR / f"CAD_ESRI_POLISHED_COMPLETE_JAN_{timestamp}.xlsx"
        logger.info(f"Saving to: {output_file.name}")
        
        final_df.to_excel(output_file, index=False, engine='openpyxl')
        
        file_size = output_file.stat().st_size / (1024 * 1024)
        logger.info(f"File saved: {file_size:.1f} MB")
        
        # Summary
        logger.info("=" * 80)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total records: {len(final_df):,}")
        logger.info(f"Date range: {final_df['TimeOfCall'].min()} to {final_df['TimeOfCall'].max()}")
        logger.info(f"Output file: {output_file}")
        logger.info("[OK] Ready for ArcGIS Pro import!")
        
        return output_file
        
    except Exception as e:
        logger.error(f"[ERROR] Backfill failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    output = main()
