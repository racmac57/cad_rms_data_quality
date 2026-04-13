"""
Tool Discovery Script for HPD ESRI Backfill Workflow
====================================================
Purpose: Find the exact Python callable name and output dataset for Publish Call Data tool
Run: Using ArcGIS Pro Python environment on the server
Date: 2026-02-02
Author: R. A. Carucci

This script must be run on HPD2022LAWSOFT server using ArcGIS Pro Python.
"""
import arcpy
import json
from pathlib import Path
from datetime import datetime

# Configuration
TOOLBOX_PATH = r"C:\HPD ESRI\LawEnforcementDataManagement_New\LawEnforcementDataManagement.atbx"
TOOLBOX_ALIAS = "tbx1"
OUTPUT_JSON = r"C:\HPD ESRI\04_Scripts\_out\tool_discovery.json"

print("=" * 70)
print("TOOL DISCOVERY SCRIPT - HPD ESRI Backfill Workflow")
print("=" * 70)
print(f"Run time: {datetime.now().isoformat()}")
print(f"ArcGIS Pro version: {arcpy.GetInstallInfo()['Version']}")
print()

results = {
    "timestamp": datetime.now().isoformat(),
    "arcgis_version": arcpy.GetInstallInfo()['Version'],
    "success": False,
    "toolbox_path": TOOLBOX_PATH,
    "toolbox_alias": TOOLBOX_ALIAS,
    "all_tools_count": 0,
    "tbx1_tools": [],
    "publish_candidates": [],
    "recommended_tool": None,
    "error": None
}

try:
    # Step 1: Import toolbox
    print(f"[Step 1] Importing toolbox...")
    print(f"  Path: {TOOLBOX_PATH}")
    print(f"  Alias: {TOOLBOX_ALIAS}")
    arcpy.ImportToolbox(TOOLBOX_PATH, TOOLBOX_ALIAS)
    print("  ✓ SUCCESS: Toolbox imported")
    
    # Step 2: List all tools
    print(f"\n[Step 2] Listing all tools in ArcGIS Pro environment...")
    all_tools = arcpy.ListTools()
    results["all_tools_count"] = len(all_tools)
    print(f"  Found {len(all_tools)} tools total in Pro environment")
    
    # Step 3: Filter for tools from our toolbox
    print(f"\n[Step 3] Filtering for tools from '{TOOLBOX_ALIAS}' toolbox...")
    tbx1_tools = [t for t in all_tools if t.endswith(f"_{TOOLBOX_ALIAS}")]
    results["tbx1_tools"] = tbx1_tools
    
    print(f"  Found {len(tbx1_tools)} tools from {TOOLBOX_ALIAS}:")
    for tool in tbx1_tools:
        print(f"    • {tool}")
    
    # Step 4: Identify likely publish/transform tools
    print(f"\n[Step 4] Identifying publish/transform candidates...")
    keywords = ["Transform", "Publish", "Call", "Data", "CAD"]
    publish_candidates = []
    
    for tool in tbx1_tools:
        tool_upper = tool.upper()
        matches = [kw for kw in keywords if kw.upper() in tool_upper]
        if matches:
            publish_candidates.append({
                "tool_name": tool,
                "matched_keywords": matches
            })
    
    results["publish_candidates"] = publish_candidates
    
    print(f"  Found {len(publish_candidates)} candidate(s):")
    for candidate in publish_candidates:
        print(f"    • {candidate['tool_name']}")
        print(f"      Matches: {', '.join(candidate['matched_keywords'])}")
    
    # Step 5: Recommend the most likely tool
    if publish_candidates:
        # Prefer tools with "Transform" and "Call" in the name
        best_match = None
        best_score = 0
        
        for candidate in publish_candidates:
            score = 0
            tool_name = candidate["tool_name"]
            if "Transform" in tool_name:
                score += 2
            if "Call" in tool_name:
                score += 2
            if "Data" in tool_name:
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        if best_match:
            tool_name = best_match["tool_name"]
            print(f"\n[Step 5] Recommended tool: {tool_name}")
            
            # Try to get tool callable format
            try:
                # Test if tool is callable
                tool_obj = getattr(arcpy, tool_name, None)
                if tool_obj:
                    print(f"  ✓ Tool is callable as: arcpy.{tool_name}()")
                    callable_format = f"arcpy.{tool_name}()"
                else:
                    print(f"  ⚠ Tool object not found, but name is valid")
                    callable_format = f"arcpy.{tool_name}()"
                
                results["recommended_tool"] = {
                    "python_name": tool_name,
                    "callable": callable_format,
                    "display_name": "Publish Call Data",
                    "toolbox_alias": TOOLBOX_ALIAS,
                    "confidence": "HIGH" if best_score >= 3 else "MEDIUM"
                }
                
            except Exception as e:
                print(f"  ⚠ Could not test callability: {e}")
                results["recommended_tool"] = {
                    "python_name": tool_name,
                    "callable": f"arcpy.{tool_name}()",
                    "display_name": "Publish Call Data",
                    "toolbox_alias": TOOLBOX_ALIAS,
                    "confidence": "MEDIUM",
                    "note": "Could not verify callability"
                }
    else:
        print(f"\n[Step 5] ⚠ WARNING: No publish/transform candidates found")
        print("  All tools from tbx1:")
        for tool in tbx1_tools:
            print(f"    • {tool}")
    
    results["success"] = True
    print(f"\n✓ Discovery completed successfully!")
    
except Exception as e:
    results["error"] = str(e)
    results["success"] = False
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Save results
print(f"\n[Step 6] Saving results...")
print(f"  Output: {OUTPUT_JSON}")

try:
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    print("  ✓ Results saved successfully")
except Exception as e:
    print(f"  ✗ ERROR saving results: {e}")

# Print summary
print("\n" + "=" * 70)
print("DISCOVERY SUMMARY")
print("=" * 70)
if results["success"]:
    if results["recommended_tool"]:
        print(f"✓ Recommended Tool Found:")
        print(f"  Python Name:  {results['recommended_tool']['python_name']}")
        print(f"  Callable:     {results['recommended_tool']['callable']}")
        print(f"  Confidence:   {results['recommended_tool']['confidence']}")
        print()
        print("Next Steps:")
        print("1. Review the output JSON file:")
        print(f"   Get-Content '{OUTPUT_JSON}' | ConvertFrom-Json | Format-List")
        print()
        print("2. Copy the 'python_name' to config.json:")
        print(f"   \"arcgis_tool_python_name\": \"{results['recommended_tool']['python_name']}\"")
        print()
        print("3. Test calling the tool manually to verify it works")
    else:
        print("⚠ No recommended tool found")
        print("  Review the tbx1_tools list in the JSON output")
else:
    print("✗ Discovery failed - see error details above")
print("=" * 70)
