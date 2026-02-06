"""
Officer Validator

Validates that the 'Officer' field contains valid personnel
from the reference file.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple, Set
from pathlib import Path
from .base_validator import BaseValidator


class OfficerValidator(BaseValidator):
    """
    Validator for the 'Officer' field.
    
    Validates:
    1. Officer/unit exists in personnel master file
    2. Flags inactive officers still appearing
    3. Detects potential new personnel (drift)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Officer validator.
        
        Args:
            config: Optional configuration. Can override:
                - reference_file: Path to Assignment_Master_V2.csv
                - field_name: Column name to validate
                - weight: Weight for quality scoring
                - allow_unknown: Whether to allow values not in reference
        """
        config = config or {}
        config.setdefault('weight', 0.10)  # 10% of quality score
        config.setdefault('allow_null', True)  # Officer can be null
        config.setdefault('allow_unknown', True)  # Allow unknown (flag as drift)
        
        super().__init__(config)
        
        self._field_name = config.get('field_name', 'Officer')
        self.reference_file = config.get('reference_file')
        
        # Load reference data
        self.valid_officers: Set[str] = set()
        self.active_officers: Set[str] = set()
        self.inactive_officers: Set[str] = set()
        self._load_reference()
    
    @property
    def field_name(self) -> str:
        return self._field_name
    
    def _load_reference(self) -> None:
        """Load valid officers from reference file."""
        if self.reference_file and Path(self.reference_file).exists():
            try:
                ref_df = pd.read_csv(self.reference_file)
                
                # Get all personnel
                name_fields = ['FULL_NAME', 'BADGE_NUMBER', 'PADDED_BADGE_NUMBER']
                for field in name_fields:
                    if field in ref_df.columns:
                        values = ref_df[field].dropna().str.upper().str.strip()
                        self.valid_officers.update(values)
                
                # Separate active vs inactive
                if 'STATUS' in ref_df.columns:
                    active_df = ref_df[ref_df['STATUS'].str.upper() == 'ACTIVE']
                    inactive_df = ref_df[ref_df['STATUS'].str.upper() == 'INACTIVE']
                    
                    for field in name_fields:
                        if field in active_df.columns:
                            self.active_officers.update(
                                active_df[field].dropna().str.upper().str.strip()
                            )
                        if field in inactive_df.columns:
                            self.inactive_officers.update(
                                inactive_df[field].dropna().str.upper().str.strip()
                            )
                            
            except Exception as e:
                print(f"Warning: Could not load reference file: {e}")
    
    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate Officer values.
        
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
        unknown_officers = set()
        inactive_officers_found = set()
        
        for idx, row in df.iterrows():
            value = row[field]
            case_number = row[case_number_field] if has_case_number else None
            
            # Check for null
            if pd.isna(value):
                null_count += 1
                if not self.config.get('allow_null', True):
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=value,
                        issue_type='null_value',
                        message='Officer is null/empty',
                        case_number=case_number
                    ))
                continue
            
            value_upper = str(value).strip().upper()
            
            # Check if officer exists in reference
            if self.valid_officers:
                if value_upper not in self.valid_officers:
                    unknown_officers.add(str(value).strip())
                    
                    if not self.config.get('allow_unknown', True):
                        issues.append(self._create_issue(
                            row_index=idx,
                            field=field,
                            value=value,
                            issue_type='unknown_officer',
                            message=f"Officer not in reference: '{value}'",
                            severity='warning',
                            case_number=case_number
                        ))
                
                # Check if inactive officer
                elif value_upper in self.inactive_officers:
                    inactive_officers_found.add(str(value).strip())
                    issues.append(self._create_issue(
                        row_index=idx,
                        field=field,
                        value=value,
                        issue_type='inactive_officer',
                        message=f"Inactive officer appearing in data: '{value}'",
                        severity='info',
                        case_number=case_number
                    ))
        
        # Create summary
        extra_stats = {
            'reference_file': str(self.reference_file) if self.reference_file else 'None',
            'reference_count': len(self.valid_officers),
            'active_count': len(self.active_officers),
            'inactive_count': len(self.inactive_officers),
            'null_count': null_count,
            'unknown_officers': list(unknown_officers)[:20],
            'inactive_officers_found': list(inactive_officers_found)[:10],
            'unique_values': df[field].nunique() if field in df.columns else 0
        }
        
        return self.issues_to_dataframe(issues), self._create_summary(df, issues, extra_stats)
