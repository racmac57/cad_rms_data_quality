"""
version_check — Warn if schemas.yaml standards_version diverges from Standards/VERSION.

Usage:
    from shared.utils.version_check import check_standards_version
    check_standards_version()          # logs WARNING if mismatch
    check_standards_version(strict=True)  # raises on mismatch
"""

import logging
from pathlib import Path

from .schemas_loader import load_schemas

logger = logging.getLogger(__name__)


def check_standards_version(*, strict: bool = False) -> bool:
    """Compare schemas.yaml standards_version against Standards/VERSION.

    Returns True if versions match (or VERSION file is missing).
    Logs a WARNING on mismatch.  Raises RuntimeError if *strict* and mismatch.
    """
    cfg = load_schemas()
    yaml_version = cfg.get('metadata', {}).get('standards_version', '').lstrip('v')
    standards_root: Path = cfg['standards_root']
    version_file = standards_root / 'VERSION'

    if not version_file.exists():
        logger.info(
            'Standards/VERSION not found at %s — skipping version check',
            version_file,
        )
        return True

    file_version = version_file.read_text(encoding='utf-8').strip().lstrip('v')

    if yaml_version == file_version:
        logger.info(
            'Standards version OK: schemas.yaml=%s, VERSION=%s',
            yaml_version, file_version,
        )
        return True

    msg = (
        f'Standards version MISMATCH: schemas.yaml says v{yaml_version}, '
        f'but Standards/VERSION says v{file_version}. '
        f'Update schemas.yaml metadata.standards_version after Standards upgrades.'
    )
    if strict:
        raise RuntimeError(msg)
    logger.warning(msg)
    return False
