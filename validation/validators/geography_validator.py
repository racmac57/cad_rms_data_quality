"""
Geography Validator

Validates address and location fields for proper format
and domain values.
"""

import pandas as pd
import re
from typing import Dict, Any, Optional, Tuple, List
from .base_validator import BaseValidator


# Valid Hackensack ZIP codes
VALID_ZIPS = {'07601', '07602', '07606'}

# Address pattern
ADDRESS_PATTERN = re.compile(
    r'^.+,\s*Hackensack,\s*NJ,?\s*\d{5}',
    re.IGNORECASE
)

# Police HQ address (exclude from response time calculations)
POLICE_HQ_ADDRESSES = [
    '225 STATE STREET',
    '225 STATE ST',
]


class GeographyValidator(BaseValidator):
    """
    Validator for address/location fields.
    
    Validates:
    1. Address contains Hackensack, NJ
    2. ZIP code is in valid Hackensack range
    3. Identifies Police HQ addresses for exclusion
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Geography validator.
        
        Args:
            config: Optional configuration. Can override:
                - field_name: Column name to validate
                - weight: Weight for quality scoring
                - valid_zips: List of valid ZIP codes
        """
        config = config or {}
        config.setdefault('weight', 0.05)  # 5% of quality score
        config.setdefault('allow_null', False)
        
        super().__init__(config)
        
        self._field_name = config.get('field_name', 'FullAddress2')
        self.valid_zips = set(config.get('valid_zips', VALID_ZIPS))
    
    @property
    def field_name(self) -> str:
        return self._field_name
    
    def _is_police_hq(self, address: str) -> bool:
        """Check if address is Police HQ."""
        if pd.isna(address):
            return False
        
        address_upper = str(address).upper()
        for hq in POLICE_HQ_ADDRESSES:
            if hq in address_upper:
                return True
        return False
    
    def _extract_zip(self, address: str) -> Optional[str]:
        """Extract ZIP code from address."""
        if pd.isna(address):
            return None
        
        # Look for 5-digit ZIP
        match = re.search(r'\b(\d{5})\b', str(address))
        if match:
            return match.group(1)
        return None
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate geography fields.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (issues_dataframe, summary_dict)
        """
        issues = []
        field = self.field_name
        
        if field not in df.columns:
            return self.issues_to_dataframe(issues), self._create_summary(df, issues)
        
        case_number_field = self.config.get('case_number_field', 'ReportNumberNew')
        has_case_number = case_number_field in df.columns
        
        # Track statistics
        null_count = 0
        not_hackensack = 0
        invalid_zip = 0
        police_hq_count = 0
        
        for idx, row in df.iterrows():
            value = row[field]
            case_number = row[case_number_field] if has_case_number else None
            
            # Check for null
            if pd.isna(value):
                null_count += 1
                if not self.config.get('allow_null', False):
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=value,
                        issue_type='null_value',
                        message='Address is null/empty',
                        case_number=case_number
                    ))
                continue
            
            value_str = str(value)
            value_upper = value_str.upper()
            
            # Check if Police HQ (informational only)
            if self._is_police_hq(value_str):
                police_hq_count += 1
            
            # Check if Hackensack
            if 'HACKENSACK' not in value_upper:
                not_hackensack += 1
                issues.append(self._create_issue(
                    row_index=idx,
                    field=field,
                    value=value_str,
                    issue_type='not_hackensack',
                    message=f"Address not in Hackensack: '{value_str[:50]}...'",
                    severity='warning',
                    case_number=case_number
                ))
                continue
            
            # Check if NJ
            if 'NJ' not in value_upper and 'NEW JERSEY' not in value_upper:
                issues.append(self._create_issue(
                    row_index=idx,
                    field=field,
                    value=value_str,
                    issue_type='not_nj',
                    message=f"Address not in NJ: '{value_str[:50]}...'",
                    severity='warning',
                    case_number=case_number
                ))
            
            # Check ZIP code
            zip_code = self._extract_zip(value_str)
            if zip_code and zip_code not in self.valid_zips:
                invalid_zip += 1
                issues.append(self._create_issue(
                    row_index=idx,
                    field=field,
                    value=value_str,
                    issue_type='invalid_zip',
                    message=f"ZIP {zip_code} not in Hackensack range",
                    severity='warning',
                    case_number=case_number
                ))
        
        # Create summary
        extra_stats = {
            'null_count': null_count,
            'not_hackensack': not_hackensack,
            'invalid_zip': invalid_zip,
            'police_hq_count': police_hq_count,
            'valid_zips': list(self.valid_zips),
            'unique_addresses': df[field].nunique() if field in df.columns else 0
        }
        
        return self.issues_to_dataframe(issues), self._create_summary(df, issues, extra_stats)


def is_police_hq_address(address: str) -> bool:
    """
    Check if an address is the Police HQ.
    
    Used to exclude from response time calculations.
    
    Args:
        address: Address string
        
    Returns:
        True if Police HQ, False otherwise
    """
    if pd.isna(address):
        return False
    
    address_upper = str(address).upper()
    for hq in POLICE_HQ_ADDRESSES:
        if hq in address_upper:
            return True
    return False
