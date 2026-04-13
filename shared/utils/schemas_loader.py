"""
schemas_loader — Resolve ${standards_root} in schemas.yaml and return typed paths.

Usage:
    from shared.utils.schemas_loader import load_schemas
    cfg = load_schemas()
    print(cfg['schemas']['canonical'])   # Path object
    print(cfg['metadata']['standards_version'])  # "v3.0.0"
"""

import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml

_DEFAULT_STANDARDS_ROOT = (
    r'C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Standards'
)

_VAR_RE = re.compile(r'\$\{(\w+)\}')

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / 'config'


def load_schemas(config_path: Path = None) -> Dict[str, Any]:
    """Load schemas.yaml with ${standards_root} expansion.

    Resolution order for standards_root:
      1. STANDARDS_ROOT environment variable (if set)
      2. Literal ``standards_root`` key in the YAML file
      3. Hard-coded default (_DEFAULT_STANDARDS_ROOT)

    All string values containing ``${standards_root}`` are expanded.
    Path-like strings (containing '/' or '\\') are converted to Path objects.
    """
    if config_path is None:
        config_path = _CONFIG_DIR / 'schemas.yaml'

    with open(config_path, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)

    # Determine the root
    standards_root = os.environ.get(
        'STANDARDS_ROOT',
        raw.get('standards_root', _DEFAULT_STANDARDS_ROOT),
    )

    variables = {'standards_root': standards_root}

    def _expand(value: Any) -> Any:
        if isinstance(value, str):
            expanded = _VAR_RE.sub(
                lambda m: variables.get(m.group(1), m.group(0)),
                value,
            )
            # Convert path-like strings to Path objects
            if '/' in expanded or '\\' in expanded:
                return Path(expanded)
            return expanded
        if isinstance(value, dict):
            return {k: _expand(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_expand(item) for item in value]
        return value

    resolved = _expand(raw)
    # Ensure standards_root itself is a Path
    resolved['standards_root'] = Path(standards_root)
    return resolved
