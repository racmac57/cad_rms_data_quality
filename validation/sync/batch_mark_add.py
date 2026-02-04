"""
Batch Mark Add - Extract all drift entries and mark them as 'Add'
One-time script for initial sync of reference data
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime


def extract_and_mark_all():
    """Extract all drift entries from validation JSON and mark as Add"""
    
    # Load validation summary
    json_path = Path('validation/reports/validation_summary_20260204_003131.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    output_dir = Path('validation/reports/drift')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Process Call Type Drift
    call_type_drift = next((d for d in data['drift_results'] if d['detector'] == 'CallTypeDriftDetector'), None)
    
    if call_type_drift:
        new_types = call_type_drift.get('new_call_types', [])
        print(f"Found {len(new_types)} new call types")
        
        if new_types:
            df_new = pd.DataFrame(new_types)
            df_new = df_new.rename(columns={
                'value': 'CallType',
                'normalized': 'CallType_Normalized',
                'count': 'Frequency'
            })
            # Mark ALL as Add (bulk sync)
            df_new['Action'] = 'Add'
            df_new['ConsolidateWith'] = ''
            df_new['Notes'] = 'Bulk sync 2026-02-04'
            
            output_file = output_dir / f'call_types_approved_{timestamp}.csv'
            df_new.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Created: {output_file} ({len(df_new)} entries)")
    
    # Process Personnel Drift
    personnel_drift = next((d for d in data['drift_results'] if d['detector'] == 'PersonnelDriftDetector'), None)
    
    if personnel_drift:
        new_personnel = personnel_drift.get('new_personnel', [])
        print(f"Found {len(new_personnel)} new personnel")
        
        if new_personnel:
            df_new = pd.DataFrame(new_personnel)
            df_new = df_new.rename(columns={
                'value': 'Officer',
                'normalized': 'Officer_Normalized',
                'count': 'CallCount'
            })
            # Mark ALL as Add (bulk sync)
            df_new['Action'] = 'Add'
            df_new['ConsolidateWith'] = ''
            df_new['Status'] = 'Active'
            df_new['Notes'] = 'Bulk sync 2026-02-04'
            
            output_file = output_dir / f'personnel_approved_{timestamp}.csv'
            df_new.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Created: {output_file} ({len(df_new)} entries)")
    
    print("\nCSV files created with Action='Add' for all entries")
    print("Ready to apply with: python validation/sync/apply_drift_sync.py --apply")


if __name__ == '__main__':
    extract_and_mark_all()
