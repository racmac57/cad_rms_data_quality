#!/usr/bin/env python3
"""
Batch Integrity Verification Script - Pre-Weekend Lockdown

Purpose:
    Verifies SHA256 hash integrity and record count reconciliation for all
    batch files before weekend. Ensures data is safe and ready for Monday's
    full 15-batch backfill execution.

Features:
    - Reads batch_manifest.json
    - Verifies SHA256 hash for each batch file
    - Verifies record count matches manifest
    - Checks for missing or extra files
    - Generates pre-flight verification report

Dependencies:
    - pandas, openpyxl

Author: R. A. Carucci
Created: 2026-02-06
Version: 1.0.0
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
except ImportError as e:
    print(f"[ERROR] Missing required dependency: {e}")
    print("Install with: pip install pandas openpyxl")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Batch directory (should be copied to server)
BATCHES_DIR = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\batches")
MANIFEST_FILENAME = "batch_manifest.json"

# Optional: Server batch directory (for verification after copy)
SERVER_BATCHES_DIR = Path(r"C:\HPD ESRI\03_Data\CAD\Backfill\Batches")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_manifest(batches_dir: Path) -> dict:
    """Load batch_manifest.json."""
    manifest_path = batches_dir / MANIFEST_FILENAME

    if not manifest_path.exists():
        print(f"\n[ERROR] Manifest not found: {manifest_path}")
        print("        Run split_baseline_into_batches.py first")
        sys.exit(1)

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    return manifest


def verify_batch_file(batch_metadata: dict, batches_dir: Path) -> dict:
    """
    Verify single batch file integrity.

    Returns:
        dict: Verification result with status and details
    """
    batch_path = batches_dir / batch_metadata["filename"]
    result = {
        "batch_number": batch_metadata["batch_number"],
        "filename": batch_metadata["filename"],
        "exists": False,
        "hash_match": False,
        "record_count_match": False,
        "errors": []
    }

    # Check if file exists
    if not batch_path.exists():
        result["errors"].append("File not found")
        return result

    result["exists"] = True

    # Verify SHA256 hash
    try:
        calculated_hash = calculate_sha256(batch_path)
        expected_hash = batch_metadata["sha256_hash"]

        if calculated_hash == expected_hash:
            result["hash_match"] = True
        else:
            result["errors"].append(
                f"Hash mismatch (expected: {expected_hash[:16]}..., got: {calculated_hash[:16]}...)"
            )
    except Exception as e:
        result["errors"].append(f"Hash calculation failed: {e}")

    # Verify record count
    try:
        df = pd.read_excel(batch_path, sheet_name="Sheet1", engine="openpyxl")
        actual_count = len(df)
        expected_count = batch_metadata["record_count"]

        if actual_count == expected_count:
            result["record_count_match"] = True
        else:
            result["errors"].append(
                f"Record count mismatch (expected: {expected_count:,}, got: {actual_count:,})"
            )
    except Exception as e:
        result["errors"].append(f"Record count verification failed: {e}")

    return result


def verify_all_batches(manifest: dict, batches_dir: Path) -> list:
    """Verify all batch files in manifest."""
    print(f"\n[1/3] Verifying {len(manifest['batches'])} batch files")
    print(f"      Directory: {batches_dir}")

    results = []

    for batch_metadata in manifest["batches"]:
        batch_num = batch_metadata["batch_number"]
        filename = batch_metadata["filename"]

        print(f"      Batch {batch_num:02d}: {filename}... ", end="", flush=True)

        result = verify_batch_file(batch_metadata, batches_dir)
        results.append(result)

        if result["exists"] and result["hash_match"] and result["record_count_match"]:
            print("[PASS]")
        else:
            print("[FAIL]")
            for error in result["errors"]:
                print(f"                {error}")

    return results


def check_for_extra_files(manifest: dict, batches_dir: Path) -> list:
    """Check for unexpected Excel files in batch directory."""
    print(f"\n[2/3] Checking for unexpected files")

    expected_files = {b["filename"] for b in manifest["batches"]}
    expected_files.add(MANIFEST_FILENAME)

    actual_files = set()
    for file_path in batches_dir.glob("*.xlsx"):
        actual_files.add(file_path.name)

    extra_files = actual_files - expected_files

    if extra_files:
        print(f"      [WARNING] Found {len(extra_files)} unexpected file(s):")
        for filename in sorted(extra_files):
            print(f"                {filename}")
    else:
        print(f"      [PASS] No unexpected files found")

    return list(extra_files)


def generate_verification_report(
    manifest: dict,
    results: list,
    extra_files: list,
    batches_dir: Path
) -> None:
    """Generate verification report."""
    print(f"\n[3/3] Generating verification report")

    # Calculate statistics
    total_batches = len(results)
    passed = sum(
        1 for r in results
        if r["exists"] and r["hash_match"] and r["record_count_match"]
    )
    failed = total_batches - passed

    # Build report
    report_lines = [
        "=" * 70,
        "BATCH INTEGRITY VERIFICATION REPORT",
        "=" * 70,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Directory: {batches_dir}",
        "",
        "SUMMARY:",
        f"  Total batches: {total_batches}",
        f"  Passed: {passed} ({(passed/total_batches*100):.1f}%)",
        f"  Failed: {failed} ({(failed/total_batches*100):.1f}%)",
        "",
        "VERIFICATION RESULTS:",
        ""
    ]

    # Add batch results
    for result in results:
        status = "PASS" if (
            result["exists"] and
            result["hash_match"] and
            result["record_count_match"]
        ) else "FAIL"

        report_lines.append(
            f"  Batch {result['batch_number']:02d}: {result['filename']:<40} [{status}]"
        )

        if result["errors"]:
            for error in result["errors"]:
                report_lines.append(f"            - {error}")

    # Add extra files section
    if extra_files:
        report_lines.append("")
        report_lines.append("UNEXPECTED FILES:")
        for filename in sorted(extra_files):
            report_lines.append(f"  - {filename}")

    # Add manifest reconciliation
    expected_records = 754409  # From baseline
    actual_manifest_records = manifest.get('total_records', 0)

    report_lines.extend([
        "",
        "MANIFEST RECONCILIATION:",
        f"  Expected total records: {expected_records:,}",
        f"  Manifest total records: {actual_manifest_records:,}",
        f"  Match: {'YES' if actual_manifest_records == expected_records else 'NO'}",
        "",
    ])

    # Final status
    if failed == 0 and not extra_files:
        report_lines.extend([
            "=" * 70,
            "STATUS: READY FOR BACKFILL",
            "=" * 70,
            "All batch files verified and ready for Monday's full execution.",
            "Data is safe and locked down for the weekend.",
            ""
        ])
    else:
        report_lines.extend([
            "=" * 70,
            "STATUS: ISSUES DETECTED",
            "=" * 70,
            "Review and resolve issues before proceeding with backfill.",
            ""
        ])

    report_lines.append("=" * 70)

    # Write report
    report_text = "\n".join(report_lines)
    report_path = batches_dir / "batch_integrity_verification.txt"
    report_path.write_text(report_text)

    # Print to console
    print(report_text)
    print(f"\nReport saved to: {report_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("=" * 70)
    print("BATCH INTEGRITY VERIFICATION - Pre-Weekend Lockdown")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    try:
        # Check if batches directory exists
        if not BATCHES_DIR.exists():
            print(f"\n[ERROR] Batches directory not found: {BATCHES_DIR}")
            print("        Run split_baseline_into_batches.py first")
            return 1

        # Load manifest
        manifest = load_manifest(BATCHES_DIR)

        # Verify all batches
        results = verify_all_batches(manifest, BATCHES_DIR)

        # Check for extra files
        extra_files = check_for_extra_files(manifest, BATCHES_DIR)

        # Generate verification report
        generate_verification_report(manifest, results, extra_files, BATCHES_DIR)

        # Return exit code
        failed = sum(
            1 for r in results
            if not (r["exists"] and r["hash_match"] and r["record_count_match"])
        )

        if failed > 0 or extra_files:
            print("\n[WARNING] Verification detected issues - review report before proceeding")
            return 1
        else:
            print("\n[SUCCESS] All batches verified - ready for backfill execution")
            return 0

    except Exception as e:
        print(f"\n[ERROR] Fatal error during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
