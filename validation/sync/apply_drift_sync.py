"""
Reference Data Sync Tool
Applies approved drift detection changes to reference files

Usage:
  1. Run extract_drift_reports.py to get CSV files
  2. Review and mark actions in the CSV files
  3. Run this script to apply approved changes
"""
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
import shutil


def backup_file(file_path: str):
    """Create timestamped backup of reference file"""
    path = Path(file_path)
    if not path.exists():
        return None
    
    backup_dir = path.parent / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f"{path.stem}_backup_{timestamp}{path.suffix}"
    
    shutil.copy2(path, backup_path)
    print(f"[OK] Backup created: {backup_path}")
    return backup_path


def sync_call_types(additions_csv: str, reference_file: str, dry_run: bool = True):
    """
    Sync call types: Add approved new types to reference file
    
    Args:
        additions_csv: Path to call_types_to_add_*.csv (with Action column marked)
        reference_file: Path to CallTypes_Master.csv
        dry_run: If True, only show what would be changed
    """
    
    # Load review file
    df_review = pd.read_csv(additions_csv, encoding='utf-8-sig')
    
    # Filter to approved additions
    to_add = df_review[df_review['Action'].str.upper() == 'ADD'].copy()
    
    if len(to_add) == 0:
        print("No call types marked for addition")
        return
    
    print(f"\nCall Types to Add: {len(to_add)}")
    
    # Load reference file
    df_ref = pd.read_csv(reference_file, encoding='utf-8-sig')
    print(f"Current reference file: {len(df_ref)} call types")
    
    # Prepare new rows (match reference file structure)
    # Assuming CallTypes_Master has: Incident, Incident_Norm, Category_Type, Response_Type
    new_rows = []
    for _, row in to_add.iterrows():
        new_row = {
            'Incident': row['CallType'],
            'Incident_Norm': row['CallType_Normalized'],
            'Category_Type': '',  # Will need manual categorization
            'Response_Type': ''    # Will need manual categorization
        }
        new_rows.append(new_row)
    
    df_new = pd.DataFrame(new_rows)
    
    if dry_run:
        print("\n[DRY RUN] Would add these call types:")
        print(df_new.to_string(index=False))
        print(f"\nNew total: {len(df_ref) + len(df_new)} call types")
        print("\nTo apply changes, run with --apply flag")
    else:
        # Backup original
        backup_path = backup_file(reference_file)
        
        # Append new rows
        df_combined = pd.concat([df_ref, df_new], ignore_index=True)
        
        # Sort by Incident
        df_combined = df_combined.sort_values('Incident')
        
        # Save
        df_combined.to_csv(reference_file, index=False, encoding='utf-8-sig')
        
        print(f"\n[OK] Updated {reference_file}")
        print(f"  Added: {len(df_new)} call types")
        print(f"  New total: {len(df_combined)} call types")
        print(f"  Backup: {backup_path}")
        print(f"\n[NOTE] Review and set Category_Type and Response_Type for new entries")


def sync_personnel(additions_csv: str, reference_file: str, dry_run: bool = True):
    """
    Sync personnel: Add approved new personnel to reference file
    
    Args:
        additions_csv: Path to personnel_to_add_*.csv (with Action column marked)
        reference_file: Path to Assignment_Master_V2.csv
        dry_run: If True, only show what would be changed
    """
    
    # Load review file
    df_review = pd.read_csv(additions_csv, encoding='utf-8-sig')
    
    # Filter to approved additions
    to_add = df_review[df_review['Action'].str.upper() == 'ADD'].copy()
    
    if len(to_add) == 0:
        print("No personnel marked for addition")
        return
    
    print(f"\nPersonnel to Add: {len(to_add)}")
    
    # Load reference file
    df_ref = pd.read_csv(reference_file, encoding='utf-8-sig')
    print(f"Current reference file: {len(df_ref)} personnel")
    
    # Prepare new rows (match reference file structure)
    # Will need to match actual column names in Assignment_Master_V2.csv
    new_rows = []
    for _, row in to_add.iterrows():
        new_row = {
            'FullName': row['Officer'],  # Adjust column name as needed
            'Status': row.get('Status', 'Active'),
            'Badge': '',  # Extract from name if possible
            'Notes': row.get('Notes', '')
        }
        new_rows.append(new_row)
    
    df_new = pd.DataFrame(new_rows)
    
    if dry_run:
        print("\n[DRY RUN] Would add these personnel:")
        print(df_new.to_string(index=False))
        print(f"\nNew total: {len(df_ref) + len(df_new)} personnel")
        print("\nTo apply changes, run with --apply flag")
    else:
        # Backup original
        backup_path = backup_file(reference_file)
        
        # Append new rows
        df_combined = pd.concat([df_ref, df_new], ignore_index=True)
        
        # Sort by name
        if 'FullName' in df_combined.columns:
            df_combined = df_combined.sort_values('FullName')
        
        # Save
        df_combined.to_csv(reference_file, index=False, encoding='utf-8-sig')
        
        print(f"\n[OK] Updated {reference_file}")
        print(f"  Added: {len(df_new)} personnel")
        print(f"  New total: {len(df_combined)} personnel")
        print(f"  Backup: {backup_path}")


def main():
    parser = argparse.ArgumentParser(description='Sync reference files with approved drift changes')
    parser.add_argument('--call-types', help='Path to reviewed call_types_to_add_*.csv')
    parser.add_argument('--personnel', help='Path to reviewed personnel_to_add_*.csv')
    parser.add_argument('--call-types-ref', 
                       default=r'C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\CallTypes_Master.csv',
                       help='Path to CallTypes_Master.csv')
    parser.add_argument('--personnel-ref',
                       default=r'C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Personnel\Assignment_Master_V2.csv',
                       help='Path to Assignment_Master_V2.csv')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    
    args = parser.parse_args()
    
    if not args.call_types and not args.personnel:
        print("Error: Specify --call-types and/or --personnel CSV file")
        parser.print_help()
        return
    
    print("=" * 70)
    print("Reference Data Sync Tool")
    print("=" * 70)
    
    if not args.apply:
        print("\n[!] DRY RUN MODE - No changes will be made")
        print("Add --apply flag to actually update reference files\n")
    
    # Sync call types
    if args.call_types:
        print("\n" + "=" * 70)
        print("CALL TYPES SYNC")
        print("=" * 70)
        sync_call_types(args.call_types, args.call_types_ref, dry_run=not args.apply)
    
    # Sync personnel
    if args.personnel:
        print("\n" + "=" * 70)
        print("PERSONNEL SYNC")
        print("=" * 70)
        sync_personnel(args.personnel, args.personnel_ref, dry_run=not args.apply)
    
    print("\n" + "=" * 70)
    if args.apply:
        print("[OK] Sync complete!")
        print("\nNext steps:")
        print("  1. Review the updated reference files")
        print("  2. Run validation again to verify changes")
        print("  3. Commit changes to git")
    else:
        print("Dry run complete. Review proposed changes above.")
        print("Run with --apply to make actual changes.")


if __name__ == '__main__':
    main()
