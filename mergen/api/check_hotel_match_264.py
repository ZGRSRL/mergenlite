#!/usr/bin/env python3
"""Check hotel match 264 results."""
import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("🏨 HOTEL MATCH 264 KONTROLÜ")
print("=" * 70)
print()

# Get hotel match 264
resp = requests.get(f"{API_BASE}/api/pipeline/results/264")
if resp.status_code == 200:
    data = resp.json()
    result_json = data.get('result_json', {})
    
    print("📄 Hotel Match Result:")
    print(f"   Status: {data.get('status')}")
    print(f"   Keys: {list(result_json.keys())[:20]}")
    print()
    
    # Hotels
    hotels = result_json.get('hotels', [])
    print(f"🏨 Hotels: {len(hotels)} found")
    if hotels:
        for i, hotel in enumerate(hotels[:5], 1):
            print(f"\n   {i}. {hotel.get('name', 'N/A')}")
            print(f"      Score: {hotel.get('score', 'N/A')}")
            print(f"      Price: {hotel.get('price_per_night', 'N/A')}")
            print(f"      Distance: {hotel.get('distance', 'N/A')}")
    else:
        print("   ⚠️ No hotels found!")
        print(f"   Full result_json keys: {list(result_json.keys())}")
        print(f"   Result JSON sample: {json.dumps(result_json, indent=2)[:500]}")

print()
print("=" * 70)

