"""
Scheduled Task Script: Publish Call Data to ArcGIS Online
Runs ArcGIS Pro Model Builder tool via ArcPy during off-peak hours
Created: 2026-02-04
"""
import arcpy
import sys
import os
from datetime import datetime

# Set up logging
log_dir = r"C:\Temp\arcgis_scheduled_tasks"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"publish_call_data_{timestamp}.log")

def log(message):
    """Write to log file and print"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    with open(log_file, 'a') as f:
        f.write(log_message + '\n')

try:
    log("="*80)
    log("Scheduled Task: Publish Call Data to ArcGIS Online")
    log("="*80)
    
    # Path to the Excel file that the tool expects
    input_file = r"C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx"
    
    log(f"Input file: {input_file}")
    
    # Verify input file exists
    if not os.path.exists(input_file):
        log(f"ERROR: Input file not found: {input_file}")
        sys.exit(1)
    
    log("Input file verified - exists")
    
    # Import the toolbox
    log("Importing ArcGIS toolbox...")
    arcpy.ImportToolbox(r"C:\Program Files\ArcGIS\Pro\Resources\ArcToolbox\toolboxes\Crime Analysis and Safety Tools.tbx")
    
    log("Starting Publish Call Data tool...")
    log("Expected duration: 60-90 minutes for upload step")
    
    # Run the tool
    # Based on earlier discovery, the callable function is TransformCallData
    result = arcpy.TransformCallData_tbx1(input_file)
    
    log("Tool execution completed!")
    log(f"Result: {result}")
    
    # Check messages
    log("\nTool Messages:")
    for i in range(arcpy.GetMessageCount()):
        log(arcpy.GetMessage(i))
    
    log("="*80)
    log("SUCCESS: Publish Call Data completed successfully")
    log("="*80)
    
    sys.exit(0)
    
except Exception as e:
    log("="*80)
    log(f"ERROR: Tool failed with exception")
    log(f"Error: {str(e)}")
    log("="*80)
    
    # Log any ArcPy messages
    if arcpy.GetMessageCount() > 0:
        log("\nArcPy Messages:")
        for i in range(arcpy.GetMessageCount()):
            log(arcpy.GetMessage(i))
    
    sys.exit(1)
