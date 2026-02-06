"""
ArcGIS Pro Publish Tool Runner - Staged Batch Support
======================================================
Purpose: Execute TransformCallData_tbx1 with heartbeat monitoring and batch mode support
Run via: ArcGIS Pro Python environment (propy.bat)
Date: 2026-02-06
Author: R. A. Carucci
Version: 2.0.0 (Staged Backfill with Watchdog)

Features:
- Heartbeat file updates for watchdog monitoring
- Batch mode detection (overwrite vs append)
- Support for pre-geocoded X/Y coordinates
- Marker file creation for batch sequencing
"""
import arcpy
import sys
import json
import time
from pathlib import Path
from datetime import datetime

def load_config(config_path):
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load config from {config_path}: {e}")
        sys.exit(1)

def update_heartbeat(heartbeat_file):
    """
    Write current timestamp to heartbeat file for watchdog monitoring.
    
    The PowerShell orchestrator monitors this file to detect silent hangs.
    If heartbeat is not updated within 5 minutes, the process is killed.
    """
    try:
        Path(heartbeat_file).write_text(str(time.time()))
    except Exception as e:
        print(f"WARNING: Failed to update heartbeat: {e}")

def detect_batch_number(staging_dir):
    """
    Extract batch number from marker file created by orchestrator.
    
    Returns:
        int or None: Batch number if marker exists, None otherwise
    """
    batch_marker = Path(staging_dir) / "_current_batch.txt"
    
    if batch_marker.exists():
        try:
            return int(batch_marker.read_text().strip())
        except Exception:
            pass
    
    return None

def main():
    """Main execution function."""
    print("=" * 70)
    print("ARCGIS PRO PUBLISH TOOL RUNNER")
    print("=" * 70)
    print(f"Run time: {datetime.now().isoformat()}")
    print(f"ArcGIS Pro version: {arcpy.GetInstallInfo()['Version']}")
    print()
    
    # Get config path from command line argument
    if len(sys.argv) < 2:
        print("ERROR: Config path not provided")
        print("Usage: propy.bat run_publish_call_data.py <config.json>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    print(f"[1] Loading configuration from: {config_path}")
    config = load_config(config_path)
    print("    ✓ Config loaded successfully")
    
    # Extract paths from config
    toolbox_path = config['paths']['arcgis_toolbox']
    toolbox_alias = config['paths']['arcgis_tool_alias']
    tool_name = config['paths']['arcgis_tool_python_name']
    tool_callable = config['paths']['arcgis_tool_callable']
    staging_file = config['paths']['staging_file']
    staging_dir = config['paths']['staging_dir']
    
    # Heartbeat file for watchdog monitoring
    heartbeat_file = Path(staging_dir) / "heartbeat.txt"
    
    print(f"\n[2] Configuration:")
    print(f"    Toolbox:       {toolbox_path}")
    print(f"    Alias:         {toolbox_alias}")
    print(f"    Tool:          {tool_name}")
    print(f"    Callable:      {tool_callable}")
    print(f"    Staging file:  {staging_file}")
    print(f"    Heartbeat:     {heartbeat_file}")
    
    # Verify staging file exists
    if not Path(staging_file).exists():
        print(f"\n✗ ERROR: Staging file does not exist: {staging_file}")
        sys.exit(1)
    
    staging_size = Path(staging_file).stat().st_size / (1024 * 1024)  # MB
    print(f"    Staging size:  {staging_size:.2f} MB")
    
    # Detect batch mode
    marker_file = Path(staging_dir) / "is_first_batch.txt"
    batch_num = detect_batch_number(staging_dir)
    
    if marker_file.exists():
        mode = "APPEND"
        batch_info = f"Batch {batch_num}" if batch_num else "Subsequent Batch"
    else:
        mode = "OVERWRITE"
        batch_info = "Batch 01 (Initial)"
    
    print(f"\n[3] Batch Mode Detected:")
    print(f"    Mode:          {mode}")
    print(f"    Batch:         {batch_info}")
    print(f"    Marker exists: {marker_file.exists()}")
    
    try:
        # Step 4: Import toolbox
        print(f"\n[4] Importing toolbox with alias '{toolbox_alias}'...")
        arcpy.ImportToolbox(toolbox_path, toolbox_alias)
        print("    ✓ Toolbox imported successfully")
        
        # Step 5: Initialize heartbeat (CRITICAL for watchdog)
        print(f"\n[5] Initializing heartbeat monitoring...")
        update_heartbeat(heartbeat_file)
        print(f"    ✓ Heartbeat initialized: {heartbeat_file}")
        
        # Step 6: Run the tool
        print(f"\n[6] Running tool: {tool_name} ({mode} mode)")
        print(f"    This may take several minutes...")
        print(f"    Watchdog monitoring active (5-minute timeout)")
        print()
        
        # Call the tool using the confirmed callable format
        # CRITICAL: Use arcpy.TransformCallData_tbx1() format only
        # NOTE: If tool supports X/Y parameters, pass them here:
        #       result = arcpy.TransformCallData_tbx1(staging_file, "X_Coord", "Y_Coord")
        result = arcpy.TransformCallData_tbx1()
        
        # Update heartbeat after successful completion
        update_heartbeat(heartbeat_file)
        print(f"    ✓ Heartbeat updated after tool completion")
        
        # Step 7: Capture and display geoprocessing messages
        messages = arcpy.GetMessages()
        print("\n" + "=" * 70)
        print("GEOPROCESSING MESSAGES")
        print("=" * 70)
        print(messages)
        print("=" * 70)
        
        # Step 8: Check for errors
        severity = arcpy.GetMaxSeverity()
        
        print(f"\n[7] Tool execution completed")
        print(f"    Max severity: {severity}")
        print(f"    Batch mode:   {mode}")
        
        if severity == 2:
            print("    ✗ ERROR: Tool failed")
            sys.exit(1)
        elif severity == 1:
            print("    ⚠ WARNING: Tool completed with warnings")
            # Create marker file after first successful run (even with warnings)
            if not marker_file.exists():
                marker_file.write_text(f"First batch completed at {datetime.now().isoformat()}")
                print(f"    ✓ Marker file created: {marker_file}")
            sys.exit(0)
        else:
            print("    ✓ SUCCESS: Tool completed successfully")
            # Create marker file after first successful run
            if not marker_file.exists():
                marker_file.write_text(f"First batch completed at {datetime.now().isoformat()}")
                print(f"    ✓ Marker file created: {marker_file}")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n✗ EXCEPTION: {e}")
        print("\n" + "=" * 70)
        print("ARCPY MESSAGES")
        print("=" * 70)
        try:
            print(arcpy.GetMessages())
        except:
            print("(No ArcPy messages available)")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
