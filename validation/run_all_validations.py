#!/usr/bin/env python
"""
Master Validation Orchestrator

Runs all validators and drift detectors on CAD/RMS data,
generates comprehensive reports, and calculates quality scores.

Usage:
    python run_all_validations.py --input data.xlsx --output reports/
    python run_all_validations.py --input data.xlsx --validators HowReported,Disposition
    python run_all_validations.py --input data.xlsx --skip-drift
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation.validators import (
    HowReportedValidator,
    DispositionValidator,
    CaseNumberValidator,
    IncidentValidator,
    DateTimeValidator,
    DurationValidator,
    OfficerValidator,
    GeographyValidator,
    DerivedFieldValidator,
)
from validation.sync import (
    CallTypeDriftDetector,
    PersonnelDriftDetector,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Default paths (relative to cad_rms_data_quality root)
DEFAULT_CALLTYPES_REF = r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\CallTypes_Master.csv"
DEFAULT_PERSONNEL_REF = r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Personnel\Assignment_Master_V2.csv"


class ValidationOrchestrator:
    """
    Master orchestrator for running all validators and drift detectors.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize orchestrator with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Reference file paths
        self.calltypes_ref = self.config.get('calltypes_reference', DEFAULT_CALLTYPES_REF)
        self.personnel_ref = self.config.get('personnel_reference', DEFAULT_PERSONNEL_REF)
        
        # Initialize validators
        self.validators = self._init_validators()
        self.drift_detectors = self._init_drift_detectors()
        
        # Results storage
        self.validation_results: List[Dict] = []
        self.drift_results: List[Dict] = []
        self.all_issues: pd.DataFrame = pd.DataFrame()
    
    def _init_validators(self) -> Dict[str, Any]:
        """Initialize all validators with configuration."""
        return {
            'HowReported': HowReportedValidator(),
            'Disposition': DispositionValidator(),
            'CaseNumber': CaseNumberValidator(),
            'Incident': IncidentValidator({
                'reference_file': self.calltypes_ref,
                'allow_unknown': True  # Flag as drift, not error
            }),
            'DateTime': DateTimeValidator(),
            'Duration': DurationValidator(),
            'Officer': OfficerValidator({
                'reference_file': self.personnel_ref
            }),
            'Geography': GeographyValidator(),
            'DerivedFields': DerivedFieldValidator(),
        }
    
    def _init_drift_detectors(self) -> Dict[str, Any]:
        """Initialize drift detectors with configuration."""
        return {
            'CallType': CallTypeDriftDetector({
                'reference_file': self.calltypes_ref
            }),
            'Personnel': PersonnelDriftDetector({
                'reference_file': self.personnel_ref
            }),
        }
    
    def load_data(self, input_path: str, sample_size: Optional[int] = None) -> pd.DataFrame:
        """
        Load data from file.
        
        Args:
            input_path: Path to input file (Excel or CSV)
            sample_size: Optional number of rows to sample
            
        Returns:
            Loaded DataFrame
        """
        logger.info(f"Loading data from: {input_path}")
        
        path = Path(input_path)
        if path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(input_path, engine='openpyxl', dtype={'ReportNumberNew': str})
        elif path.suffix.lower() == '.csv':
            df = pd.read_csv(input_path, low_memory=False, dtype={'ReportNumberNew': str})
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        if sample_size and len(df) > sample_size:
            logger.info(f"Sampling {sample_size} rows from {len(df)} total")
            df = df.sample(n=sample_size, random_state=42)
        
        logger.info(f"Loaded {len(df):,} records with {len(df.columns)} columns")
        return df
    
    def run_validators(self, 
                       df: pd.DataFrame, 
                       validator_names: Optional[List[str]] = None) -> List[Dict]:
        """
        Run validators on dataframe.
        
        Args:
            df: DataFrame to validate
            validator_names: Optional list of specific validators to run
            
        Returns:
            List of validation results
        """
        results = []
        all_issues = []
        
        validators_to_run = validator_names or list(self.validators.keys())
        
        for name in validators_to_run:
            if name not in self.validators:
                logger.warning(f"Unknown validator: {name}")
                continue
            
            validator = self.validators[name]
            logger.info(f"Running {name} validator...")
            
            try:
                issues_df, summary = validator.validate(df)
                results.append(summary)
                
                if len(issues_df) > 0:
                    all_issues.append(issues_df)
                
                logger.info(
                    f"  {name}: {summary['pass_rate']:.1f}% pass rate "
                    f"({summary['error_count']} errors, {summary['warning_count']} warnings)"
                )
            except Exception as e:
                logger.error(f"  {name} failed: {str(e)}")
                results.append({
                    'validator': name,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Combine all issues
        if all_issues:
            self.all_issues = pd.concat(all_issues, ignore_index=True)
        
        self.validation_results = results
        return results
    
    def run_drift_detection(self,
                           df: pd.DataFrame,
                           detector_names: Optional[List[str]] = None) -> List[Dict]:
        """
        Run drift detectors on dataframe.
        
        Args:
            df: DataFrame to analyze
            detector_names: Optional list of specific detectors to run
            
        Returns:
            List of drift detection results
        """
        results = []
        
        detectors_to_run = detector_names or list(self.drift_detectors.keys())
        
        for name in detectors_to_run:
            if name not in self.drift_detectors:
                logger.warning(f"Unknown drift detector: {name}")
                continue
            
            detector = self.drift_detectors[name]
            logger.info(f"Running {name} drift detector...")
            
            try:
                result = detector.detect(df)
                results.append(result)
                
                stats = result.get('statistics', {})
                drift = result.get('drift_detected', False)
                logger.info(
                    f"  {name}: Drift {'DETECTED' if drift else 'not detected'} "
                    f"({stats.get('unique_call_types', stats.get('unique_officers', 0))} unique values)"
                )
            except Exception as e:
                logger.error(f"  {name} failed: {str(e)}")
                results.append({
                    'detector': name,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        self.drift_results = results
        return results
    
    def calculate_quality_score(self) -> Dict[str, Any]:
        """
        Calculate overall quality score from validation results.
        
        Returns:
            Quality score dictionary
        """
        if not self.validation_results:
            return {'score': None, 'error': 'No validation results'}
        
        total_weight = 0
        weighted_sum = 0
        
        for result in self.validation_results:
            if 'error' in result:
                continue
            
            weight = result.get('weight', 1.0)
            pass_rate = result.get('pass_rate', 0)
            
            weighted_sum += pass_rate * weight
            total_weight += weight
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0
        
        return {
            'overall_score': round(overall_score, 2),
            'total_validators': len(self.validation_results),
            'failed_validators': sum(1 for r in self.validation_results if 'error' in r),
            'grade': self._score_to_grade(overall_score),
            'timestamp': datetime.now().isoformat()
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 99:
            return 'A+'
        elif score >= 95:
            return 'A'
        elif score >= 90:
            return 'A-'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'B-'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def generate_report(self, output_dir: str) -> Dict[str, str]:
        """
        Generate validation report files.
        
        Args:
            output_dir: Directory for output files
            
        Returns:
            Dictionary of output file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_files = {}
        
        # Save validation summary (JSON)
        summary_file = output_path / f'validation_summary_{timestamp}.json'
        summary = {
            'quality_score': self.calculate_quality_score(),
            'validation_results': self.validation_results,
            'drift_results': self.drift_results,
            'generated_at': datetime.now().isoformat()
        }
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        output_files['summary_json'] = str(summary_file)
        
        # Save issues (Excel)
        if len(self.all_issues) > 0:
            issues_file = output_path / f'validation_issues_{timestamp}.xlsx'
            self.all_issues.to_excel(issues_file, index=False)
            output_files['issues_excel'] = str(issues_file)
        
        # Save human-readable report (Markdown)
        report_file = output_path / f'validation_report_{timestamp}.md'
        with open(report_file, 'w') as f:
            f.write(self._generate_markdown_report())
        output_files['report_md'] = str(report_file)
        
        logger.info(f"Reports saved to: {output_dir}")
        return output_files
    
    def _generate_markdown_report(self) -> str:
        """Generate markdown report content."""
        quality = self.calculate_quality_score()
        
        lines = [
            "# CAD Data Quality Validation Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## Quality Score",
            "",
            f"**Overall Score:** {quality['overall_score']}% ({quality['grade']})",
            "",
            "---",
            "",
            "## Validation Results",
            "",
            "| Validator | Pass Rate | Errors | Warnings |",
            "|-----------|-----------|--------|----------|",
        ]
        
        for result in self.validation_results:
            if 'error' in result:
                lines.append(f"| {result.get('validator', 'Unknown')} | ERROR | - | - |")
            else:
                lines.append(
                    f"| {result.get('validator', 'Unknown')} | "
                    f"{result.get('pass_rate', 0):.1f}% | "
                    f"{result.get('error_count', 0)} | "
                    f"{result.get('warning_count', 0)} |"
                )
        
        lines.extend([
            "",
            "---",
            "",
            "## Drift Detection",
            "",
        ])
        
        for result in self.drift_results:
            if 'error' in result:
                lines.append(f"**{result.get('detector', 'Unknown')}:** ERROR")
            else:
                drift = result.get('drift_detected', False)
                status = 'DRIFT DETECTED' if drift else 'No drift'
                stats = result.get('statistics', {})
                lines.append(f"**{result.get('detector', 'Unknown')}:** {status}")
                
                if 'new_call_types_count' in stats:
                    lines.append(f"  - New call types: {stats['new_call_types_count']}")
                    lines.append(f"  - Unused call types: {stats['unused_call_types_count']}")
                elif 'new_personnel_count' in stats:
                    lines.append(f"  - New personnel: {stats['new_personnel_count']}")
                    lines.append(f"  - Inactive appearing: {stats['inactive_appearing_count']}")
                
                lines.append("")
        
        lines.extend([
            "---",
            "",
            "## Issues Summary",
            "",
            f"**Total Issues Found:** {len(self.all_issues)}",
            "",
        ])
        
        if len(self.all_issues) > 0:
            # Issues by type
            lines.append("### By Issue Type")
            issue_counts = self.all_issues['issue_type'].value_counts()
            for issue_type, count in issue_counts.items():
                lines.append(f"- {issue_type}: {count}")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "*Report generated by CAD/RMS Data Quality Validation System*",
        ])
        
        return '\n'.join(lines)
    
    def run(self,
            input_path: str,
            output_dir: str,
            validator_names: Optional[List[str]] = None,
            skip_drift: bool = False,
            sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Run complete validation pipeline.
        
        Args:
            input_path: Path to input data file
            output_dir: Directory for output reports
            validator_names: Optional list of specific validators
            skip_drift: Whether to skip drift detection
            sample_size: Optional sample size for large files
            
        Returns:
            Complete results dictionary
        """
        logger.info("="*60)
        logger.info("CAD/RMS Data Quality Validation")
        logger.info("="*60)
        
        # Load data
        df = self.load_data(input_path, sample_size)
        
        # Run validators
        logger.info("")
        logger.info("Running field validators...")
        self.run_validators(df, validator_names)
        
        # Run drift detection
        if not skip_drift:
            logger.info("")
            logger.info("Running drift detection...")
            self.run_drift_detection(df)
        
        # Calculate quality score
        quality_score = self.calculate_quality_score()
        logger.info("")
        logger.info(f"Overall Quality Score: {quality_score['overall_score']}% ({quality_score['grade']})")
        
        # Generate reports
        logger.info("")
        output_files = self.generate_report(output_dir)
        
        logger.info("")
        logger.info("="*60)
        logger.info("Validation Complete!")
        logger.info("="*60)
        
        return {
            'quality_score': quality_score,
            'validation_results': self.validation_results,
            'drift_results': self.drift_results,
            'issues_count': len(self.all_issues),
            'output_files': output_files
        }


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description='Run CAD/RMS data quality validation'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to input data file (Excel or CSV)'
    )
    parser.add_argument(
        '--output', '-o',
        default='validation/reports',
        help='Output directory for reports (default: validation/reports)'
    )
    parser.add_argument(
        '--validators',
        help='Comma-separated list of validators to run (default: all)'
    )
    parser.add_argument(
        '--skip-drift',
        action='store_true',
        help='Skip drift detection'
    )
    parser.add_argument(
        '--sample',
        type=int,
        help='Sample size for large files'
    )
    parser.add_argument(
        '--calltypes-ref',
        default=DEFAULT_CALLTYPES_REF,
        help='Path to CallTypes reference file'
    )
    parser.add_argument(
        '--personnel-ref',
        default=DEFAULT_PERSONNEL_REF,
        help='Path to Personnel reference file'
    )
    
    args = parser.parse_args()
    
    # Parse validators
    validator_names = None
    if args.validators:
        validator_names = [v.strip() for v in args.validators.split(',')]
    
    # Create orchestrator
    config = {
        'calltypes_reference': args.calltypes_ref,
        'personnel_reference': args.personnel_ref,
    }
    orchestrator = ValidationOrchestrator(config)
    
    # Run validation
    results = orchestrator.run(
        input_path=args.input,
        output_dir=args.output,
        validator_names=validator_names,
        skip_drift=args.skip_drift,
        sample_size=args.sample
    )
    
    # Print summary
    print()
    print(f"Quality Score: {results['quality_score']['overall_score']}% ({results['quality_score']['grade']})")
    print(f"Total Issues: {results['issues_count']}")
    print(f"Reports saved to: {args.output}")
    
    return 0 if results['quality_score']['overall_score'] >= 90 else 1


if __name__ == '__main__':
    sys.exit(main())
