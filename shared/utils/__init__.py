"""
Shared Utilities
================

- call_type_normalizer: Normalize and validate call type names
- report_builder: SCRPA/HPD styled HTML validation summary (validate_cad, validate_rms)
"""

from .call_type_normalizer import normalize_call_type, validate_call_types, validate_call_type_format
from .report_builder import build_scrpa_report
from .schemas_loader import load_schemas
from .version_check import check_standards_version
