# 🕒 2026-02-15-20-00-00 (EST)
# Hackensack_PD_ETL/CAD_Geocode_Polisher.py
# Author: R. A. Carucci
# Purpose: Geocode Raw CAD Excel files and export Polished GIS-ready versions.

import arcpy
import os
import pandas as pd

# --- CONFIGURATION ---
arcpy.env.overwriteOutput = True
arcpy.env.workspace = r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished\base"

# Paths
RAW_CAD_DIR = r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\yearly"
POLISHED_DIR = r"C:\Users\carucci_r\OneDrive - City of Hackensack\13_PROCESSED_DATA\ESRI_Polished"
LOCATOR_PATH = r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\GeographicData\NJ_Geocode"
REFERENCE_SCHEMA = os.path.join(arcpy.env.workspace, "Base_Schema.gdb\CAD_Master_Template")

def polish_cad_data(file_name):
    input_path = os.path.join(RAW_CAD_DIR, file_name)
    output_name = file_name.replace(".xlsx", "_POLISHED")
    output_fc = os.path.join(POLISHED_DIR, f"Polished_Data.gdb\{output_name}")

    print(f"--- Processing: {file_name} ---")

    try:
        # 1. Load Excel to Memory Table
        temp_table = "memory\cad_temp"
        arcpy.conversion.ExcelToTable(input_path, temp_table)

        # 2. Geocoding
        # Note: 'Address' is assumed; update 'Address OR Intersection' based on your CAD headers
        print("Geocoding addresses via NJ_Geocode...")
        address_fields = "Address OR Intersection Address VISIBLE NONE" 
        
        arcpy.geocoding.GeocodeAddresses(
            in_table=temp_table,
            address_locator=LOCATOR_PATH,
            in_address_fields=address_fields,
            out_feature_class=output_fc,
            out_relationship_type="STATIC"
        )

        # 3. Polish & Schema Alignment
        # Adding Long/Lat fields specifically for RAG/Backfill if they don't exist
        arcpy.management.AddFields(output_fc, [
            ["Longitude", "DOUBLE"],
            ["Latitude", "DOUBLE"],
            ["Processed_Date", "DATE"]
        ])

        # Calculate Geometry (NJ State Plane to WGS84 for Long/Lat)
        print("Calculating Longitude/Latitude...")
        arcpy.management.CalculateGeometryAttributes(
            output_fc, 
            [["Longitude", "POINT_X"], ["Latitude", "POINT_Y"]],
            coordinate_system=arcpy.SpatialReference(4326) # WGS84 for RAG compatibility
        )

        print(f"SUCCESS: {output_name} created in Polished GDB.")
        
    except Exception as e:
        print(f"ERROR processing {file_name}: {str(e)}")
    finally:
        if arcpy.Exists("memory\cad_temp"):
            arcpy.management.Delete("memory\cad_temp")

# --- EXECUTION ---
if __name__ == "__main__":
    # Process all yearly files currently in the root yearly directory
    for f in os.listdir(RAW_CAD_DIR):
        if f.endswith(".xlsx") and "CAD_ALL" in f:
            polish_cad_data(f)

    print("\nBatch Processing Complete.")