"""
Personnel Drift Detector

Monitors for new or changed personnel that appear in CAD data
but are not present in the reference file.
"""

import pandas as pd
from typing import Dict, Any, Optional, Set, List
from pathlib import Path
from datetime import datetime
import json


class PersonnelDriftDetector:
    """
    Detector for personnel reference data drift.
    
    Identifies:
    1. New officers/units appearing in data not in reference
    2. Inactive officers still appearing in data
    3. Officers in reference not seen in data (potential departures)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Personnel drift detector.
        
        Args:
            config: Optional configuration. Can override:
                - reference_file: Path to Assignment_Master_V2.csv
                - field_name: Column name for officer/unit
                - days_threshold: Days without appearance to flag as inactive
        """
        self.config = config or {}
        
        self.reference_file = self.config.get('reference_file')
        self.field_name = self.config.get('field_name', 'Officer')
        self.days_threshold = self.config.get('days_threshold', 90)
        
        # Load reference data
        self.all_personnel: Set[str] = set()
        self.active_personnel: Set[str] = set()
        self.inactive_personnel: Set[str] = set()
        self.reference_df: Optional[pd.DataFrame] = None
        self._load_reference()
    
    def _load_reference(self) -> None:
        """Load reference personnel from file."""
        if self.reference_file and Path(self.reference_file).exists():
            try:
                self.reference_df = pd.read_csv(self.reference_file)
                
                # Load all personnel identifiers
                name_fields = ['FULL_NAME', 'BADGE_NUMBER', 'PADDED_BADGE_NUMBER']
                for field in name_fields:
                    if field in self.reference_df.columns:
                        values = self.reference_df[field].dropna().str.strip().str.upper()
                        self.all_personnel.update(values)
                
                # Separate active/inactive
                if 'STATUS' in self.reference_df.columns:
                    active_df = self.reference_df[
                        self.reference_df['STATUS'].str.upper() == 'ACTIVE'
                    ]
                    inactive_df = self.reference_df[
                        self.reference_df['STATUS'].str.upper() == 'INACTIVE'
                    ]
                    
                    for field in name_fields:
                        if field in active_df.columns:
                            self.active_personnel.update(
                                active_df[field].dropna().str.strip().str.upper()
                            )
                        if field in inactive_df.columns:
                            self.inactive_personnel.update(
                                inactive_df[field].dropna().str.strip().str.upper()
                            )
                            
            except Exception as e:
                print(f"Warning: Could not load reference file: {e}")
    
    def _normalize_officer(self, value: str) -> str:
        """Normalize officer/unit identifier."""
        if pd.isna(value):
            return ''
        return str(value).strip().upper()
    
    def detect(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect personnel drift in dataframe.
        
        Args:
            df: DataFrame with officer/unit data
            
        Returns:
            Drift detection results dictionary
        """
        if self.field_name not in df.columns:
            return {
                'error': f"Field '{self.field_name}' not found in dataframe",
                'timestamp': datetime.now().isoformat()
            }
        
        # Get all personnel from data
        data_personnel = set()
        personnel_counts = df[self.field_name].value_counts()
        
        for val in df[self.field_name].dropna():
            normalized = self._normalize_officer(val)
            if normalized:
                data_personnel.add(normalized)
        
        # Find new personnel (in data, not in reference)
        new_personnel = []
        if self.all_personnel:
            for raw_val in df[self.field_name].dropna().unique():
                normalized = self._normalize_officer(raw_val)
                if normalized and normalized not in self.all_personnel:
                    count = personnel_counts.get(raw_val, 0)
                    new_personnel.append({
                        'value': str(raw_val).strip(),
                        'normalized': normalized,
                        'count': int(count)
                    })
            
            new_personnel.sort(key=lambda x: x['count'], reverse=True)
        
        # Find inactive personnel still appearing
        inactive_appearing = []
        for raw_val in df[self.field_name].dropna().unique():
            normalized = self._normalize_officer(raw_val)
            if normalized in self.inactive_personnel:
                count = personnel_counts.get(raw_val, 0)
                inactive_appearing.append({
                    'value': str(raw_val).strip(),
                    'count': int(count),
                    'note': 'Marked as INACTIVE in reference'
                })
        
        inactive_appearing.sort(key=lambda x: x['count'], reverse=True)
        
        # Find active personnel not appearing
        missing_active = []
        if self.active_personnel:
            for active in self.active_personnel:
                if active not in data_personnel:
                    # Find original case from reference
                    original = active
                    if self.reference_df is not None:
                        for field in ['FULL_NAME', 'BADGE_NUMBER']:
                            if field in self.reference_df.columns:
                                matches = self.reference_df[
                                    self.reference_df[field].str.upper().str.strip() == active
                                ]
                                if len(matches) > 0:
                                    original = matches.iloc[0][field]
                                    break
                    
                    missing_active.append({
                        'value': original,
                        'note': f'Active in reference but not seen in data'
                    })
        
        # Calculate statistics
        total_unique = df[self.field_name].nunique()
        reference_count = len(self.all_personnel)
        active_count = len(self.active_personnel)
        
        return {
            'detector': 'PersonnelDriftDetector',
            'field': self.field_name,
            'reference_file': str(self.reference_file) if self.reference_file else None,
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_records': len(df),
                'unique_officers': total_unique,
                'reference_count': reference_count,
                'active_in_reference': active_count,
                'inactive_in_reference': len(self.inactive_personnel),
                'new_personnel_count': len(new_personnel),
                'inactive_appearing_count': len(inactive_appearing),
                'missing_active_count': len(missing_active)
            },
            'drift_detected': len(new_personnel) > 0 or len(inactive_appearing) > 0,
            'new_personnel': new_personnel[:30],
            'inactive_appearing': inactive_appearing[:20],
            'missing_active': missing_active[:30],
            'top_officers': personnel_counts.head(20).to_dict()
        }
    
    def generate_sync_recommendations(self, results: Dict) -> List[Dict]:
        """
        Generate recommendations for syncing reference data.
        
        Args:
            results: Results from detect()
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Recommend adding new personnel
        for new_person in results.get('new_personnel', []):
            if new_person['count'] >= 5:  # Only if seen 5+ times
                recommendations.append({
                    'action': 'ADD',
                    'officer': new_person['value'],
                    'count': new_person['count'],
                    'priority': 'HIGH' if new_person['count'] >= 50 else 'MEDIUM',
                    'reason': f"Seen {new_person['count']} times but not in reference"
                })
        
        # Recommend reviewing inactive personnel appearing
        for inactive in results.get('inactive_appearing', []):
            recommendations.append({
                'action': 'VERIFY_STATUS',
                'officer': inactive['value'],
                'count': inactive['count'],
                'priority': 'HIGH',
                'reason': 'Marked INACTIVE but still appearing in data'
            })
        
        # Recommend reviewing missing active personnel
        for missing in results.get('missing_active', []):
            recommendations.append({
                'action': 'VERIFY_STATUS',
                'officer': missing['value'],
                'priority': 'LOW',
                'reason': 'Marked ACTIVE but not seen in data'
            })
        
        return recommendations
    
    def save_results(self, results: Dict, output_path: str) -> None:
        """Save drift detection results to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
