"""
Extract ALL drift items directly from baseline vs reference files
Bypasses the 50-item limit in the drift detectors
"""
import pandas as pd
from pathlib import Path
from datetime import datetime


def normalize_value(val):
    """Normalize a value for comparison"""
    if pd.isna(val):
        return None
    return str(val).strip().upper()


def extract_call_type_drift():
    """Extract ALL new call types (not limited to 50)"""
    
    print("=" * 70)
    print("CALL TYPE DRIFT EXTRACTION")
    print("=" * 70)
    
    # Load baseline data
    baseline_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx"
    print(f"Loading baseline: {baseline_path}")
    df = pd.read_excel(baseline_path, dtype={'ReportNumberNew': str})
    print(f"Loaded {len(df)} records")
    
    # Load reference file
    ref_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\CallTypes_Master.csv"
    print(f"Loading reference: {ref_path}")
    df_ref = pd.read_csv(ref_path, encoding='utf-8-sig')
    print(f"Reference has {len(df_ref)} call types")
    
    # Get normalized reference call types
    ref_types = set()
    for col in ['Incident', 'Incident_Norm']:
        if col in df_ref.columns:
            ref_types.update(df_ref[col].dropna().apply(normalize_value).tolist())
    print(f"Reference normalized types: {len(ref_types)}")
    
    # Get unique call types from data
    field_name = 'Incident'
    data_types = df[field_name].dropna().unique()
    print(f"Data unique types: {len(data_types)}")
    
    # Count occurrences
    type_counts = df[field_name].value_counts()
    
    # Find new types (in data, not in reference)
    new_types = []
    for raw_val in data_types:
        normalized = normalize_value(raw_val)
        if normalized and normalized not in ref_types:
            new_types.append({
                'CallType': str(raw_val).strip(),
                'CallType_Normalized': normalized,
                'Frequency': int(type_counts.get(raw_val, 0)),
                'Action': 'Add',
                'ConsolidateWith': '',
                'Notes': ''
            })
    
    # Sort by frequency
    new_types.sort(key=lambda x: x['Frequency'], reverse=True)
    print(f"Found {len(new_types)} NEW call types")
    
    # Save to CSV
    output_dir = Path('validation/reports/drift')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'call_types_ALL_to_add_{timestamp}.csv'
    
    df_new = pd.DataFrame(new_types)
    df_new.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Saved: {output_file}")
    
    # Show top 10
    print("\nTop 10 new call types:")
    for i, t in enumerate(new_types[:10], 1):
        print(f"  {i}. {t['CallType']} ({t['Frequency']} calls)")
    
    return len(new_types), str(output_file)


def extract_personnel_drift():
    """Extract ALL new personnel (not limited to 50)"""
    
    print("\n" + "=" * 70)
    print("PERSONNEL DRIFT EXTRACTION")
    print("=" * 70)
    
    # Load baseline data
    baseline_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base\CAD_ESRI_Polished_Baseline.xlsx"
    print(f"Loading baseline: {baseline_path}")
    df = pd.read_excel(baseline_path, dtype={'ReportNumberNew': str})
    print(f"Loaded {len(df)} records")
    
    # Load reference file
    ref_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Personnel\Assignment_Master_V2.csv"
    print(f"Loading reference: {ref_path}")
    df_ref = pd.read_csv(ref_path, encoding='utf-8-sig')
    print(f"Reference has {len(df_ref)} personnel")
    
    # Get normalized reference personnel
    ref_personnel = set()
    for col in df_ref.columns:
        if 'name' in col.lower() or 'officer' in col.lower() or 'full' in col.lower():
            ref_personnel.update(df_ref[col].dropna().apply(normalize_value).tolist())
    print(f"Reference normalized personnel: {len(ref_personnel)}")
    
    # Get unique personnel from data - check multiple columns
    personnel_columns = ['AssignedOfficer', 'Assigned Officer', 'Officer', 'Primary Unit']
    field_name = None
    for col in personnel_columns:
        if col in df.columns:
            field_name = col
            break
    
    if not field_name:
        print("Warning: Could not find officer column in data")
        return 0, None
    
    print(f"Using column: {field_name}")
    
    data_personnel = df[field_name].dropna().unique()
    print(f"Data unique personnel: {len(data_personnel)}")
    
    # Count occurrences
    personnel_counts = df[field_name].value_counts()
    
    # Find new personnel (in data, not in reference)
    new_personnel = []
    for raw_val in data_personnel:
        normalized = normalize_value(raw_val)
        if normalized and normalized not in ref_personnel:
            new_personnel.append({
                'Officer': str(raw_val).strip(),
                'Officer_Normalized': normalized,
                'CallCount': int(personnel_counts.get(raw_val, 0)),
                'Action': 'Add',
                'ConsolidateWith': '',
                'Status': 'Active',
                'Notes': ''
            })
    
    # Sort by count
    new_personnel.sort(key=lambda x: x['CallCount'], reverse=True)
    print(f"Found {len(new_personnel)} NEW personnel")
    
    # Save to CSV
    output_dir = Path('validation/reports/drift')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'personnel_ALL_to_add_{timestamp}.csv'
    
    df_new = pd.DataFrame(new_personnel)
    df_new.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Saved: {output_file}")
    
    # Show top 10
    print("\nTop 10 new personnel:")
    for i, p in enumerate(new_personnel[:10], 1):
        print(f"  {i}. {p['Officer']} ({p['CallCount']} calls)")
    
    return len(new_personnel), str(output_file)


if __name__ == '__main__':
    call_count, call_file = extract_call_type_drift()
    personnel_count, personnel_file = extract_personnel_drift()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"New call types: {call_count}")
    print(f"New personnel: {personnel_count}")
    print(f"\nCSV files created with Action='Add' for all entries")
    print(f"\nNext steps:")
    print(f"  python validation/sync/apply_drift_sync.py --call-types \"{call_file}\" --personnel \"{personnel_file}\" --apply")
