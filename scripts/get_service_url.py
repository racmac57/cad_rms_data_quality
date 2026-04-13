# 🕒 2026-02-09-09-00-00
# CAD_Backfill_Option_C/get_service_url.py
# Author: R. A. Carucci
# Purpose: Extract FeatureServer REST endpoint URL from ArcGIS Online item ID for backfill operations

import arcpy
import json
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection

def get_service_url_from_item():
    """
    Extract the actual FeatureServer REST endpoint URL from dashboard item ID.
    
    Dashboard Item: https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2
    Returns: Full REST endpoint URL for use in arcpy operations
    """
    
    item_id = "44173f3345974fe79a01bfa463350ce2"
    org_url = "https://hpd0223.maps.arcgis.com"
    
    print("=" * 80)
    print("SERVICE URL DISCOVERY")
    print("=" * 80)
    print(f"\nItem ID: {item_id}")
    print(f"Organization: {org_url}")
    
    # Method 1: Using ArcGIS API for Python (requires arcgis package)
    try:
        print("\n[Method 1] Connecting via ArcGIS API for Python...")
        gis = GIS(org_url, verify_cert=False)  # Uses current ArcGIS Pro credentials
        
        item = gis.content.get(item_id)
        print(f"✅ Item found: {item.title}")
        print(f"   Type: {item.type}")
        
        # Get the service URL
        if hasattr(item, 'url'):
            service_url = item.url
            print(f"\n✅ Service URL: {service_url}")
            
            # Extract layer URLs if it's a FeatureService
            if item.type == "Feature Service":
                flc = FeatureLayerCollection.fromitem(item)
                print(f"\n   Layers in service:")
                for layer in flc.layers:
                    print(f"   - {layer.properties.name} (ID: {layer.properties.id})")
                    print(f"     URL: {layer.url}")
                
                for table in flc.tables:
                    print(f"   - {table.properties.name} (ID: {table.properties.id}) [TABLE]")
                    print(f"     URL: {table.url}")
                    
                    # CFStable is likely a table, not a layer
                    if "CFStable" in table.properties.name or table.properties.id == 0:
                        print(f"\n✅ FOUND CFStable TABLE:")
                        print(f"   URL: {table.url}")
                        print(f"   Record Count: {table.query(where='1=1', return_count_only=True)}")
                        return table.url
            
            return service_url
        else:
            print("⚠️  Item has no direct URL property")
            
    except ImportError:
        print("⚠️  ArcGIS API for Python not available, trying arcpy method...")
    except Exception as e:
        print(f"⚠️  Method 1 failed: {e}")
    
    # Method 2: Using arcpy (more reliable in ArcGIS Pro environment)
    try:
        print("\n[Method 2] Using arcpy to describe layer...")
        
        # Try common URL patterns for HPD
        base_urls = [
            f"https://services.arcgis.com/YourOrgID/arcgis/rest/services/CFStable/FeatureServer/0",
            f"https://services1.arcgis.com/YourOrgID/arcgis/rest/services/CFStable/FeatureServer/0",
            f"https://services.arcgis.com/hpd0223/arcgis/rest/services/CFStable/FeatureServer/0",
        ]
        
        print("\n   Attempting to connect to known URL patterns...")
        for url in base_urls:
            try:
                desc = arcpy.Describe(url)
                print(f"✅ Connected to: {url}")
                print(f"   Feature count: {arcpy.management.GetCount(url)[0]}")
                return url
            except:
                continue
                
    except Exception as e:
        print(f"⚠️  Method 2 failed: {e}")
    
    # Method 3: Manual extraction via REST API
    print("\n[Method 3] Querying ArcGIS REST API directly...")
    import urllib.request
    
    rest_url = f"{org_url}/sharing/rest/content/items/{item_id}?f=json"
    
    try:
        with urllib.request.urlopen(rest_url) as response:
            data = json.loads(response.read().decode())
            
            print(f"✅ Item details retrieved")
            print(f"   Title: {data.get('title', 'Unknown')}")
            print(f"   Type: {data.get('type', 'Unknown')}")
            
            if 'url' in data:
                service_url = data['url']
                print(f"\n✅ Service URL: {service_url}")
                
                # Try to get layer info
                layers_url = f"{service_url}/layers?f=json"
                try:
                    with urllib.request.urlopen(layers_url) as layer_response:
                        layer_data = json.loads(layer_response.read().decode())
                        
                        print("\n   Layers/Tables:")
                        for layer in layer_data.get('layers', []):
                            print(f"   - {layer['name']} (ID: {layer['id']}) [LAYER]")
                        
                        for table in layer_data.get('tables', []):
                            print(f"   - {table['name']} (ID: {table['id']}) [TABLE]")
                            if "CFStable" in table['name'] or table['id'] == 0:
                                table_url = f"{service_url}/{table['id']}"
                                print(f"\n✅ FOUND CFStable TABLE:")
                                print(f"   URL: {table_url}")
                                return table_url
                except:
                    pass
                
                return service_url
                
    except Exception as e:
        print(f"⚠️  Method 3 failed: {e}")
    
    print("\n" + "=" * 80)
    print("❌ Could not automatically determine service URL")
    print("=" * 80)
    print("\nMANUAL STEPS:")
    print("1. Open ArcGIS Pro")
    print("2. In Catalog pane, expand 'Portal' → 'My Content'")
    print("3. Find 'CFStable' or the dashboard layer")
    print("4. Right-click → 'Copy URL'")
    print("5. Paste the URL into the scripts below")
    print("\nOR:")
    print("1. Go to: https://hpd0223.maps.arcgis.com/home/item.html?id=44173f3345974fe79a01bfa463350ce2")
    print("2. Click 'View' button (if it's a layer)")
    print("3. Look for the REST endpoint in the URL or description")
    
    return None

if __name__ == "__main__":
    url = get_service_url_from_item()
    
    if url:
        print("\n" + "=" * 80)
        print("✅ SUCCESS - Use this URL in your backup and truncate scripts:")
        print("=" * 80)
        print(f"\n{url}\n")
        
        # Save to file for easy copy-paste
        with open(r"C:\HPD ESRI\04_Scripts\service_url.txt", "w") as f:
            f.write(url)
        print("✅ URL saved to: C:\\HPD ESRI\\04_Scripts\\service_url.txt")
    else:
        print("\n⚠️  Follow manual steps above to find the service URL")
