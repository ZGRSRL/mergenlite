#!/usr/bin/env python3
"""Check locations in analysis 268."""
import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("📍 ANALİZ 268 - LOCATIONS KONTROLÜ")
print("=" * 70)
print()

# Get SOW Analysis 268
resp = requests.get(f"{API_BASE}/api/pipeline/results/268")
if resp.status_code == 200:
    data = resp.json()
    result_json = data.get('result_json', {})
    sow_analysis = result_json.get('sow_analysis', {})
    
    locations = sow_analysis.get('Locations', [])
    print(f"📋 Locations Array: {len(locations)} şehir")
    print()
    
    for i, loc in enumerate(locations, 1):
        city = loc.get('city', 'N/A')
        stadium = loc.get('stadium', 'N/A')
        start_date = loc.get('start_date', 'N/A')
        num_days = loc.get('num_days', 'N/A')
        print(f"   {i}. {city}")
        print(f"      Stadium: {stadium}")
        print(f"      Start: {start_date}, Days: {num_days}")
        print()
    
    # Check if Houston is in the list
    houston_locations = [loc for loc in locations if 'houston' in loc.get('city', '').lower()]
    if houston_locations:
        print(f"✅ Houston bulundu: {len(houston_locations)} adet")
        for loc in houston_locations:
            print(f"   - {loc.get('city')} - Start: {loc.get('start_date')}")
    else:
        print("⚠️ Houston locations array'de bulunamadı!")
    
    # Check EventDetails
    event_details = sow_analysis.get('EventDetails', {})
    print(f"\n📄 Event Details:")
    print(f"   Event Name: {event_details.get('event_name', 'N/A')}")
    print(f"   Location: {event_details.get('location_str', 'N/A')}")
    print(f"   Start Date: {event_details.get('start_date', 'N/A')}")
    print(f"   End Date: {event_details.get('end_date', 'N/A')}")

print()
print("=" * 70)

