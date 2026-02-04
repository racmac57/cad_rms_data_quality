"""
Data Drift Detectors

This package contains drift detectors for monitoring changes
in reference data over time.

Drift detectors identify:
- New values appearing in data not in reference files
- Values in reference files no longer appearing in data
- Distribution shifts in domain values
"""

from .call_type_drift import CallTypeDriftDetector
from .personnel_drift import PersonnelDriftDetector

__all__ = [
    'CallTypeDriftDetector',
    'PersonnelDriftDetector',
]

__version__ = '1.0.0'
