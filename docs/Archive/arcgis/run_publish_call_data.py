"""
ArcGIS Pro Publish Tool Runner
================================
Purpose: Execute the Publish Call Data tool (TransformCallData_tbx1) using configuration
Run via: ArcGIS Pro Python environment (propy.bat)
Date: 2026-02-02
Author: R. A. Carucci

This script replaces the inline heredoc pattern for better reliability.
"""
import arcpy
import sys
import json
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
    
    print(f"\n[2] Configuration:")
    print(f"    Toolbox:       {toolbox_path}")
    print(f"    Alias:         {toolbox_alias}")
    print(f"    Tool:          {tool_name}")
    print(f"    Callable:      {tool_callable}")
    print(f"    Staging file:  {staging_file}")
    
    # Verify staging file exists
    if not Path(staging_file).exists():
        print(f"\n✗ ERROR: Staging file does not exist: {staging_file}")
        sys.exit(1)
    
    staging_size = Path(staging_file).stat().st_size / (1024 * 1024)  # MB
    print(f"    Staging size:  {staging_size:.2f} MB")
    
    try:
        # Step 3: Import toolbox
        print(f"\n[3] Importing toolbox with alias '{toolbox_alias}'...")
        arcpy.ImportToolbox(toolbox_path, toolbox_alias)
        print("    ✓ Toolbox imported successfully")
        
        # Step 4: Run the tool
        print(f"\n[4] Running tool: {tool_name}")
        print(f"    This may take several minutes...")
        print()
        
        # Call the tool using the confirmed callable format
        # CRITICAL: Use arcpy.TransformCallData_tbx1() format only
        result = arcpy.TransformCallData_tbx1()
        
        # Step 5: Capture and display geoprocessing messages
        messages = arcpy.GetMessages()
        print("\n" + "=" * 70)
        print("GEOPROCESSING MESSAGES")
        print("=" * 70)
        print(messages)
        print("=" * 70)
        
        # Step 6: Check for errors
        severity = arcpy.GetMaxSeverity()
        
        print(f"\n[5] Tool execution completed")
        print(f"    Max severity: {severity}")
        
        if severity == 2:
            print("    ✗ ERROR: Tool failed")
            sys.exit(1)
        elif severity == 1:
            print("    ⚠ WARNING: Tool completed with warnings")
            sys.exit(0)
        else:
            print("    ✓ SUCCESS: Tool completed successfully")
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
