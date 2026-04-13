# Field Mapping Reference: Source Excel -> Online Service
# Based on ModelBuilder "Publish Call Data"

FIELD_MAPPING = {
    # Core identification
    'ReportNumberNew': 'callid',           # Call ID / Report Number
    
    # Call classification
    'Incident': 'calltype',                 # Call Type / Incident
    'How_Reported': 'callsource',          # How Reported / Call Source
    
    # Location
    'FullAddress2': 'fulladdr',            # Full Address
    'Grid': 'grid',                        # Grid (may need to check target field name)
    'ZoneCalc': 'zone',                    # Zone
    
    # Dates/Times (these require ConvertTimeField transformation)
    'Time_Of_Call': 'calldate',            # Needs datetime conversion
    'Time_Dispatched': 'dispatchdate',     # Needs datetime conversion
    'Time_Out': 'enroutedate',             # Needs datetime conversion  
    'Time_In': 'cleardate',                # Needs datetime conversion
    
    # Calculated fields (these are computed, not direct mappings)
    # 'dispatchtime' = (dispatchdate - calldate) in minutes
    # 'queuetime' = (enroutedate - dispatchdate) in minutes
    # 'cleartime' = (cleardate - enroutedate) in minutes
    # 'responsetime' = dispatchtime + queuetime
    
    # Date attributes (computed from calldate)
    # 'calldow' = day of week name
    # 'calldownum' = day of week number
    # 'callhour' = hour
    # 'callmonth' = month
    # 'callyear' = year
    
    # Other fields from Excel
    'cYear': None,      # Already have callyear computed
    'cMonth': None,     # Already have callmonth computed
    'Hour_Calc': None,  # Already have callhour computed
}

# Target schema fields (from diagnostic)
TARGET_FIELDS = [
    'callid', 'callcat', 'calltype', 'priority', 'description', 
    'callsource', 'callerinfo', 'fulladdr', 'city', 'state',
    # ... and 30 more fields
]

print("""
KEY FINDING:
============
The ModelBuilder does NOT just append raw Excel data. It performs:

1. Field name transformations (ReportNumberNew -> callid)
2. DateTime conversions (Text -> Date fields)
3. Calculated fields (response times, etc.)
4. Date attribute extraction (day of week, hour, etc.)
5. THEN geocodes addresses
6. THEN appends to online service

Our XY coordinate script skipped ALL of these transformations!
That's why the online service has 565K records with geometry but NULL attributes.
""")
