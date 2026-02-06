# Scheduled Upload Guide - Publish Call Data at 3 AM

**Created:** February 4, 2026  
**Purpose:** Automate the "Publish Call Data" tool to run during off-peak hours (3 AM)

---

## 🎯 What This Does

Automatically runs the ArcGIS Pro "Publish Call Data" tool at 3 AM to upload 565,870 records to ArcGIS Online feature service during off-peak network hours.

---

## 📋 Prerequisites

1. ✅ RDP server stays powered on overnight
2. ✅ You remain logged into the RDP session (or auto-login configured)
3. ✅ Network connection available
4. ✅ ArcGIS Pro license active

---

## 🚀 Setup Instructions (5 minutes)

### Step 1: Copy Files to RDP Server

**Option A: If on RDP now**
1. Copy these 2 files from your local machine to the RDP server's `C:\Temp\`:
   - `scheduled_publish_call_data.py`
   - `Schedule-PublishCallData.ps1`

**Option B: Via OneDrive (if accessible from RDP)**
```
Source (local): C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\
Files: scheduled_publish_call_data.py, Schedule-PublishCallData.ps1
Destination (RDP): C:\Temp\
```

### Step 2: Run the Setup Script on RDP Server

**In RDP session, open PowerShell as Administrator:**

```powershell
cd C:\Temp
.\Schedule-PublishCallData.ps1
```

**Or, if files are in OneDrive path accessible from RDP:**

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
.\Schedule-PublishCallData.ps1
```

The script will:
- ✅ Verify all required files exist
- ✅ Show task configuration
- ✅ Ask for confirmation
- ✅ Create Windows Scheduled Task
- ✅ Set to run at 3:00 AM

### Step 3: Verify Task Created

**Check in Task Scheduler:**
```
1. Open Task Scheduler (taskschd.msc)
2. Look for: "ArcGIS_Publish_Call_Data_3AM"
3. Verify:
   - Status: Ready
   - Next Run Time: Tomorrow at 3:00 AM
   - Trigger: Daily at 3:00 AM
```

---

## 🧪 Optional: Test the Task Now

Before leaving it to run at 3 AM, you can test it:

```powershell
Start-ScheduledTask -TaskName "ArcGIS_Publish_Call_Data_3AM"
```

Then monitor:
- Task Scheduler: Watch "Last Run Result"
- Logs: `C:\Temp\arcgis_scheduled_tasks\publish_call_data_YYYYMMDD_HHMMSS.log`

**To stop a running test:**
```powershell
Stop-ScheduledTask -TaskName "ArcGIS_Publish_Call_Data_3AM"
```

---

## 📊 Monitoring

### Check Task Status (Tomorrow Morning)

**PowerShell:**
```powershell
Get-ScheduledTask -TaskName "ArcGIS_Publish_Call_Data_3AM" | Select-Object TaskName, State, LastRunTime, LastTaskResult
```

**Task Scheduler GUI:**
```
1. Open Task Scheduler
2. Click on "ArcGIS_Publish_Call_Data_3AM"
3. Check:
   - Last Run Time
   - Last Run Result (0x0 = success)
   - History tab for details
```

### Check Logs

**Log Location:**
```
C:\Temp\arcgis_scheduled_tasks\publish_call_data_YYYYMMDD_HHMMSS.log
```

**What to look for:**
- `SUCCESS: Publish Call Data completed successfully` ✅
- `ERROR: Tool failed with exception` ❌
- Tool messages and timestamps

### Verify Upload Success

**Check ArcGIS Online:**
```
1. Log into https://hpd0223.maps.arcgis.com
2. Go to CallsForService feature service
3. Check record count: Should be 565,870
4. Check Data tab: "Phone/911" should NOT exist
5. Verify last modified date matches 3 AM run time
```

---

## 🔧 Troubleshooting

### Task Shows "Error" Status

**Check the log file for details:**
```powershell
Get-Content "C:\Temp\arcgis_scheduled_tasks\publish_call_data_*.log" -Tail 50
```

**Common Issues:**

1. **"Input file not found"**
   - Solution: Verify `C:\HPD ESRI\03_Data\CAD\Backfill\_STAGING\ESRI_CADExport.xlsx` exists

2. **"Cannot import toolbox"**
   - Solution: Ensure ArcGIS Pro license is active and you're logged into RDP session

3. **"Network error" or "Timeout"**
   - Solution: Network issue - retry manually or reschedule for next night

### Task Didn't Run

**Possible reasons:**
- RDP server was off/restarted
- User not logged in (some tasks require active session)
- Network unavailable at 3 AM

**Check History:**
```
Task Scheduler > ArcGIS_Publish_Call_Data_3AM > History tab
```

---

## 🛑 Stop/Remove the Task

### Disable Without Removing
```powershell
Disable-ScheduledTask -TaskName "ArcGIS_Publish_Call_Data_3AM"
```

### Remove Completely
```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality"
.\Schedule-PublishCallData.ps1 -RemoveTask
```

Or manually:
```powershell
Unregister-ScheduledTask -TaskName "ArcGIS_Publish_Call_Data_3AM" -Confirm:$false
```

---

## 📱 Remote Access from Laptop

### Windows Laptop:
```
1. Open "Remote Desktop Connection" (mstsc.exe)
2. Computer: [RDP Server IP/Name]
3. Username: [Your Username]
4. Connect
```

### Mac Laptop:
```
1. Install "Microsoft Remote Desktop" from App Store
2. Add PC with server details
3. Connect with credentials
```

**Then check task status:**
```powershell
Get-ScheduledTask -TaskName "ArcGIS_Publish_Call_Data_3AM" | Select-Object TaskName, State, LastRunTime, LastTaskResult
```

---

## ⏰ Schedule Options

### Run Once Tomorrow Only
```powershell
.\Schedule-PublishCallData.ps1 -RunOnce
```

### Run Daily at Different Time (e.g., 2:30 AM)
```powershell
.\Schedule-PublishCallData.ps1 -Time "02:30:00"
```

### Custom Task Name
```powershell
.\Schedule-PublishCallData.ps1 -TaskName "Custom_Upload_Task"
```

---

## ✅ Success Checklist (Tomorrow Morning)

- [ ] Task shows "Last Run Result: Success (0x0)"
- [ ] Log file shows "SUCCESS: Publish Call Data completed successfully"
- [ ] ArcGIS Online feature service has 565,870 records
- [ ] Dashboard no longer shows "Phone/911" combined values
- [ ] Dashboard shows separate "Phone" and "9-1-1" options

---

## 📞 If Issues Occur

1. **Check the log file first** - it will tell you exactly what failed
2. **Verify network was available** during the 3 AM window
3. **Try running manually** from ArcGIS Pro to confirm it works
4. **Reschedule for next night** if needed

---

**Created:** 2026-02-04 12:45 AM  
**Status:** Ready to deploy  
**Estimated Run Time:** 60-90 minutes (3:00 AM - 4:30 AM)
