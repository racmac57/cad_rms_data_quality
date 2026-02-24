"""
Geocode December 2025 CAD data only.
Run this with ArcGIS Pro Python (propy) so geocoding works. Takes ~5-15 min for one month.
Output has latitude/longitude for use in backfill pipeline.
"""
import sys
from pathlib import Path

# Paths - adjust if your OneDrive root differs
ONEDRIVE = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack")
DEC_2025_INPUT = ONEDRIVE / r"05_EXPORTS\_CAD\monthly\2025\2025_12_CAD.xlsx"
OUTPUT_DIR = ONEDRIVE / r"13_PROCESSED_DATA\ESRI_Polished\cached\december_2025"
OUTPUT_NAME = "2025_12_CAD_GEO_CACHED.xlsx"

def main():
    if not DEC_2025_INPUT.exists():
        print(f"ERROR: December 2025 file not found: {DEC_2025_INPUT}")
        print("  Check that 2025_12_CAD.xlsx exists in 05_EXPORTS\\_CAD\\monthly\\2025\\")
        return 1

    # Delegate to existing geocoding cache
    repo_scripts = Path(__file__).resolve().parent
    create_geocoding = repo_scripts / "create_geocoding_cache.py"
    if not create_geocoding.exists():
        print(f"ERROR: create_geocoding_cache.py not found: {create_geocoding}")
        return 1

    # Import and run (same process so arcpy is already loaded if running under propy)
    import create_geocoding_cache as gcc
    result = gcc.create_geocoding_cache(
        str(DEC_2025_INPUT),
        str(OUTPUT_DIR),
        use_arcpy=True,
        output_filename=OUTPUT_NAME,
    )
    print(f"Output: {OUTPUT_DIR / OUTPUT_NAME}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
