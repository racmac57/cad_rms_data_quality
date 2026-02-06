#!/usr/bin/env python3
"""
RMS Monthly Export Validation Script
=====================================

Validates monthly RMS exports and generates:
- Quality score (0-100)
- Validation summary report (HTML)
- Action items for manual correction (Excel)
- Metrics for trend analysis (JSON)

Reports are written to: monthly_validation/reports/YYYY_MM_rms/
(prefix YYYY_MM = month being reported on, e.g. January 2026 -> 2026_01_rms)

Usage:
    python monthly_validation/scripts/validate_rms.py --input "path/to/monthly_rms.xlsx"
    python monthly_validation/scripts/validate_rms.py --input "path/to/monthly_rms.xlsx" --output "custom/output/dir"

Author: R. A. Carucci
Date: 2026-02-02
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse
import logging
import json
import yaml
import re
import sys
from typing import Dict, List, Tuple, Optional, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.utils.report_builder import build_scrpa_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths
CONFIG_PATH = PROJECT_ROOT / "config" / "consolidation_sources.yaml"
VALIDATION_RULES_PATH = PROJECT_ROOT / "config" / "validation_rules.yaml"
DEFAULT_OUTPUT_BASE = PROJECT_ROOT / "monthly_validation" / "reports"


# ============================================================================
# CONFIGURATION LOADING
# ============================================================================

def load_config(config_path: Path = CONFIG_PATH) -> Dict:
    """Load configuration from YAML file."""
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"[OK] Loaded config: {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def load_validation_rules(rules_path: Path = VALIDATION_RULES_PATH) -> Dict:
    """Load validation rules from YAML file."""
    if not rules_path.exists():
        logger.warning(f"Validation rules not found: {rules_path}. Using defaults.")
        return get_default_validation_rules()

    try:
        with open(rules_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        logger.info(f"[OK] Loaded validation rules: {rules_path}")
        return rules
    except Exception as e:
        logger.error(f"Failed to load validation rules: {e}")
        return get_default_validation_rules()


def get_default_validation_rules() -> Dict:
    """Return default validation rules if config not available."""
    return {
        'case_number': {
            'pattern': r'^\d{2}-\d{6}([A-Z])?$',
            'required': True
        },
        'required_fields': {
            # RMS export: Case Number, FullAddress, Zone (not Location, PDZone, or OffenseCode)
        'rms': ['CaseNumber', 'IncidentDate', 'IncidentTime', 'FullAddress', 'Zone']
        },
        'quality_scoring': {
            'weights': {
                'required_fields': 30,
                'valid_formats': 25,
                'address_quality': 20,
                'domain_compliance': 15,
                'consistency_checks': 10
            }
        }
    }


# ============================================================================
# REPORT DIRECTORY MANAGEMENT
# ============================================================================

def parse_report_month_from_path(input_path: Path) -> Optional[str]:
    """
    Extract report month (YYYY_MM) from input file path for folder naming.

    Looks for patterns like 2026_01 or 2026-01 in the filename (month being reported on).
    Returns None if not found (caller may fall back to current date).

    Examples:
        "2026_01_RMS.xlsx" -> "2026_01"
        "RMS_2026_01.xlsx" -> "2026_01"
        "exports/2026-01_rms.xlsx" -> "2026_01"
    """
    name = input_path.name
    # Match YYYY_MM or YYYY-MM (allow _ or - after month, e.g. 2026_01_RMS.xlsx)
    match = re.search(r'(20\d{2})[_\-](0[1-9]|1[0-2])(?=[_\-.\\]|$)', name)
    if match:
        return f"{match.group(1)}_{match.group(2)}"
    return None


def get_report_directory(
    output_base: Path = DEFAULT_OUTPUT_BASE,
    report_month: Optional[str] = None,
    suffix: str = "rms",
) -> Path:
    """
    Generate report directory. Prefix is the month being reported on (YYYY_MM).

    Args:
        output_base: Base path for reports (e.g. monthly_validation/reports).
        report_month: Optional YYYY_MM (e.g. "2026_01") from the data month; if None, uses current date.
        suffix: Folder suffix, e.g. "cad" or "rms".

    Returns:
        Path to report directory (created if not exists), e.g. reports/2026_01_rms.
    """
    if report_month:
        folder_name = f"{report_month}_{suffix}"
    else:
        folder_name = f"{datetime.now().strftime('%Y_%m')}_{suffix}"
    report_dir = output_base / folder_name
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def update_latest_pointer(report_dir: Path, metrics: Dict):
    """Update latest.json to point to current run."""
    latest_file = DEFAULT_OUTPUT_BASE / "latest.json"

    # Load existing data if it exists (might have CAD data too)
    existing = {}
    if latest_file.exists():
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            pass

    # Update with RMS info
    existing["latest_rms_run"] = str(report_dir.name)
    existing["rms_timestamp"] = datetime.now().isoformat()
    existing["rms_path"] = str(report_dir)
    existing["rms_record_count"] = metrics.get("total_records")
    existing["rms_quality_score"] = metrics.get("quality_score")
    existing["rms_action_items_count"] = metrics.get("action_items_count")

    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2)
    logger.info(f"[OK] Updated latest.json -> {report_dir.name}")


# ============================================================================
# DATA LOADING
# ============================================================================

def load_rms_export(file_path: Path) -> pd.DataFrame:
    """
    Load RMS export file (Excel or CSV).

    CaseNumber / "Case Number" is forced to string so Excel does not
    convert values like 26-000001 to number (26000001.0) or date.

    Args:
        file_path: Path to RMS export file

    Returns:
        DataFrame with RMS records
    """
    logger.info(f"Loading RMS export: {file_path.name}")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine file type
    suffix = file_path.suffix.lower()

    if suffix in ['.xlsx', '.xls']:
        # Force case number column(s) to string so "26-000001" is not read as number/date
        dtype_overrides = {}
        head = pd.read_excel(file_path, engine='openpyxl', nrows=0)
        for col in head.columns:
            c = str(col).strip().lower().replace(' ', '')
            if c in ('casenumber', 'case_number'):
                dtype_overrides[col] = str
                break
        df = pd.read_excel(file_path, engine='openpyxl', dtype=dtype_overrides if dtype_overrides else None)
    elif suffix == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

    logger.info(f"  Loaded {len(df):,} records, {len(df.columns)} columns")

    # Standardize column names: RMS export uses "Case Number", FullAddress, Zone (not Location, PDZone, OffenseCode)
    # Map legacy "Location" and "Address" to FullAddress so required_fields check works
    column_mappings = {
        'Case Number': 'CaseNumber',
        'Case_Number': 'CaseNumber',
        'Incident Date': 'IncidentDate',
        'Incident_Date': 'IncidentDate',
        'Incident Time': 'IncidentTime',
        'Incident_Time': 'IncidentTime',
        'Full Address': 'FullAddress',
        'Full_Address': 'FullAddress',
        'Location': 'FullAddress',   # legacy export header; canonical is FullAddress
        'Address': 'FullAddress',
        # Zone stays Zone (RMS uses Zone, not PDZone); PDZone in export maps to Zone for consistency
        'PDZone': 'Zone',
        # OffenseCode not in current RMS export; keep mapping for backwards compatibility if present
        'Offense Code': 'OffenseCode',
        'Offense_Code': 'OffenseCode',
    }

    for old_name, new_name in column_mappings.items():
        if old_name in df.columns and new_name not in df.columns:
            df = df.rename(columns={old_name: new_name})

    # Ensure CaseNumber is string and normalize (Excel numeric/date/quote artifacts)
    if 'CaseNumber' in df.columns:
        df['CaseNumber'] = (
            df['CaseNumber']
            .astype(str)
            .apply(_normalize_case_number_for_display)
        )

    return df


# ============================================================================
# CASE NUMBER NORMALIZATION (Excel dtype / display artifacts)
# ============================================================================

def _normalize_case_number_for_display(value) -> str:
    """
    Coerce CaseNumber to string and fix Excel artifacts.

    Excel may read "26-000001" as number (26000001.0), date, or store as text
    with a leading quote ('26-000001). Strip quotes and normalize to YY-NNNNNN.
    """
    if pd.isna(value):
        return ''
    s = str(value).strip().strip("'\"")  # Excel text-with-quote artifact
    if not s:
        return ''
    # Already in YY-NNNNNN or YY-NNNNNNA form
    if re.match(r'^\d{2}-\d{6}([A-Z])?$', s):
        return s
    # Float artifact: 26000001.0 -> 26-000001
    if '.' in s:
        s = s.split('.')[0]
    # Integer or string without hyphen: 26000001 or 26000001A -> 26-000001 or 26-000001A
    s = s.replace('-', '')
    if len(s) >= 8 and s[:8].isdigit():
        suffix = s[8:] if len(s) > 8 else ''
        return s[:2] + '-' + s[2:8] + suffix
    if len(s) == 7 and s.isdigit():
        return s[:2] + '-' + s[2:]
    return str(value).strip().strip("'\"")


def _normalize_case_number_for_regex(value) -> str:
    """Normalize value for regex match (same logic as display)."""
    return _normalize_case_number_for_display(value)


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_case_numbers(df: pd.DataFrame, pattern: str) -> pd.DataFrame:
    """
    Validate case number format using regex pattern.

    Values are normalized before matching so Excel numeric/date coercion
    (e.g. 26000001.0 or 26-000001 stored as number) is treated as YY-NNNNNN.

    Returns:
        DataFrame with validation results
    """
    if 'CaseNumber' not in df.columns:
        logger.warning("CaseNumber column not found")
        return pd.DataFrame()

    regex = re.compile(pattern)

    results = []
    for idx, row in df.iterrows():
        value = row.get('CaseNumber', '')
        normalized = _normalize_case_number_for_regex(value)
        if pd.isna(value) or normalized == '':
            results.append({
                'row_number': idx + 2,  # Excel row (1-indexed + header)
                'CaseNumber': value,
                'IncidentDate': row.get('IncidentDate', ''),
                'field': 'CaseNumber',
                'current_value': str(value) if not pd.isna(value) else 'NULL',
                'suggested_correction': 'Provide valid case number (YY-NNNNNN)',
                'rule_violated': 'Case number is null or empty',
                'category': 'Data Quality',
                'priority': 1
            })
        elif not regex.match(normalized):
            results.append({
                'row_number': idx + 2,
                'CaseNumber': value,
                'IncidentDate': row.get('IncidentDate', ''),
                'field': 'CaseNumber',
                'current_value': str(value),
                'suggested_correction': 'Format should be YY-NNNNNN or YY-NNNNNNA',
                'rule_violated': 'Invalid case number format',
                'category': 'Data Quality',
                'priority': 1
            })

    return pd.DataFrame(results)


def validate_required_fields(df: pd.DataFrame, required_fields: List[str]) -> pd.DataFrame:
    """
    Validate that required fields are not null/empty.

    Returns:
        DataFrame with validation results
    """
    results = []

    for field in required_fields:
        if field not in df.columns:
            logger.warning(f"Required field not found: {field}")
            continue

        # Find null or empty values
        null_mask = df[field].isna() | (df[field].astype(str).str.strip() == '')
        null_rows = df[null_mask]

        for idx, row in null_rows.iterrows():
            results.append({
                'row_number': idx + 2,
                'CaseNumber': row.get('CaseNumber', ''),
                'IncidentDate': row.get('IncidentDate', ''),
                'field': field,
                'current_value': 'NULL' if pd.isna(row[field]) else str(row[field]),
                'suggested_correction': f'Provide value for {field}',
                'rule_violated': f'Required field {field} is null or empty',
                'category': 'Missing Data',
                'priority': 1
            })

    return pd.DataFrame(results)


def validate_date_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate date field formats and logical consistency.

    Returns:
        DataFrame with validation results
    """
    results = []

    if 'IncidentDate' not in df.columns:
        logger.warning("IncidentDate column not found")
        return pd.DataFrame()

    for idx, row in df.iterrows():
        date_value = row.get('IncidentDate', '')

        if pd.isna(date_value):
            continue  # Handled by required_fields

        # Try to parse date
        try:
            if isinstance(date_value, str):
                parsed_date = pd.to_datetime(date_value)
            else:
                parsed_date = pd.to_datetime(date_value)

            # Check for future dates
            if parsed_date > pd.Timestamp.now():
                results.append({
                    'row_number': idx + 2,
                    'CaseNumber': row.get('CaseNumber', ''),
                    'IncidentDate': date_value,
                    'field': 'IncidentDate',
                    'current_value': str(date_value),
                    'suggested_correction': 'Date should not be in the future',
                    'rule_violated': 'Future date detected',
                    'category': 'Date Validation',
                    'priority': 2
                })

            # Check for very old dates (before 2000)
            if parsed_date.year < 2000:
                results.append({
                    'row_number': idx + 2,
                    'CaseNumber': row.get('CaseNumber', ''),
                    'IncidentDate': date_value,
                    'field': 'IncidentDate',
                    'current_value': str(date_value),
                    'suggested_correction': 'Verify date - appears too old',
                    'rule_violated': 'Suspiciously old date',
                    'category': 'Date Validation',
                    'priority': 3
                })

        except Exception as e:
            results.append({
                'row_number': idx + 2,
                'CaseNumber': row.get('CaseNumber', ''),
                'IncidentDate': date_value,
                'field': 'IncidentDate',
                'current_value': str(date_value),
                'suggested_correction': 'Use valid date format (YYYY-MM-DD)',
                'rule_violated': f'Invalid date format: {str(e)[:50]}',
                'category': 'Date Validation',
                'priority': 2
            })

    return pd.DataFrame(results)


def validate_time_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate time field formats, including known "1" artifact issue.

    Returns:
        DataFrame with validation results
    """
    results = []

    if 'IncidentTime' not in df.columns:
        logger.warning("IncidentTime column not found")
        return pd.DataFrame()

    for idx, row in df.iterrows():
        time_value = row.get('IncidentTime', '')

        if pd.isna(time_value):
            continue  # Handled by required_fields

        str_value = str(time_value).strip()

        # Check for known "1" artifact (common RMS export issue)
        if str_value == '1':
            results.append({
                'row_number': idx + 2,
                'CaseNumber': row.get('CaseNumber', ''),
                'IncidentDate': row.get('IncidentDate', ''),
                'field': 'IncidentTime',
                'current_value': str_value,
                'suggested_correction': 'Replace with actual time or 00:00:00',
                'rule_violated': 'Known "1" artifact in time field',
                'category': 'Time Validation',
                'priority': 2
            })

    return pd.DataFrame(results)


def validate_offense_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate offense code format.

    Returns:
        DataFrame with validation results
    """
    results = []

    if 'OffenseCode' not in df.columns:
        logger.warning("OffenseCode column not found")
        return pd.DataFrame()

    for idx, row in df.iterrows():
        code_value = row.get('OffenseCode', '')

        if pd.isna(code_value) or not str(code_value).strip():
            continue  # Handled by required_fields

        # Check for suspicious patterns (too short, all numbers, etc.)
        str_value = str(code_value).strip()

        # Offense codes should typically have letters and numbers
        # This is a soft check - adjust pattern as needed
        if len(str_value) < 2:
            results.append({
                'row_number': idx + 2,
                'CaseNumber': row.get('CaseNumber', ''),
                'IncidentDate': row.get('IncidentDate', ''),
                'field': 'OffenseCode',
                'current_value': str_value,
                'suggested_correction': 'Verify offense code - appears incomplete',
                'rule_violated': 'Offense code too short',
                'category': 'Offense Code',
                'priority': 3
            })

    return pd.DataFrame(results)


# ============================================================================
# QUALITY SCORING
# ============================================================================

def calculate_quality_score(df: pd.DataFrame, action_items: pd.DataFrame,
                           weights: Dict) -> Tuple[float, Dict]:
    """
    Calculate overall quality score (0-100) based on validation results.

    Args:
        df: Original DataFrame
        action_items: DataFrame of validation issues
        weights: Dictionary with scoring weights

    Returns:
        Tuple of (quality_score, breakdown_dict)
    """
    total_records = len(df)
    if total_records == 0:
        return 0.0, {}

    # Count issues by category
    priority_1_count = len(action_items[action_items['priority'] == 1]) if not action_items.empty else 0
    priority_2_count = len(action_items[action_items['priority'] == 2]) if not action_items.empty else 0
    priority_3_count = len(action_items[action_items['priority'] == 3]) if not action_items.empty else 0

    # Calculate component scores
    # Required fields score (30 points)
    missing_required = len(action_items[action_items['category'] == 'Missing Data']) if not action_items.empty else 0
    required_score = max(0, weights.get('required_fields', 30) * (1 - missing_required / total_records))

    # Valid formats score (25 points)
    format_issues = len(action_items[action_items['category'] == 'Data Quality']) if not action_items.empty else 0
    format_score = max(0, weights.get('valid_formats', 25) * (1 - format_issues / total_records))

    # Domain compliance score (15 points) - includes date/time/offense validation
    date_issues = len(action_items[action_items['category'].isin(['Date Validation', 'Time Validation', 'Offense Code'])]) if not action_items.empty else 0
    domain_score = max(0, weights.get('domain_compliance', 15) * (1 - date_issues / total_records))

    # Consistency score (10 points)
    consistency_score = weights.get('consistency_checks', 10) * 0.95  # Baseline

    # Address quality (20 points) - placeholder for full implementation
    address_score = weights.get('address_quality', 20) * 0.9  # Assume 90% quality baseline

    # Total score
    total_score = required_score + format_score + domain_score + consistency_score + address_score

    breakdown = {
        'required_fields': round(required_score, 2),
        'valid_formats': round(format_score, 2),
        'domain_compliance': round(domain_score, 2),
        'consistency_checks': round(consistency_score, 2),
        'address_quality': round(address_score, 2),
        'priority_1_issues': priority_1_count,
        'priority_2_issues': priority_2_count,
        'priority_3_issues': priority_3_count
    }

    return round(total_score, 2), breakdown


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_action_items_excel(action_items: pd.DataFrame, output_path: Path):
    """
    Generate Excel file with action items organized by priority.

    Args:
        action_items: DataFrame with all validation issues
        output_path: Path to output Excel file
    """
    if action_items.empty:
        logger.info("No action items to export - all records passed validation")
        # Create empty file with headers only
        pd.DataFrame(columns=['row_number', 'CaseNumber', 'IncidentDate', 'field',
                              'current_value', 'suggested_correction', 'rule_violated',
                              'category', 'priority']).to_excel(output_path, index=False)
        return

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: Critical Issues (Priority 1)
        critical = action_items[action_items['priority'] == 1]
        if not critical.empty:
            critical.to_excel(writer, sheet_name='Critical Issues (P1)', index=False)

        # Sheet 2: Warnings (Priority 2)
        warnings = action_items[action_items['priority'] == 2]
        if not warnings.empty:
            warnings.to_excel(writer, sheet_name='Warnings (P2)', index=False)

        # Sheet 3: Info (Priority 3)
        info = action_items[action_items['priority'] == 3]
        if not info.empty:
            info.to_excel(writer, sheet_name='Info (P3)', index=False)

        # Sheet 4: All Issues
        action_items.to_excel(writer, sheet_name='All Issues', index=False)

    logger.info(f"[OK] Action items exported: {output_path}")


def generate_validation_summary_html(df: pd.DataFrame, action_items: pd.DataFrame,
                                     quality_score: float, breakdown: Dict,
                                     input_file: Path, output_path: Path):
    """
    Generate SCRPA/HPD styled HTML validation summary report (shared report_builder).

    Args:
        df: Original DataFrame
        action_items: DataFrame with validation issues
        quality_score: Overall quality score
        breakdown: Score breakdown by category
        input_file: Path to input file
        output_path: Path to output HTML file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if quality_score >= 95:
        quality_label = "Excellent"
    elif quality_score >= 80:
        quality_label = "Good"
    elif quality_score >= 60:
        quality_label = "Needs Attention"
    else:
        quality_label = "Critical"

    output_folder_name = output_path.parent.name if output_path.parent else ""

    html_content = build_scrpa_report(
        report_title="RMS Data Quality Validation",
        input_file_name=input_file.name,
        timestamp=timestamp,
        total_records=len(df),
        quality_score=quality_score,
        quality_label=quality_label,
        breakdown=breakdown,
        action_items=action_items,
        script_name="monthly_validation/scripts/validate_rms.py",
        accent_color="#0d233c",
        output_folder_name=output_folder_name,
        data_source="rms",
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"[OK] Validation summary exported: {output_path}")


def generate_metrics_json(df: pd.DataFrame, action_items: pd.DataFrame,
                          quality_score: float, breakdown: Dict,
                          input_file: Path, output_path: Path):
    """
    Generate JSON metrics file for trend analysis.

    Args:
        df: Original DataFrame
        action_items: DataFrame with validation issues
        quality_score: Overall quality score
        breakdown: Score breakdown by category
        input_file: Path to input file
        output_path: Path to output JSON file
    """
    metrics = {
        "validation_timestamp": datetime.now().isoformat(),
        "data_source": "rms",
        "input_file": str(input_file.name),
        "total_records": len(df),
        "quality_score": quality_score,
        "score_breakdown": breakdown,
        "action_items_count": len(action_items),
        "issues_by_category": {},
        "issues_by_priority": {
            "priority_1": len(action_items[action_items['priority'] == 1]) if not action_items.empty else 0,
            "priority_2": len(action_items[action_items['priority'] == 2]) if not action_items.empty else 0,
            "priority_3": len(action_items[action_items['priority'] == 3]) if not action_items.empty else 0
        },
        "pass_rate": round((len(df) - len(action_items)) / len(df) * 100, 2) if len(df) > 0 else 0
    }

    # Add category breakdown
    if not action_items.empty:
        metrics["issues_by_category"] = action_items['category'].value_counts().to_dict()

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"[OK] Metrics exported: {output_path}")


# ============================================================================
# MAIN VALIDATION WORKFLOW
# ============================================================================

def run_validation(input_file: Path, output_dir: Optional[Path] = None) -> Dict:
    """
    Run complete RMS validation workflow.

    Args:
        input_file: Path to RMS export file
        output_dir: Optional output directory (auto-generated if not provided)

    Returns:
        Dictionary with validation results
    """
    logger.info("=" * 60)
    logger.info("RMS MONTHLY VALIDATION")
    logger.info("=" * 60)

    start_time = datetime.now()

    # Load configuration
    config = load_config()
    rules = load_validation_rules()

    # Setup output directory (prefix YYYY_MM = month being reported on)
    if output_dir is None:
        report_month = parse_report_month_from_path(input_file)
        output_dir = get_report_directory(report_month=report_month, suffix="rms")
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Output directory: {output_dir}")

    # Setup log file for this run
    log_handler = logging.FileHandler(output_dir / "validation.log")
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)

    # Load data
    df = load_rms_export(input_file)

    # Run validations
    logger.info("\n[STEP 1] Validating case numbers...")
    case_number_pattern = rules.get('case_number', {}).get('pattern', r'^\d{2}-\d{6}([A-Z])?$')
    # Ensure pattern matches valid format (YAML may escape backslashes differently)
    if not re.match(case_number_pattern, '26-000001'):
        case_number_pattern = r'^\d{2}-\d{6}([A-Z])?$'
    case_issues = validate_case_numbers(df, case_number_pattern)
    logger.info(f"  Found {len(case_issues)} case number issues")

    logger.info("\n[STEP 2] Validating required fields...")
    required_fields = rules.get('required_fields', {}).get('rms', [])
    required_issues = validate_required_fields(df, required_fields)
    logger.info(f"  Found {len(required_issues)} missing field issues")

    logger.info("\n[STEP 3] Validating date fields...")
    date_issues = validate_date_fields(df)
    logger.info(f"  Found {len(date_issues)} date issues")

    logger.info("\n[STEP 4] Validating time fields...")
    time_issues = validate_time_fields(df)
    logger.info(f"  Found {len(time_issues)} time issues")

    logger.info("\n[STEP 5] Validating offense codes...")
    offense_issues = validate_offense_codes(df)
    logger.info(f"  Found {len(offense_issues)} offense code issues")

    # Combine all action items
    all_issues = [case_issues, required_issues, date_issues, time_issues, offense_issues]
    non_empty = [df for df in all_issues if not df.empty]

    if non_empty:
        action_items = pd.concat(non_empty, ignore_index=True)
    else:
        action_items = pd.DataFrame()

    logger.info(f"\n[STEP 6] Calculating quality score...")
    weights = rules.get('quality_scoring', {}).get('weights', {})
    quality_score, breakdown = calculate_quality_score(df, action_items, weights)
    logger.info(f"  Quality Score: {quality_score}/100")

    # Generate reports
    logger.info("\n[STEP 7] Generating reports...")

    action_items_path = output_dir / "action_items.xlsx"
    generate_action_items_excel(action_items, action_items_path)

    summary_path = output_dir / "validation_summary.html"
    generate_validation_summary_html(df, action_items, quality_score, breakdown, input_file, summary_path)

    metrics_path = output_dir / "metrics.json"
    generate_metrics_json(df, action_items, quality_score, breakdown, input_file, metrics_path)

    # Update latest pointer
    metrics = {
        "total_records": len(df),
        "quality_score": quality_score,
        "action_items_count": len(action_items)
    }
    update_latest_pointer(output_dir, metrics)

    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Total records:    {len(df):,}")
    logger.info(f"  Quality score:    {quality_score}/100")
    logger.info(f"  Action items:     {len(action_items):,}")
    logger.info(f"  Processing time:  {elapsed:.2f}s")
    logger.info(f"  Reports:          {output_dir}")

    # Remove temporary log handler
    logger.removeHandler(log_handler)
    log_handler.close()

    return {
        "success": True,
        "total_records": len(df),
        "quality_score": quality_score,
        "breakdown": breakdown,
        "action_items_count": len(action_items),
        "output_dir": str(output_dir),
        "elapsed_seconds": elapsed
    }


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate monthly RMS exports and generate quality reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Validate with auto-generated output directory
    python validate_rms.py --input "C:/path/to/2026_02_RMS.xlsx"

    # Validate with custom output directory
    python validate_rms.py --input "C:/path/to/2026_02_RMS.xlsx" --output "custom/output"

    # Verbose mode
    python validate_rms.py --input "C:/path/to/2026_02_RMS.xlsx" --verbose
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to RMS export file (Excel or CSV)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output directory for reports (default: YYYY_MM_rms from input file month)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    input_file = Path(args.input)
    output_dir = Path(args.output) if args.output else None

    try:
        result = run_validation(input_file, output_dir)

        if result['quality_score'] >= 80:
            sys.exit(0)
        else:
            logger.warning(f"Quality score below threshold: {result['quality_score']}/100")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
