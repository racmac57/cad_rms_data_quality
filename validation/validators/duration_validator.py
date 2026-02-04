"""
Duration Validator

Validates time duration fields (Time Spent, Time Response) for
proper format and reasonable values.
"""

import pandas as pd
import re
from typing import Dict, Any, Optional, Tuple
from datetime import timedelta
from .base_validator import BaseValidator


# Duration pattern: H:MM:SS or HH:MM:SS
DURATION_PATTERN = re.compile(r'^(\d{1,2}):(\d{2}):(\d{2})$')


class DurationValidator(BaseValidator):
    """
    Validator for duration fields.
    
    Validates:
    1. Duration format (H:MM:SS or HH:MM:SS)
    2. Duration is within reasonable bounds
    3. Flags outliers for investigation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Duration validator.
        
        Args:
            config: Optional configuration. Can override:
                - fields: List of duration fields to validate
                - max_response_minutes: Max response time before flagging (default: 120)
                - max_spent_hours: Max time spent before flagging (default: 12)
                - weight: Weight for quality scoring
        """
        config = config or {}
        config.setdefault('weight', 0.05)  # 5% of quality score
        
        super().__init__(config)
        
        self._fields = config.get('fields', ['Time Spent', 'Time Response'])
        self.max_response_minutes = config.get('max_response_minutes', 120)  # 2 hours
        self.max_spent_hours = config.get('max_spent_hours', 12)  # 12 hours
    
    @property
    def field_name(self) -> str:
        return 'Duration Fields'
    
    def _parse_duration(self, value: Any) -> Optional[timedelta]:
        """
        Parse a duration value to timedelta.
        
        Args:
            value: Value to parse (format: H:MM:SS)
            
        Returns:
            Parsed timedelta or None
        """
        if pd.isna(value):
            return None
        
        value_str = str(value).strip()
        match = DURATION_PATTERN.match(value_str)
        
        if not match:
            return None
        
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate duration fields.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (issues_dataframe, summary_dict)
        """
        issues = []
        
        case_number_field = self.config.get('case_number_field', 'ReportNumberNew')
        has_case_number = case_number_field in df.columns
        
        # Track statistics
        null_counts = {f: 0 for f in self._fields if f in df.columns}
        format_errors = {f: 0 for f in self._fields if f in df.columns}
        outliers = {f: 0 for f in self._fields if f in df.columns}
        
        for idx, row in df.iterrows():
            case_number = row[case_number_field] if has_case_number else None
            
            for field in self._fields:
                if field not in df.columns:
                    continue
                
                value = row[field]
                
                # Check for null
                if pd.isna(value):
                    null_counts[field] += 1
                    continue
                
                # Try to parse
                parsed = self._parse_duration(value)
                
                if parsed is None:
                    format_errors[field] += 1
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=value,
                        issue_type='format_error',
                        message=f"Cannot parse duration: '{value}'",
                        case_number=case_number
                    ))
                    continue
                
                # Check for outliers
                total_minutes = parsed.total_seconds() / 60
                total_hours = parsed.total_seconds() / 3600
                
                if field == 'Time Response':
                    if total_minutes > self.max_response_minutes:
                        outliers[field] += 1
                        issues.append(self._create_issue(
                            row_index=idx,
                            field=field,
                            value=value,
                            issue_type='outlier',
                            message=f"Response time {value} exceeds {self.max_response_minutes} minutes",
                            severity='warning',
                            case_number=case_number
                        ))
                
                elif field == 'Time Spent':
                    if total_hours > self.max_spent_hours:
                        outliers[field] += 1
                        issues.append(self._create_issue(
                            row_index=idx,
                            field=field,
                            value=value,
                            issue_type='outlier',
                            message=f"Time spent {value} exceeds {self.max_spent_hours} hours",
                            severity='warning',
                            case_number=case_number
                        ))
                
                # Check for negative or zero (would indicate calculation issue)
                if parsed.total_seconds() < 0:
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=value,
                        issue_type='negative_duration',
                        message=f"Negative duration: {value}",
                        case_number=case_number
                    ))
        
        # Create summary
        extra_stats = {
            'fields_validated': [f for f in self._fields if f in df.columns],
            'null_counts': null_counts,
            'format_errors': format_errors,
            'outliers': outliers,
            'thresholds': {
                'max_response_minutes': self.max_response_minutes,
                'max_spent_hours': self.max_spent_hours
            }
        }
        
        return self.issues_to_dataframe(issues), self._create_summary(df, issues, extra_stats)


def parse_duration_to_seconds(value: Any) -> Optional[float]:
    """
    Parse a duration value to total seconds.
    
    Args:
        value: Duration string (H:MM:SS format)
        
    Returns:
        Total seconds or None
    """
    if pd.isna(value):
        return None
    
    match = DURATION_PATTERN.match(str(value).strip())
    if not match:
        return None
    
    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    
    return hours * 3600 + minutes * 60 + seconds
