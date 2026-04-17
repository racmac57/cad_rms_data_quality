"""
Disposition Validator

Validates that the 'Disposition' field contains only valid domain values.
This field indicates call outcome and is critical for reporting.

Domain and raw->canonical mapping load from Standards JSON via
``shared.utils.normalization`` (declared in ``config/schemas.yaml``).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from shared.utils.normalization import (
    load_disposition_canonical_targets,
    load_disposition_map,
)

from .base_validator import DomainValidator

# Legacy targets retained alongside the Standards canonical_targets so that
# historical exports containing these values are not flagged as invalid.
# Remove an entry only after confirming no in-flight reports rely on it.
_LEGACY_VALID_DISPOSITIONS = (
    "Cleared",
    "Report",
    "No Action Needed",
    "Referred",
    "Citation Issued",
)


def _build_valid_dispositions() -> list[str]:
    canonical = load_disposition_canonical_targets()
    seen: set[str] = set()
    out: list[str] = []
    for value in (*canonical, *_LEGACY_VALID_DISPOSITIONS):
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


VALID_DISPOSITIONS: list[str] = _build_valid_dispositions()


class DispositionValidator(DomainValidator):
    """
    Validator for the 'Disposition' field.

    Checks that all disposition values are in the valid domain.
    Disposition indicates how the call was resolved.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize Disposition validator.

        Args:
            config: Optional configuration. Can override:
                - valid_values: List of valid values
                - field_name: Column name to validate
                - weight: Weight for quality scoring
        """
        config = config or {}

        valid_values = config.get("valid_values", VALID_DISPOSITIONS)
        config.setdefault("weight", 0.15)  # 15% of quality score
        config.setdefault("allow_null", False)

        super().__init__(valid_values=valid_values, case_sensitive=False, config=config)

        self._field_name: str = config.get("field_name", "Disposition")

    @property
    def field_name(self) -> str:
        return self._field_name

    def validate(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
        """
        Validate Disposition values.

        Args:
            df: DataFrame to validate

        Returns:
            Tuple of (issues_dataframe, summary_dict)
        """
        issues_df, summary = super().validate(df)

        # Add field-specific analysis
        if self.field_name in df.columns:
            # Analyze disposition distribution for anomalies
            value_counts = df[self.field_name].value_counts()
            total = len(df)

            # Flag if any single disposition is > 70% (unusual)
            for disp, count in value_counts.items():
                pct = count / total * 100
                if pct > 70:
                    summary["warning"] = f"'{disp}' accounts for {pct:.1f}% of all dispositions"

            # Check for values that might be pre-normalization
            raw_values = df[self.field_name].dropna().unique()
            potentially_fixable = []
            valid_upper = {v.upper() for v in VALID_DISPOSITIONS}

            for val in raw_values:
                val_upper = str(val).upper()
                if val_upper not in valid_upper:
                    if "COMPLETE" in val_upper:
                        potentially_fixable.append((val, "May be Complete variant"))
                    elif "ARREST" in val_upper:
                        potentially_fixable.append((val, "May be Arrest variant"))
                    elif "REPORT" in val_upper:
                        potentially_fixable.append((val, "May be Report variant"))

            summary["potentially_fixable"] = potentially_fixable[:10]
            summary["reference"] = (
                "Standards/CAD_RMS/mappings/disposition_normalization_map.json"
            )

        return issues_df, summary


def get_disposition_mapping() -> dict[str, str]:
    """
    Return the raw->canonical Disposition mapping from Standards JSON.

    Source: ``09_Reference/Standards/CAD_RMS/mappings/disposition_normalization_map.json``
    Keys are UPPERCASE; apply ``.upper()`` to raw input before lookup.
    """
    return load_disposition_map()
