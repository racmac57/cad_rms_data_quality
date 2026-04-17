"""
normalization — Load CAD/RMS domain normalization maps from Standards JSON.

Source of truth: ``09_Reference/Standards/CAD_RMS/mappings/*.json`` (paths
declared under ``mappings:`` in ``config/schemas.yaml``).

JSON shape:
    {
      "_metadata": {"canonical_targets": [...], ...},
      "mapping": {"RAW_UPPER": "Canonical Value", ...}
    }

Mapping keys are UPPERCASE. Callers normalize input with ``.str.upper()``
before lookup.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from .schemas_loader import load_schemas


def _load_mapping_json(schemas_key: str) -> dict:
    cfg = load_schemas()
    try:
        path: Path = cfg["mappings"][schemas_key]
    except KeyError as exc:
        raise KeyError(
            f"schemas.yaml mappings.{schemas_key} not declared. "
            "Add the path under 'mappings:' in config/schemas.yaml."
        ) from exc
    if not path.exists():
        raise FileNotFoundError(
            f"{schemas_key}: expected JSON at {path}. "
            "Verify Standards/CAD_RMS/mappings/ is synced."
        )
    with open(path, encoding="utf-8") as f:
        data: dict = json.load(f)
    return data


@cache
def load_disposition_map() -> dict[str, str]:
    """Return the raw->canonical Disposition mapping (UPPERCASE keys)."""
    return dict(_load_mapping_json("disposition_normalization")["mapping"])


@cache
def load_disposition_canonical_targets() -> tuple[str, ...]:
    """Return the canonical Disposition target values (immutable tuple)."""
    data = _load_mapping_json("disposition_normalization")
    return tuple(data["_metadata"]["canonical_targets"])


@cache
def load_how_reported_map() -> dict[str, str]:
    """Return the raw->canonical How Reported mapping (UPPERCASE keys)."""
    return dict(_load_mapping_json("how_reported_normalization")["mapping"])


@cache
def load_how_reported_canonical_targets() -> tuple[str, ...]:
    """Return the canonical How Reported target values (immutable tuple)."""
    data = _load_mapping_json("how_reported_normalization")
    return tuple(data["_metadata"]["canonical_targets"])
