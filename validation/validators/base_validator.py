"""
Base Validator Class

Provides common functionality for all field validators.
All validators inherit from this base class.
"""

import pandas as pd
from typing import Tuple, List, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseValidator(ABC):
    """
    Abstract base class for all field validators.
    
    Subclasses must implement:
        - validate(df) -> Tuple[pd.DataFrame, Dict]
        - field_name property
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validator with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.weight = self.config.get('weight', 1.0)
        self._issues: List[Dict] = []
        
    @property
    @abstractmethod
    def field_name(self) -> str:
        """Return the name of the field being validated."""
        pass
    
    @property
    def validator_name(self) -> str:
        """Return the name of this validator."""
        return self.__class__.__name__
    
    @abstractmethod
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate the dataframe and return issues.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (issues_dataframe, summary_dict)
        """
        pass
    
    def _create_issue(self, 
                      row_index: int,
                      field: str,
                      value: Any,
                      issue_type: str,
                      message: str,
                      severity: str = 'error',
                      case_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a standardized issue dictionary.
        
        Args:
            row_index: Row index in the dataframe
            field: Field name with issue
            value: The problematic value
            issue_type: Category of issue (e.g., 'invalid_domain', 'format_error')
            message: Human-readable description
            severity: 'error', 'warning', or 'info'
            case_number: Optional case number for reference
            
        Returns:
            Issue dictionary
        """
        return {
            'row_index': row_index,
            'field': field,
            'value': str(value)[:100] if value is not None else None,  # Truncate long values
            'issue_type': issue_type,
            'message': message,
            'severity': severity,
            'case_number': case_number,
            'validator': self.validator_name,
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_summary(self, 
                        df: pd.DataFrame, 
                        issues: List[Dict],
                        extra_stats: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a standardized summary dictionary.
        
        Args:
            df: Original dataframe
            issues: List of issues found
            extra_stats: Additional statistics to include
            
        Returns:
            Summary dictionary
        """
        total = len(df)
        error_count = sum(1 for i in issues if i.get('severity') == 'error')
        warning_count = sum(1 for i in issues if i.get('severity') == 'warning')
        
        valid_count = total - error_count
        pass_rate = (valid_count / total * 100) if total > 0 else 100.0
        
        summary = {
            'validator': self.validator_name,
            'field': self.field_name,
            'weight': self.weight,
            'total_records': total,
            'valid_records': valid_count,
            'error_count': error_count,
            'warning_count': warning_count,
            'pass_rate': round(pass_rate, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        if extra_stats:
            summary.update(extra_stats)
            
        return summary
    
    def get_unique_invalid_values(self, issues: List[Dict]) -> List[str]:
        """
        Extract unique invalid values from issues list.
        
        Args:
            issues: List of issue dictionaries
            
        Returns:
            List of unique invalid values
        """
        values = set()
        for issue in issues:
            if issue.get('value') is not None:
                values.add(issue['value'])
        return sorted(list(values))
    
    def issues_to_dataframe(self, issues: List[Dict]) -> pd.DataFrame:
        """
        Convert issues list to DataFrame.
        
        Args:
            issues: List of issue dictionaries
            
        Returns:
            DataFrame of issues
        """
        if not issues:
            return pd.DataFrame(columns=[
                'row_index', 'field', 'value', 'issue_type', 
                'message', 'severity', 'case_number', 'validator', 'timestamp'
            ])
        return pd.DataFrame(issues)


class DomainValidator(BaseValidator):
    """
    Base class for domain value validation.
    
    Validates that field values are within a defined set of valid values.
    """
    
    def __init__(self, 
                 valid_values: List[str],
                 case_sensitive: bool = False,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize domain validator.
        
        Args:
            valid_values: List of valid values for the field
            case_sensitive: Whether comparison should be case-sensitive
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.case_sensitive = case_sensitive
        
        if case_sensitive:
            self.valid_values = set(valid_values)
        else:
            self.valid_values = set(v.upper() for v in valid_values)
    
    def is_valid(self, value: Any) -> bool:
        """
        Check if a value is in the valid set.
        
        Args:
            value: Value to check
            
        Returns:
            True if valid, False otherwise
        """
        if pd.isna(value):
            return self.config.get('allow_null', False)
            
        if self.case_sensitive:
            return str(value) in self.valid_values
        else:
            return str(value).upper() in self.valid_values
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate domain values in dataframe.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (issues_dataframe, summary_dict)
        """
        issues = []
        field = self.field_name
        
        if field not in df.columns:
            logger.warning(f"Field '{field}' not found in dataframe")
            return self.issues_to_dataframe(issues), self._create_summary(df, issues)
        
        # Get case number field if available
        case_number_field = self.config.get('case_number_field', 'ReportNumberNew')
        has_case_number = case_number_field in df.columns
        
        # Validate each row
        for idx, row in df.iterrows():
            value = row[field]
            
            if not self.is_valid(value):
                case_number = row[case_number_field] if has_case_number else None
                
                if pd.isna(value):
                    issue_type = 'null_value'
                    message = f"{field} is null/empty"
                else:
                    issue_type = 'invalid_domain'
                    message = f"'{value}' is not a valid {field} value"
                
                issues.append(self._create_issue(
                    row_index=idx,
                    field=field,
                    value=value,
                    issue_type=issue_type,
                    message=message,
                    case_number=case_number
                ))
        
        # Create summary with value distribution
        value_counts = df[field].value_counts().head(20).to_dict()
        invalid_values = self.get_unique_invalid_values(issues)
        
        extra_stats = {
            'valid_values_count': len(self.valid_values),
            'invalid_values_found': invalid_values[:20],  # Limit to 20
            'value_distribution': value_counts
        }
        
        return self.issues_to_dataframe(issues), self._create_summary(df, issues, extra_stats)


class FormatValidator(BaseValidator):
    """
    Base class for format/pattern validation.
    
    Validates that field values match a specific pattern (regex).
    """
    
    def __init__(self,
                 pattern: str,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize format validator.
        
        Args:
            pattern: Regular expression pattern
            config: Optional configuration dictionary
        """
        import re
        super().__init__(config)
        self.pattern = pattern
        self.compiled_pattern = re.compile(pattern)
    
    def is_valid(self, value: Any) -> bool:
        """
        Check if a value matches the pattern.
        
        Args:
            value: Value to check
            
        Returns:
            True if valid, False otherwise
        """
        if pd.isna(value):
            return self.config.get('allow_null', False)
            
        return bool(self.compiled_pattern.match(str(value)))
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate format in dataframe.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (issues_dataframe, summary_dict)
        """
        issues = []
        field = self.field_name
        
        if field not in df.columns:
            logger.warning(f"Field '{field}' not found in dataframe")
            return self.issues_to_dataframe(issues), self._create_summary(df, issues)
        
        case_number_field = self.config.get('case_number_field', 'ReportNumberNew')
        has_case_number = case_number_field in df.columns
        
        for idx, row in df.iterrows():
            value = row[field]
            
            if not self.is_valid(value):
                case_number = row[case_number_field] if has_case_number else None
                
                if pd.isna(value):
                    issue_type = 'null_value'
                    message = f"{field} is null/empty"
                else:
                    issue_type = 'format_error'
                    message = f"'{value}' does not match expected format"
                
                issues.append(self._create_issue(
                    row_index=idx,
                    field=field,
                    value=value,
                    issue_type=issue_type,
                    message=message,
                    case_number=case_number
                ))
        
        invalid_values = self.get_unique_invalid_values(issues)
        extra_stats = {
            'pattern': self.pattern,
            'invalid_values_found': invalid_values[:20]
        }
        
        return self.issues_to_dataframe(issues), self._create_summary(df, issues, extra_stats)
