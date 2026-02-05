# Pre-Flight: Copy Scripts to Server (5 minutes)
# Run this FIRST if the orchestrator scripts don't exist on the server yet

# ==============================================================================
# Check if scripts exist on server
# ==============================================================================

# Connect to HPD2022LAWSOFT via RDP, then run:

Test-Path "C:\HPD ESRI\04_Scripts\Invoke-CADBackfillPublish.ps1"
Test-Path "C:\HPD ESRI\04_Scripts\Test-PublishReadiness.ps1"
Test-Path "C:\HPD ESRI\04_Scripts\run_publish_call_data.py"
Test-Path "C:\HPD ESRI\04_Scripts\config.json"

# If any return False, copy them to server:

# ==============================================================================
# Option A: Copy via network share (from LOCAL machine)
# ==============================================================================

# Try SMB share first:
Copy-Item "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\arcgis\*" `
          "\\HPD2022LAWSOFT\c$\HPD ESRI\04_Scripts\" `
          -Include "*.ps1","*.py","*.json" `
          -Force

# ==============================================================================
# Option B: Manual copy via RDP (if network share blocked)
# ==============================================================================

# 1. On LOCAL machine, open File Explorer:
#    C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\arcgis\

# 2. Copy these 4 files:
#    - Invoke-CADBackfillPublish.ps1
#    - Test-PublishReadiness.ps1
#    - run_publish_call_data.py
#    - config.json

# 3. In RDP session, paste to:
#    C:\HPD ESRI\04_Scripts\

# ==============================================================================
# Verify scripts exist
# ==============================================================================

Get-ChildItem "C:\HPD ESRI\04_Scripts\" | Select-Object Name, Length

# Should show:
#   Invoke-CADBackfillPublish.ps1  (~15 KB)
#   Test-PublishReadiness.ps1      (~10 KB)
#   run_publish_call_data.py       (~3 KB)
#   config.json                    (~2 KB)

# ==============================================================================
# DONE - Now proceed to EXECUTE_NOW_BACKFILL.md Step 1
# ==============================================================================
