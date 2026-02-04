"""
Call Type Drift Detector

Monitors for new or changed call types that appear in CAD data
but are not present in the reference file.
"""

import pandas as pd
from typing import Dict, Any, Optional, Set, List, Tuple
from pathlib import Path
from datetime import datetime
import json
import re


# Statute suffix pattern for normalization
STATUTE_SUFFIX_RE = re.compile(r'\s*-\s*((?:2C|39):[0-9A-Za-z.\-\s]+)\s*$')


class CallTypeDriftDetector:
    """
    Detector for call type reference data drift.
    
    Identifies:
    1. New call types in data not in reference
    2. Call types in reference not seen in data
    3. Frequency changes (distribution shift)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize CallType drift detector.
        
        Args:
            config: Optional configuration. Can override:
                - reference_file: Path to CallTypes_Master.csv
                - field_name: Column name for call types
                - days_threshold: Days without appearance to flag as unused
        """
        self.config = config or {}
        
        self.reference_file = self.config.get('reference_file')
        self.field_name = self.config.get('field_name', 'Incident')
        self.days_threshold = self.config.get('days_threshold', 90)
        
        # Load reference data
        self.reference_call_types: Set[str] = set()
        self.reference_df: Optional[pd.DataFrame] = None
        self._load_reference()
    
    def _load_reference(self) -> None:
        """Load reference call types from file."""
        if self.reference_file and Path(self.reference_file).exists():
            try:
                # Read CSV with explicit dtype for Incident column
                self.reference_df = pd.read_csv(self.reference_file, dtype={'Incident': str})
                if 'Incident' in self.reference_df.columns:
                    # Filter out rows where Incident is numeric (like bare "1")
                    valid_incidents = self.reference_df['Incident'].dropna()
                    # Remove rows that are just numbers
                    valid_incidents = valid_incidents[~valid_incidents.str.match(r'^\d+$')]
                    self.reference_call_types = set(
                        valid_incidents.str.strip().str.upper()
                    )
            except Exception as e:
                print(f"Warning: Could not load reference file: {e}")
    
    def _normalize_call_type(self, value: str) -> str:
        """
        Normalize a call type for comparison.
        
        Removes statute suffix and normalizes whitespace.
        """
        if pd.isna(value):
            return ''
        
        normalized = str(value).strip().upper()
        
        # Remove statute suffix
        match = STATUTE_SUFFIX_RE.search(normalized)
        if match:
            normalized = normalized[:match.start()].strip()
        
        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def detect(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect call type drift in dataframe.
        
        Args:
            df: DataFrame with call type data
            
        Returns:
            Drift detection results dictionary
        """
        if self.field_name not in df.columns:
            return {
                'error': f"Field '{self.field_name}' not found in dataframe",
                'timestamp': datetime.now().isoformat()
            }
        
        # Get all call types from data
        data_call_types = set()
        data_call_type_counts = df[self.field_name].value_counts()
        
        for val in df[self.field_name].dropna():
            normalized = self._normalize_call_type(val)
            if normalized:
                data_call_types.add(normalized)
        
        # Find new call types (in data, not in reference)
        new_call_types = []
        if self.reference_call_types:
            for raw_val in df[self.field_name].dropna().unique():
                normalized = self._normalize_call_type(raw_val)
                if normalized and normalized not in self.reference_call_types:
                    count = data_call_type_counts.get(raw_val, 0)
                    new_call_types.append({
                        'value': str(raw_val).strip(),
                        'normalized': normalized,
                        'count': int(count)
                    })
            
            # Sort by count (highest first)
            new_call_types.sort(key=lambda x: x['count'], reverse=True)
        
        # Find unused call types (in reference, not in data)
        unused_call_types = []
        if self.reference_call_types:
            for ref_type in self.reference_call_types:
                if ref_type not in data_call_types:
                    # Find original case from reference
                    original = ref_type
                    if self.reference_df is not None:
                        matches = self.reference_df[
                            self.reference_df['Incident'].str.upper().str.strip() == ref_type
                        ]
                        if len(matches) > 0:
                            original = matches.iloc[0]['Incident']
                    
                    unused_call_types.append({
                        'value': original,
                        'normalized': ref_type,
                        'note': f'Not seen in data (threshold: {self.days_threshold} days)'
                    })
        
        # Calculate statistics
        total_unique = df[self.field_name].nunique()
        reference_count = len(self.reference_call_types)
        coverage = len(data_call_types & self.reference_call_types) / reference_count * 100 if reference_count > 0 else 0
        
        return {
            'detector': 'CallTypeDriftDetector',
            'field': self.field_name,
            'reference_file': str(self.reference_file) if self.reference_file else None,
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_records': len(df),
                'unique_call_types': total_unique,
                'reference_count': reference_count,
                'coverage_pct': round(coverage, 1),
                'new_call_types_count': len(new_call_types),
                'unused_call_types_count': len(unused_call_types)
            },
            'drift_detected': len(new_call_types) > 0 or len(unused_call_types) > 0,
            'new_call_types': new_call_types[:50],  # Limit to 50
            'unused_call_types': unused_call_types[:50],
            'top_call_types': data_call_type_counts.head(20).to_dict()
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
        
        # Recommend adding new call types
        for new_type in results.get('new_call_types', []):
            if new_type['count'] >= 10:  # Only recommend if seen 10+ times
                recommendations.append({
                    'action': 'ADD',
                    'call_type': new_type['value'],
                    'count': new_type['count'],
                    'priority': 'HIGH' if new_type['count'] >= 100 else 'MEDIUM',
                    'reason': f"Seen {new_type['count']} times but not in reference"
                })
        
        # Recommend reviewing unused call types
        for unused in results.get('unused_call_types', []):
            recommendations.append({
                'action': 'REVIEW',
                'call_type': unused['value'],
                'priority': 'LOW',
                'reason': 'In reference but not seen in data'
            })
        
        return recommendations
    
    def save_results(self, results: Dict, output_path: str) -> None:
        """Save drift detection results to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
