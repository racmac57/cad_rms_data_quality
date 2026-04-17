"""
Disposition normalization map — loader + golden-pair tests.

Validates that ``shared.utils.normalization`` reads
``Standards/CAD_RMS/mappings/disposition_normalization_map.json`` and that
the ``DispositionValidator`` consumes the same JSON-backed mapping.

These tests exercise the JSON only; they do NOT require a real CAD export.
"""

import pytest

from shared.utils.normalization import (
    load_disposition_canonical_targets,
    load_disposition_map,
)

# Stable raw->canonical pairs verified against the Standards JSON on
# 2026-04-16 (entry_count: 55). If a pair stops matching, intentionally
# update Standards or this list - do not silently relax the assertion.
GOLDEN_PAIRS = [
    ("GOA", "G.O.A."),
    ("UTL", "Unable to Locate"),
    ("SEE REPORT", "See Report"),
    ("CANCELLED", "Canceled"),
    ("TOT", "TOT - See Notes"),
    ("UNFOUNDED/GOA", "Unfounded"),
    ("CLEARED", "Complete"),
    ("FIELD CONTACT", "Field Contact"),
]


@pytest.fixture(autouse=True)
def _clear_loader_cache():
    load_disposition_map.cache_clear()
    load_disposition_canonical_targets.cache_clear()
    yield
    load_disposition_map.cache_clear()
    load_disposition_canonical_targets.cache_clear()


def test_disposition_map_loads_with_uppercase_keys():
    mapping = load_disposition_map()
    assert isinstance(mapping, dict)
    assert len(mapping) >= 50, f"expected >=50 entries, got {len(mapping)}"
    for key in mapping:
        assert key == key.upper(), f"non-upper key in mapping: {key!r}"


@pytest.mark.parametrize("raw,canonical", GOLDEN_PAIRS)
def test_disposition_golden_pairs(raw, canonical):
    mapping = load_disposition_map()
    assert mapping.get(raw) == canonical, (
        f"{raw!r} should map to {canonical!r}, got {mapping.get(raw)!r}"
    )


def test_canonical_targets_includes_core_set():
    targets = set(load_disposition_canonical_targets())
    for required in ("Complete", "Arrest", "Unfounded", "G.O.A.", "See Report"):
        assert required in targets, f"missing canonical target: {required}"


def test_validator_get_disposition_mapping_uses_json():
    """The validator's get_disposition_mapping() must return the JSON map."""
    from validation.validators.disposition_validator import get_disposition_mapping

    assert get_disposition_mapping() == load_disposition_map()


def test_validator_valid_dispositions_includes_canonical_targets():
    from validation.validators.disposition_validator import VALID_DISPOSITIONS

    canonical = set(load_disposition_canonical_targets())
    valid = set(VALID_DISPOSITIONS)
    missing = canonical - valid
    assert not missing, f"VALID_DISPOSITIONS missing canonical targets: {missing}"
