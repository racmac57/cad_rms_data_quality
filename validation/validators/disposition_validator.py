"""
Disposition Validator

Validates that the 'Disposition' field contains only valid domain values.
This field indicates call outcome and is critical for reporting.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple
from .base_validator import DomainValidator


# Valid values after normalization (synced with enhanced_esri_output_generator.py valid_dispositions)
# Updated 2026-02-04: Added missing values that caused 87,896 false positives
VALID_DISPOSITIONS = [
    # Standard dispositions
    'Advised',
    'Arrest',
    'Assisted',
    'Canceled',
    'Checked OK',
    'Cleared',
    'Complete',
    'Curbside Warning',  # Added - was flagging 9 records as invalid
    'Dispersed',
    'Field Contact',     # Added - was flagging 86 records as invalid
    'G.O.A.',            # Gone on Arrival
    'Issued',
    'Other - See Notes',
    'Record Only',
    'See Report',        # Added - was flagging 86,777 records as invalid
    'See Supplement',    # Added - was flagging 1,024 records as invalid
    'Temp. Settled',
    'TOT - See Notes',   # Turned Over To
    'Transported',
    'Unable to Locate',
    'Unfounded',
    # Legacy values kept for backwards compatibility
    'Report',
    'No Action Needed',
    'Referred',
    'Citation Issued'
]


class DispositionValidator(DomainValidator):
    """
    Validator for the 'Disposition' field.
    
    Checks that all disposition values are in the valid domain.
    Disposition indicates how the call was resolved.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Disposition validator.
        
        Args:
            config: Optional configuration. Can override:
                - valid_values: List of valid values
                - field_name: Column name to validate
                - weight: Weight for quality scoring
        """
        config = config or {}
        
        valid_values = config.get('valid_values', VALID_DISPOSITIONS)
        config.setdefault('weight', 0.15)  # 15% of quality score
        config.setdefault('allow_null', False)
        
        super().__init__(valid_values=valid_values, case_sensitive=False, config=config)
        
        self._field_name = config.get('field_name', 'Disposition')
    
    @property
    def field_name(self) -> str:
        return self._field_name
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate Disposition values.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (issues_dataframe, summary_dict)
        """
        issues_df, summary = super().validate(df)
        
        # Add field-specific analysis
        if self.field_name in df.columns:
            # Analyze disposition distribution for anomalies
            value_counts = df[self.field_name].value_counts()
            total = len(df)
            
            # Flag if any single disposition is > 70% (unusual)
            for disp, count in value_counts.items():
                pct = count / total * 100
                if pct > 70:
                    summary['warning'] = f"'{disp}' accounts for {pct:.1f}% of all dispositions"
            
            # Check for values that might be pre-normalization
            raw_values = df[self.field_name].dropna().unique()
            potentially_fixable = []
            
            for val in raw_values:
                val_upper = str(val).upper()
                if val_upper not in [v.upper() for v in VALID_DISPOSITIONS]:
                    # Check for common patterns
                    if 'COMPLETE' in val_upper:
                        potentially_fixable.append((val, 'May be Complete variant'))
                    elif 'ARREST' in val_upper:
                        potentially_fixable.append((val, 'May be Arrest variant'))
                    elif 'REPORT' in val_upper:
                        potentially_fixable.append((val, 'May be Report variant'))
            
            summary['potentially_fixable'] = potentially_fixable[:10]
            summary['reference'] = 'enhanced_esri_output_generator.py DISPOSITION_MAPPING'
        
        return issues_df, summary


def get_disposition_mapping() -> Dict[str, str]:
    """
    Return the mapping of raw values to normalized values.
    
    This is a subset of the production mapping for reference.
    For the complete mapping, see enhanced_esri_output_generator.py.
    """
    return {
        # Complete variants
        'complete': 'Complete',
        'completed': 'Complete',
        'done': 'Complete',
        
        # Assisted variants
        'assisted': 'Assisted',
        'assist': 'Assisted',
        
        # Arrest variants
        'arrest': 'Arrest',
        'arrested': 'Arrest',
        'arrest made': 'Arrest',
        
        # GOA variants
        'goa': 'G.O.A.',
        'g.o.a.': 'G.O.A.',
        'gone on arrival': 'G.O.A.',
        
        # UTL variants
        'utl': 'Unable to Locate',
        'unable to locate': 'Unable to Locate',
        
        # Canceled variants
        'canceled': 'Canceled',
        'cancelled': 'Canceled',
        'cancel': 'Canceled',
        
        # Report variants
        'report': 'Report',
        'report taken': 'Report',
        'report only': 'Record Only',
        
        # Other
        'other': 'Other - See Notes',
        'see notes': 'Other - See Notes',
        'tot': 'TOT - See Notes',
        'turned over to': 'TOT - See Notes',
    }
