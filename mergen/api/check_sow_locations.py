#!/usr/bin/env python3
"""Check SOW Analysis Locations array."""
import requests
import json

API_BASE = "http://localhost:8000"
SOW_RESULT_ID = 204  # Latest SOW analysis

print("=" * 60)
print("🔍 SOW ANALYSIS LOCATIONS KONTROLÜ")
print("=" * 60)
print()

resp = requests.get(f"{API_BASE}/api/pipeline/results/{SOW_RESULT_ID}")
if resp.status_code == 200:
    result = resp.json()
    result_json = result.get('result_json', {})
    if isinstance(result_json, str):
        try:
            result_json = json.loads(result_json) if result_json else {}
        except:
            result_json = {}
    
    sow_analysis = result_json.get('sow_analysis', {})
    print(f"SOW Analysis keys: {list(sow_analysis.keys())[:10]}")
    print()
    
    locations = sow_analysis.get('Locations', [])
    if not locations:
        locations = sow_analysis.get('locations', [])
    
    print(f"Locations array length: {len(locations)}")
    print()
    
    if locations:
        print("First location:")
        print(json.dumps(locations[0], indent=2, ensure_ascii=False))
        print()
        
        # Check city field
        first_loc = locations[0]
        city = first_loc.get('city') or first_loc.get('City')
        print(f"City field: {city}")
    else:
        print("❌ No Locations array found!")
        print()
        print("Available keys in sow_analysis:")
        for key in list(sow_analysis.keys())[:20]:
            print(f"  - {key}")
else:
    print(f"✗ API hatası: {resp.status_code}")

print()
print("=" * 60)
