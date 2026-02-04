"""
Derived Field Validator

Validates that derived/calculated fields are consistent
with their source fields.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from .base_validator import BaseValidator


# Month name mapping
MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}

# Day of week mapping
DAY_NAMES = {
    0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
    4: 'Friday', 5: 'Saturday', 6: 'Sunday'
}


class DerivedFieldValidator(BaseValidator):
    """
    Validator for derived/calculated fields.
    
    Validates consistency between:
    - cYear and Time of Call year
    - cMonth and Time of Call month
    - Hour_Calc and Time of Call hour
    - DayofWeek and Time of Call day
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize DerivedField validator.
        
        Args:
            config: Optional configuration. Can override:
                - source_field: Source datetime field
                - derived_fields: List of derived fields to check
                - weight: Weight for quality scoring
        """
        config = config or {}
        config.setdefault('weight', 0.05)  # 5% of quality score
        
        super().__init__(config)
        
        self.source_field = config.get('source_field', 'Time of Call')
        self.derived_fields = config.get('derived_fields', {
            'cYear': 'year',
            'cMonth': 'month_name',
            'Hour_Calc': 'hour',
            'DayofWeek': 'day_name'
        })
    
    @property
    def field_name(self) -> str:
        return 'Derived Fields'
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse a datetime value."""
        if pd.isna(value):
            return None
        
        if isinstance(value, datetime):
            return value
        
        try:
            return datetime.fromisoformat(str(value).replace(' ', 'T'))
        except ValueError:
            pass
        
        try:
            return datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
        
        return None
    
    def _get_expected_value(self, dt: datetime, derived_type: str) -> Any:
        """Get the expected value for a derived field."""
        if derived_type == 'year':
            return dt.year
        elif derived_type == 'month_name':
            return MONTH_NAMES.get(dt.month)
        elif derived_type == 'hour':
            return dt.hour
        elif derived_type == 'day_name':
            return DAY_NAMES.get(dt.weekday())
        return None
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate derived fields.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (issues_dataframe, summary_dict)
        """
        issues = []
        
        if self.source_field not in df.columns:
            return self.issues_to_dataframe(issues), self._create_summary(df, issues)
        
        case_number_field = self.config.get('case_number_field', 'ReportNumberNew')
        has_case_number = case_number_field in df.columns
        
        # Track statistics per field
        mismatch_counts = {f: 0 for f in self.derived_fields if f in df.columns}
        null_source_count = 0
        
        for idx, row in df.iterrows():
            source_value = row[self.source_field]
            case_number = row[case_number_field] if has_case_number else None
            
            # Parse source datetime
            source_dt = self._parse_datetime(source_value)
            if source_dt is None:
                null_source_count += 1
                continue
            
            # Check each derived field
            for field, derived_type in self.derived_fields.items():
                if field not in df.columns:
                    continue
                
                actual_value = row[field]
                expected_value = self._get_expected_value(source_dt, derived_type)
                
                if pd.isna(actual_value):
                    continue
                
                # Compare values
                matches = False
                if derived_type in ['year', 'hour']:
                    # Numeric comparison
                    try:
                        matches = int(actual_value) == expected_value
                    except (ValueError, TypeError):
                        matches = False
                else:
                    # String comparison (case-insensitive)
                    matches = str(actual_value).strip().upper() == str(expected_value).upper()
                
                if not matches:
                    mismatch_counts[field] += 1
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=actual_value,
                        issue_type='derived_mismatch',
                        message=f"{field}='{actual_value}' doesn't match {self.source_field} (expected '{expected_value}')",
                        severity='warning',
                        case_number=case_number
                    ))
        
        # Create summary
        extra_stats = {
            'source_field': self.source_field,
            'derived_fields_checked': list(self.derived_fields.keys()),
            'mismatch_counts': mismatch_counts,
            'null_source_count': null_source_count
        }
        
        return self.issues_to_dataframe(issues), self._create_summary(df, issues, extra_stats)
