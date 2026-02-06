"""
Sync Helper - Extract Drift Reports to CSV
Extracts drift detection results into easy-to-review CSV files for manual approval
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse


def extract_drift_to_csv(json_report_path: str, output_dir: str = "validation/reports/drift"):
    """
    Extract drift detection results from validation JSON to separate CSV files
    
    Creates:
    - call_types_to_add.csv - New call types found in data
    - call_types_unused.csv - Call types not seen recently
    - personnel_to_add.csv - New personnel found in data
    """
    
    # Load validation summary
    with open(json_report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Process Call Type Drift
    call_type_drift = next((d for d in data['drift_results'] if d['detector'] == 'CallTypeDriftDetector'), None)
    
    if call_type_drift:
        # New call types
        new_types = call_type_drift.get('new_call_types', [])
        if new_types:
            df_new = pd.DataFrame(new_types)
            df_new = df_new.rename(columns={
                'value': 'CallType',
                'normalized': 'CallType_Normalized',
                'count': 'Frequency'
            })
            df_new['Action'] = 'Review'  # User can mark as 'Add', 'Consolidate', or 'Ignore'
            df_new['ConsolidateWith'] = ''  # For mapping to existing types
            df_new['Notes'] = ''
            
            output_file = output_path / f'call_types_to_add_{timestamp}.csv'
            df_new.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"[OK] Created: {output_file}")
            print(f"  {len(df_new)} new call types to review")
        
        # Unused call types
        unused_types = call_type_drift.get('unused_call_types', [])
        if unused_types:
            df_unused = pd.DataFrame(unused_types)
            df_unused = df_unused.rename(columns={
                'value': 'CallType',
                'normalized': 'CallType_Normalized',
                'note': 'Reason'
            })
            df_unused['Action'] = 'Review'  # User can mark as 'Archive' or 'Keep'
            df_unused['Notes'] = ''
            
            output_file = output_path / f'call_types_unused_{timestamp}.csv'
            df_unused.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"[OK] Created: {output_file}")
            print(f"  {len(df_unused)} unused call types to review")
        
        # Statistics
        stats = call_type_drift.get('statistics', {})
        print(f"\nCall Type Statistics:")
        print(f"  Reference file: {stats.get('reference_count', 0)} types")
        print(f"  Data contains: {stats.get('unique_call_types', 0)} types")
        print(f"  Coverage: {stats.get('coverage_pct', 0)}%")
    
    # Process Personnel Drift
    personnel_drift = next((d for d in data['drift_results'] if d['detector'] == 'PersonnelDriftDetector'), None)
    
    if personnel_drift:
        # New personnel
        new_personnel = personnel_drift.get('new_personnel', [])
        if new_personnel:
            df_new = pd.DataFrame(new_personnel)
            df_new = df_new.rename(columns={
                'value': 'Officer',
                'normalized': 'Officer_Normalized',
                'count': 'CallCount'
            })
            df_new['Action'] = 'Review'  # User can mark as 'Add' or 'Consolidate'
            df_new['ConsolidateWith'] = ''  # For name variations
            df_new['Status'] = 'Active'  # Active/Inactive
            df_new['Notes'] = ''
            
            output_file = output_path / f'personnel_to_add_{timestamp}.csv'
            df_new.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n[OK] Created: {output_file}")
            print(f"  {len(df_new)} new personnel to review")
        
        # Statistics
        stats = personnel_drift.get('statistics', {})
        print(f"\nPersonnel Statistics:")
        print(f"  Reference file: {stats.get('reference_count', 0)} personnel")
        print(f"  Data contains: {stats.get('unique_officers', 0)} personnel")
    
    print(f"\n[OK] Drift reports extracted to: {output_path}/")
    print(f"\nNext steps:")
    print(f"  1. Review the CSV files and mark actions")
    print(f"  2. Run sync script to apply approved changes")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract drift detection results to CSV')
    parser.add_argument('-i', '--input', required=True, help='Path to validation JSON summary')
    parser.add_argument('-o', '--output', default='validation/reports/drift', help='Output directory')
    
    args = parser.parse_args()
    extract_drift_to_csv(args.input, args.output)
