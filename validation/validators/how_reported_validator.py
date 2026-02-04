"""
How Reported (Call Source) Validator

Validates that the 'How Reported' field contains only valid domain values.
This is a critical field for dashboard filtering.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple
from .base_validator import DomainValidator


# Valid values after normalization (from enhanced_esri_output_generator.py)
VALID_HOW_REPORTED = [
    '9-1-1',
    'Phone',
    'Walk-In',
    'Self-Initiated',
    'Radio',
    'eMail',
    'Mail',
    'Other - See Notes',
    'Fax',
    'Teletype',
    'Virtual Patrol',
    'Canceled Call'
]


class HowReportedValidator(DomainValidator):
    """
    Validator for the 'How Reported' (Call Source) field.
    
    Checks that all values are in the valid domain after normalization.
    This field is critical for dashboard dropdown filters.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize HowReported validator.
        
        Args:
            config: Optional configuration. Can override:
                - valid_values: List of valid values
                - field_name: Column name to validate
                - weight: Weight for quality scoring
        """
        config = config or {}
        
        valid_values = config.get('valid_values', VALID_HOW_REPORTED)
        config.setdefault('weight', 0.15)  # 15% of quality score
        config.setdefault('allow_null', False)
        
        super().__init__(valid_values=valid_values, case_sensitive=False, config=config)
        
        self._field_name = config.get('field_name', 'How Reported')
    
    @property
    def field_name(self) -> str:
        return self._field_name
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate How Reported values.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (issues_dataframe, summary_dict)
        """
        issues_df, summary = super().validate(df)
        
        # Add field-specific analysis
        if self.field_name in df.columns:
            # Check for values that might be pre-normalization typos
            raw_values = df[self.field_name].dropna().unique()
            potentially_fixable = []
            
            for val in raw_values:
                val_upper = str(val).upper()
                if val_upper not in [v.upper() for v in VALID_HOW_REPORTED]:
                    # Check for common patterns that could be normalized
                    if '911' in val_upper or '9-1-1' in val_upper:
                        potentially_fixable.append((val, 'May be 911 variant'))
                    elif 'PHONE' in val_upper:
                        potentially_fixable.append((val, 'May be Phone variant'))
                    elif 'WALK' in val_upper:
                        potentially_fixable.append((val, 'May be Walk-In variant'))
            
            summary['potentially_fixable'] = potentially_fixable[:10]
            summary['reference'] = 'enhanced_esri_output_generator.py HOW_REPORTED_MAPPING'
        
        return issues_df, summary


def get_how_reported_mapping() -> Dict[str, str]:
    """
    Return the mapping of raw values to normalized values.
    
    This is a subset of the production mapping for reference.
    For the complete mapping, see enhanced_esri_output_generator.py.
    """
    return {
        # 911 variants
        '911': '9-1-1',
        '9-1-1': '9-1-1',
        '9/1/1': '9-1-1',
        '91-1': '9-1-1',
        '9 1 1': '9-1-1',
        '911 call': '9-1-1',
        '9-1-1 call': '9-1-1',
        
        # Phone variants
        'phone': 'Phone',
        'p': 'Phone',
        'ph': 'Phone',
        'telephone': 'Phone',
        'phone call': 'Phone',
        'phone/911': 'Phone',
        'hackensack': 'Phone',
        
        # Walk-in variants
        'walk-in': 'Walk-In',
        'walk in': 'Walk-In',
        'w': 'Walk-In',
        'walkin': 'Walk-In',
        'walk-in/lobby': 'Walk-In',
        
        # Radio variants
        'radio': 'Radio',
        'r': 'Radio',
        'officer': 'Radio',
        
        # Self-initiated
        'self-initiated': 'Self-Initiated',
        'self initiated': 'Self-Initiated',
        's': 'Self-Initiated',
        
        # Other
        'email': 'eMail',
        'e-mail': 'eMail',
        'mail': 'Mail',
        'fax': 'Fax',
        'teletype': 'Teletype',
        'other': 'Other - See Notes',
        'other - see notes': 'Other - See Notes',
    }
