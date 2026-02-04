"""
DateTime Validator

Validates date and time fields for proper format, valid ranges,
and temporal sequence logic.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, date
from .base_validator import BaseValidator


class DateTimeValidator(BaseValidator):
    """
    Validator for date/time fields.
    
    Validates:
    1. Date format (YYYY-MM-DD HH:MM:SS)
    2. Date is within valid range
    3. Date is not in the future
    4. Temporal sequence is logical (Call ≤ Dispatch ≤ Out ≤ In)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize DateTime validator.
        
        Args:
            config: Optional configuration. Can override:
                - fields: List of datetime fields to validate
                - min_date: Minimum valid date (default: 2019-01-01)
                - max_date: Maximum valid date (default: today)
                - sequence_fields: Ordered list of fields for sequence validation
                - weight: Weight for quality scoring
        """
        config = config or {}
        config.setdefault('weight', 0.15)  # 15% of quality score
        
        super().__init__(config)
        
        self._fields = config.get('fields', [
            'Time of Call',
            'Time Dispatched',
            'Time Out',
            'Time In'
        ])
        
        self.sequence_fields = config.get('sequence_fields', [
            'Time of Call',
            'Time Dispatched',
            'Time Out',
            'Time In'
        ])
        
        self.min_date = config.get('min_date', datetime(2019, 1, 1))
        self.max_date = config.get('max_date', datetime.now())
    
    @property
    def field_name(self) -> str:
        return 'DateTime Fields'
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """
        Parse a datetime value.
        
        Args:
            value: Value to parse
            
        Returns:
            Parsed datetime or None
        """
        if pd.isna(value):
            return None
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        
        value_str = str(value).strip()
        
        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M',
            '%m/%d/%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate datetime fields.
        
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
        range_errors = {f: 0 for f in self._fields if f in df.columns}
        future_dates = 0
        sequence_errors = 0
        
        for idx, row in df.iterrows():
            case_number = row[case_number_field] if has_case_number else None
            
            parsed_times = {}
            
            # Validate each datetime field
            for field in self._fields:
                if field not in df.columns:
                    continue
                
                value = row[field]
                
                # Check for null
                if pd.isna(value):
                    null_counts[field] += 1
                    continue
                
                # Try to parse
                parsed = self._parse_datetime(value)
                
                if parsed is None:
                    format_errors[field] += 1
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=value,
                        issue_type='format_error',
                        message=f"Cannot parse datetime: '{value}'",
                        case_number=case_number
                    ))
                    continue
                
                parsed_times[field] = parsed
                
                # Check date range
                if parsed < self.min_date:
                    range_errors[field] += 1
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=value,
                        issue_type='date_too_old',
                        message=f"Date {parsed.date()} is before {self.min_date.date()}",
                        severity='warning',
                        case_number=case_number
                    ))
                
                if parsed > self.max_date:
                    future_dates += 1
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=value,
                        issue_type='future_date',
                        message=f"Date {parsed.date()} is in the future",
                        case_number=case_number
                    ))
            
            # Check temporal sequence
            prev_time = None
            prev_field = None
            for field in self.sequence_fields:
                if field in parsed_times:
                    current_time = parsed_times[field]
                    if prev_time is not None and current_time < prev_time:
                        sequence_errors += 1
                        issues.append(self._create_issue(
                            row_index=idx,
                            field=field,
                            value=row.get(field),
                            issue_type='sequence_error',
                            message=f"{field} ({current_time}) is before {prev_field} ({prev_time})",
                            severity='warning',
                            case_number=case_number
                        ))
                    prev_time = current_time
                    prev_field = field
        
        # Create summary
        extra_stats = {
            'fields_validated': [f for f in self._fields if f in df.columns],
            'null_counts': null_counts,
            'format_errors': format_errors,
            'range_errors': range_errors,
            'future_dates': future_dates,
            'sequence_errors': sequence_errors,
            'date_range': f"{self.min_date.date()} to {self.max_date.date()}"
        }
        
        return self.issues_to_dataframe(issues), self._create_summary(df, issues, extra_stats)
