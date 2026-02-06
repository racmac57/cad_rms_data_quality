"""
Case Number (ReportNumberNew) Validator

Validates that case numbers follow the YY-NNNNNN format.
This is the primary identifier for all CAD records.
"""

import pandas as pd
import re
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from .base_validator import FormatValidator


# Case number pattern: YY-NNNNNN (2-digit year, dash, 6-digit sequence)
CASE_NUMBER_PATTERN = r'^\d{2}-\d{6}$'

# Valid year range
VALID_YEAR_MIN = 19  # 2019
VALID_YEAR_MAX = 26  # 2026


class CaseNumberValidator(FormatValidator):
    """
    Validator for the 'ReportNumberNew' (Case Number) field.
    
    Validates:
    1. Format matches YY-NNNNNN pattern
    2. Year prefix is within valid range (19-26)
    3. Optional: Year matches Time of Call year
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Case Number validator.
        
        Args:
            config: Optional configuration. Can override:
                - pattern: Regex pattern for case number
                - field_name: Column name to validate
                - weight: Weight for quality scoring
                - validate_year_match: Whether to check year against Time of Call
        """
        config = config or {}
        
        pattern = config.get('pattern', CASE_NUMBER_PATTERN)
        config.setdefault('weight', 0.20)  # 20% of quality score
        config.setdefault('allow_null', False)
        config.setdefault('validate_year_match', True)
        
        super().__init__(pattern=pattern, config=config)
        
        self._field_name = config.get('field_name', 'ReportNumberNew')
        self.time_field = config.get('time_field', 'Time of Call')
    
    @property
    def field_name(self) -> str:
        return self._field_name
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate case numbers.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (issues_dataframe, summary_dict)
        """
        issues = []
        field = self.field_name
        
        if field not in df.columns:
            return self.issues_to_dataframe(issues), self._create_summary(df, issues)
        
        # Check for time field to validate year match
        has_time_field = self.time_field in df.columns and self.config.get('validate_year_match')
        
        for idx, row in df.iterrows():
            value = row[field]
            case_number = str(value) if pd.notna(value) else None
            
            # Check for null
            if pd.isna(value):
                issues.append(self._create_issue(
                    row_index=idx,
                    field=field,
                    value=value,
                    issue_type='null_value',
                    message='Case number is null/empty',
                    case_number=case_number
                ))
                continue
            
            value_str = str(value)
            
            # Check format
            if not self.compiled_pattern.match(value_str):
                # Try to identify specific format issue
                if '-' not in value_str:
                    issue_msg = f"Missing dash separator in '{value_str}'"
                elif not value_str[:2].isdigit():
                    issue_msg = f"Year prefix not numeric in '{value_str}'"
                elif len(value_str.split('-')[1]) != 6:
                    issue_msg = f"Sequence number not 6 digits in '{value_str}'"
                else:
                    issue_msg = f"'{value_str}' does not match YY-NNNNNN format"
                
                issues.append(self._create_issue(
                    row_index=idx,
                    field=field,
                    value=value_str,
                    issue_type='format_error',
                    message=issue_msg,
                    case_number=case_number
                ))
                continue
            
            # Check year range
            year_prefix = int(value_str[:2])
            if year_prefix < VALID_YEAR_MIN or year_prefix > VALID_YEAR_MAX:
                issues.append(self._create_issue(
                    row_index=idx,
                    field=field,
                    value=value_str,
                    issue_type='invalid_year',
                    message=f"Year prefix {year_prefix} outside valid range ({VALID_YEAR_MIN}-{VALID_YEAR_MAX})",
                    severity='warning',
                    case_number=case_number
                ))
            
            # Validate year matches Time of Call
            if has_time_field:
                time_value = row[self.time_field]
                if pd.notna(time_value):
                    try:
                        if isinstance(time_value, str):
                            call_year = int(time_value[:4])
                        else:
                            call_year = time_value.year
                        
                        expected_prefix = call_year % 100
                        if year_prefix != expected_prefix:
                            issues.append(self._create_issue(
                                row_index=idx,
                                field=field,
                                value=value_str,
                                issue_type='year_mismatch',
                                message=f"Case year ({year_prefix}) doesn't match call year ({expected_prefix})",
                                severity='warning',
                                case_number=case_number
                            ))
                    except (ValueError, AttributeError):
                        pass  # Skip if time parsing fails
        
        # Create summary with statistics
        if field in df.columns:
            # Check for duplicates
            duplicates = df[field].value_counts()
            duplicate_count = (duplicates > 1).sum()
            max_duplicates = duplicates.max() if len(duplicates) > 0 else 0
            
            # Get year distribution
            year_dist = {}
            for val in df[field].dropna():
                try:
                    yr = str(val)[:2]
                    year_dist[yr] = year_dist.get(yr, 0) + 1
                except:
                    pass
            
            extra_stats = {
                'duplicate_case_numbers': duplicate_count,
                'max_records_per_case': max_duplicates,
                'year_distribution': year_dist,
                'note': 'Duplicates may be valid (multi-officer calls)'
            }
        else:
            extra_stats = {}
        
        invalid_values = self.get_unique_invalid_values(issues)
        extra_stats['invalid_samples'] = invalid_values[:20]
        
        return self.issues_to_dataframe(issues), self._create_summary(df, issues, extra_stats)


def normalize_case_number(value: Any) -> Optional[str]:
    """
    Normalize a case number to YY-NNNNNN format.
    
    Handles common issues like:
    - Missing dashes: "19000001" -> "19-000001"
    - Decimal artifacts: "19000001.0" -> "19-000001"
    - Extra whitespace
    
    Args:
        value: Raw case number value
        
    Returns:
        Normalized case number or None if cannot be fixed
    """
    if pd.isna(value):
        return None
    
    value_str = str(value).strip()
    
    # Remove decimal artifacts from Excel
    if '.' in value_str:
        value_str = value_str.split('.')[0]
    
    # If already valid, return as-is
    if re.match(CASE_NUMBER_PATTERN, value_str):
        return value_str
    
    # Try to fix missing dash
    if len(value_str) == 8 and value_str.isdigit():
        return f"{value_str[:2]}-{value_str[2:]}"
    
    # Cannot normalize
    return None
