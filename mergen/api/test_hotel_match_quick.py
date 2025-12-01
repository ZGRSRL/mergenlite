#!/usr/bin/env python3
"""Quick hotel match test - just start and check logs."""
import requests
import time

API_BASE = "http://localhost:8000"
OPP_ID = 6

print("🚀 Quick Hotel Match Test...")
print()

# Start Hotel Match
hotel_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": OPP_ID,
        "analysis_type": "hotel_match"
    }
)

if hotel_resp.status_code == 200:
    hotel_result = hotel_resp.json()
    hotel_analysis_id = hotel_result.get("analysis_result_id")
    print(f"✅ Hotel Match Analysis ID: {hotel_analysis_id}")
    print()
    
    # Wait for completion
    print(f"⏳ Waiting for completion...")
    for j in range(20):
        time.sleep(15)
        hotel_status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
        if hotel_status_resp.status_code == 200:
            hotel_status_data = hotel_status_resp.json()
            hotel_status = hotel_status_data.get('status')
            print(f"   Status: {hotel_status} ({j*15}s)")
            
            if hotel_status == 'completed':
                print(f"   ✅ Completed!")
                hotels = hotel_status_data.get('result_json', {}).get('hotels', [])
                print(f"   Hotels found: {len(hotels)}")
                break
            elif hotel_status == 'failed':
                print(f"   ❌ Failed!")
                break

