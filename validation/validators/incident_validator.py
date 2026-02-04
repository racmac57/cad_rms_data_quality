"""
Incident (Call Type) Validator

Validates that the 'Incident' field contains valid call types
and checks for proper format including statute suffixes.
"""

import pandas as pd
import re
from typing import Dict, Any, Optional, Tuple, Set
from pathlib import Path
from .base_validator import BaseValidator


# Pattern for NJ statute suffixes
STATUTE_SUFFIX_PATTERN = re.compile(r'\s*-\s*((?:2C|39):[0-9A-Za-z.\-\s]+)\s*$')


class IncidentValidator(BaseValidator):
    """
    Validator for the 'Incident' (Call Type) field.
    
    Validates:
    1. Call type exists in master reference file
    2. Statute suffix format is valid (if present)
    3. No unexpected trailing/leading whitespace
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Incident validator.
        
        Args:
            config: Optional configuration. Can override:
                - reference_file: Path to CallTypes_Master.csv
                - field_name: Column name to validate
                - weight: Weight for quality scoring
                - allow_unknown: Whether to allow values not in reference
        """
        config = config or {}
        config.setdefault('weight', 0.15)  # 15% of quality score
        config.setdefault('allow_null', False)
        config.setdefault('allow_unknown', False)
        
        super().__init__(config)
        
        self._field_name = config.get('field_name', 'Incident')
        self.reference_file = config.get('reference_file')
        
        # Load reference data
        self.valid_call_types: Set[str] = set()
        self._load_reference()
    
    @property
    def field_name(self) -> str:
        return self._field_name
    
    def _load_reference(self) -> None:
        """Load valid call types from reference file."""
        if self.reference_file and Path(self.reference_file).exists():
            try:
                ref_df = pd.read_csv(self.reference_file)
                if 'Incident' in ref_df.columns:
                    self.valid_call_types = set(
                        ref_df['Incident'].dropna().str.upper().str.strip()
                    )
            except Exception as e:
                print(f"Warning: Could not load reference file: {e}")
        
        # If no reference loaded, use empty set (will flag all as unknown)
        if not self.valid_call_types:
            # Provide default set of common call types
            self.valid_call_types = set()
    
    def _normalize_call_type(self, value: str) -> str:
        """
        Normalize a call type for comparison.
        
        - Strips whitespace
        - Converts to uppercase
        - Removes statute suffix for base comparison
        """
        normalized = str(value).strip().upper()
        
        # Remove statute suffix for base comparison
        match = STATUTE_SUFFIX_PATTERN.search(normalized)
        if match:
            normalized = normalized[:match.start()].strip()
        
        return normalized
    
    def _validate_statute_format(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate the format of a statute suffix if present.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        match = STATUTE_SUFFIX_PATTERN.search(value)
        if not match:
            return True, None  # No statute, that's fine
        
        statute = match.group(1)
        
        # Check for valid NJ statute format (2C:XX-X or 39:X-X)
        if not re.match(r'^(2C|39):[0-9]+', statute):
            return False, f"Invalid statute format: {statute}"
        
        return True, None
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate Incident values.
        
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
        allow_unknown = self.config.get('allow_unknown', False)
        
        unknown_call_types = set()
        whitespace_issues = 0
        statute_issues = 0
        
        for idx, row in df.iterrows():
            value = row[field]
            case_number = row[case_number_field] if has_case_number else None
            
            # Check for null
            if pd.isna(value):
                if not self.config.get('allow_null', False):
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=value,
                        issue_type='null_value',
                        message='Incident is null/empty',
                        case_number=case_number
                    ))
                continue
            
            value_str = str(value)
            
            # Check for whitespace issues
            if value_str != value_str.strip():
                whitespace_issues += 1
                issues.append(self._create_issue(
                    row_index=idx,
                    field=field,
                    value=value_str,
                    issue_type='whitespace',
                    message='Incident has leading/trailing whitespace',
                    severity='warning',
                    case_number=case_number
                ))
            
            # Check statute format
            is_valid_statute, statute_error = self._validate_statute_format(value_str)
            if not is_valid_statute:
                statute_issues += 1
                issues.append(self._create_issue(
                    row_index=idx,
                    field=field,
                    value=value_str,
                    issue_type='invalid_statute',
                    message=statute_error,
                    severity='warning',
                    case_number=case_number
                ))
            
            # Check if call type exists in reference
            if self.valid_call_types and not allow_unknown:
                normalized = self._normalize_call_type(value_str)
                if normalized not in self.valid_call_types:
                    unknown_call_types.add(value_str.strip())
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=value_str,
                        issue_type='unknown_call_type',
                        message=f"Call type not in reference: '{value_str}'",
                        severity='warning',
                        case_number=case_number
                    ))
        
        # Create summary
        extra_stats = {
            'reference_file': str(self.reference_file) if self.reference_file else 'None',
            'reference_count': len(self.valid_call_types),
            'unknown_call_types': list(unknown_call_types)[:20],
            'whitespace_issues': whitespace_issues,
            'statute_format_issues': statute_issues,
            'unique_values': df[field].nunique() if field in df.columns else 0
        }
        
        return self.issues_to_dataframe(issues), self._create_summary(df, issues, extra_stats)


def normalize_call_type(value: str) -> str:
    """
    Normalize a call type value.
    
    - Strips whitespace
    - Collapses multiple spaces to single space
    - Standardizes dashes
    
    Args:
        value: Raw call type value
        
    Returns:
        Normalized call type
    """
    if pd.isna(value):
        return ''
    
    result = str(value).strip()
    result = re.sub(r'\s+', ' ', result)  # Collapse whitespace
    result = re.sub(r'\s*-\s*', ' - ', result)  # Standardize dashes
    
    return result
