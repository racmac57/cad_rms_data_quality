"""
Call Type Normalization Utility
================================

Normalizes call type names to standard format for validation and processing.

This is the RUNTIME version for use in validators and ETL pipelines.
The reference data maintenance version lives in:
09_Reference/Classifications/CallTypes/clean_calltypes.py

Author: R. A. Carucci
Date: 2026-01-30
"""

from typing import Union
import re
import pandas as pd


# Pattern for statute suffixes: " - 2C:12-1b" or " - 39:4-50.2"
# Includes optional spaces within statute (e.g., " - 2C: 12-1b")
STATUTE_SUFFIX_RE = re.compile(
    r"\s*-\s*((?:2C|39):[0-9A-Za-z.\-\s]+)\s*$"
)


def normalize_call_type(
    value: Union[str, pd.Series],
    remove_statute: bool = False
) -> Union[str, pd.Series]:
    """
    Normalize call type names to standard format.

    Performs the following normalizations:
    - Trims whitespace
    - Collapses internal whitespace to single spaces
    - Replaces em dash (—) and en dash (–) with hyphen (-)
    - Standardizes statute suffix format (e.g., " - 2C:12-1b")
    - Optionally removes statute suffix entirely

    Args:
        value: Single string or pandas Series of call type names
        remove_statute: If True, remove statute suffix entirely
                       If False (default), standardize statute format

    Returns:
        Normalized call type(s) in same type as input

    Examples:
        >>> normalize_call_type("Aggravated Assault - 2C: 12-1b")
        'Aggravated Assault - 2C:12-1b'

        >>> normalize_call_type("Aggravated Assault - 2C:12-1b", remove_statute=True)
        'Aggravated Assault'

        >>> df["Incident_Clean"] = normalize_call_type(df["Incident"])
    """
    if isinstance(value, pd.Series):
        return value.apply(lambda x: _normalize_single_call_type(x, remove_statute))
    else:
        return _normalize_single_call_type(value, remove_statute)


def _normalize_single_call_type(value: str, remove_statute: bool = False) -> str:
    """Normalize a single call type value."""
    if pd.isna(value):
        return ""

    s = str(value)

    # Trim and collapse internal whitespace
    s = s.strip()
    s = re.sub(r"\s+", " ", s)

    # Replace em dash and en dash with plain hyphen
    s = s.replace("\u2014", "-").replace("\u2013", "-")

    # Try to find a statute suffix
    m = STATUTE_SUFFIX_RE.search(s)
    if not m:
        # No statute suffix found
        return s

    # Text before the suffix
    base_text = s[:m.start()].rstrip(" -")

    if remove_statute:
        # Remove statute suffix entirely
        return base_text

    # Statute part with spaces removed
    statute = m.group(1).replace(" ", "")

    # Final normalized form
    return f"{base_text} - {statute}"


def validate_call_type_format(value: str) -> tuple[bool, str]:
    """
    Validate if a call type is in proper format.

    Args:
        value: Call type string to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str or None)

    Examples:
        >>> validate_call_type_format("Motor Vehicle Stop")
        (True, None)

        >>> validate_call_type_format("Aggravated Assault - 2C: 12-1b")
        (False, "Statute suffix has improper spacing")
    """
    if pd.isna(value) or not value.strip():
        return False, "Call type is null or empty"

    s = str(value).strip()

    # Check for excessive whitespace
    if re.search(r"\s{2,}", s):
        return False, "Contains excessive whitespace"

    # Check for em/en dash
    if "\u2014" in s or "\u2013" in s:
        return False, "Contains em dash or en dash (should be hyphen)"

    # Check statute format if present
    m = STATUTE_SUFFIX_RE.search(s)
    if m:
        # Statute found - check if it has proper spacing
        statute = m.group(1)
        if " " in statute:
            return False, "Statute suffix has improper spacing"

    return True, None


# Convenience function for bulk validation
def validate_call_types(series: pd.Series) -> pd.DataFrame:
    """
    Validate a series of call types and return validation report.

    Args:
        series: Pandas Series of call type names

    Returns:
        DataFrame with columns: index, value, is_valid, error_message

    Example:
        >>> report = validate_call_types(df["Incident"])
        >>> invalid = report[~report["is_valid"]]
    """
    results = []

    for idx, value in series.items():
        is_valid, error_msg = validate_call_type_format(value)
        results.append({
            "index": idx,
            "value": value,
            "is_valid": is_valid,
            "error_message": error_msg
        })

    return pd.DataFrame(results)


if __name__ == "__main__":
    # Self-test
    test_cases = [
        ("Aggravated Assault - 2C: 12-1b", "Aggravated Assault - 2C:12-1b"),
        ("Motor Vehicle Stop", "Motor Vehicle Stop"),
        ("DWI - 39: 4-50", "DWI - 39:4-50"),
        ("  Multiple   Spaces  ", "Multiple Spaces"),
        ("Em—Dash Test", "Em-Dash Test"),
    ]

    print("Call Type Normalizer Self-Test")
    print("=" * 60)

    for input_val, expected in test_cases:
        result = normalize_call_type(input_val)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} Input:    '{input_val}'")
        print(f"      Expected: '{expected}'")
        print(f"      Got:      '{result}'")
        print()
