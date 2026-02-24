# 🕒 2026-02-15-20-15-00 (EST)
# Hackensack_PD_ETL/CAD_Gap_Analysis.py
# Author: R. A. Carucci
# Purpose: Identify date ranges present in Raw folders but missing from Polished GDB.

import arcpy
import os
import re

# --- PATHS ---
RAW_MONTHLY = r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\monthly"
RAW_YEARLY = r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\yearly"
POLISHED_GDB = r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\Polished_Data.gdb"

def get_date_keys(folder_path):
    """Extracts YYYY-MM or YYYY keys from filenames like 2019_CAD_ALL.xlsx"""
    keys = set()
    for f in os.listdir(folder_path):
        # Matches 4 digits (Year) and optional 2 digits (Month)
        match = re.search(r'(\d{4})_?(\d{2})?', f)
        if match:
            year = match.group(1)
            month = match.group(2) if match.group(2) else "ALL"
            keys.add(f"{year}_{month}")
    return keys

def get_polished_keys(gdb_path):
    """Extracts keys from Feature Class names in the Polished GDB"""
    arcpy.env.workspace = gdb_path
    fcs = arcpy.ListFeatureClasses()
    keys = set()
    for fc in fcs:
        match = re.search(r'(\d{4})_?(\d{2})?', fc)
        if match:
            year = match.group(1)
            month = match.group(2) if match.group(2) else "ALL"
            keys.add(f"{year}_{month}")
    return keys

# --- EXECUTION ---
print("--- CAD Backfill Gap Analysis ---")

raw_keys = get_date_keys(RAW_MONTHLY).union(get_date_keys(RAW_YEARLY))
polished_keys = get_polished_keys(POLISHED_GDB)

gaps = sorted(list(raw_keys - polished_keys))

if gaps:
    print(f"\n[!] FOUND {len(gaps)} MISSING PERIODS:")
    print("-" * 30)
    for gap in gaps:
        print(f"MISSING: {gap.replace('_', ' ')}")
    print("-" * 30)
    print("Action: Export these periods from CAD and run Polisher script.")
else:
    print("\n[✓] No gaps found. All raw data has a corresponding polished version.")