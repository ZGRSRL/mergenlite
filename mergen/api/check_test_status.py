#!/usr/bin/env python3
"""Check test status quickly."""
import requests

API_BASE = "http://localhost:8000"
OPP_ID = 6

print("📊 Test Durumu - Opportunity #6")
print("=" * 50)

# Get all analysis results
resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}/analysis")
if resp.status_code == 200:
    data = resp.json()
    results = data.get('results', [])
    
    # Get latest SOW and Hotel Match
    sow_results = [r for r in results if r.get('analysis_type') == 'sow_draft']
    hotel_results = [r for r in results if r.get('analysis_type') == 'hotel_match']
    
    if sow_results:
        latest_sow = sow_results[0]
        print(f"\n📄 SOW Analysis #{latest_sow.get('id')}: {latest_sow.get('status')}")
    
    if hotel_results:
        latest_hotel = hotel_results[0]
        print(f"🏨 Hotel Match #{latest_hotel.get('id')}: {latest_hotel.get('status')}")
        
        if latest_hotel.get('status') == 'completed':
            # Get details
            detail = requests.get(f"{API_BASE}/api/pipeline/results/{latest_hotel.get('id')}").json()
            hotels = detail.get('result_json', {}).get('hotels', [])
            reqs = detail.get('result_json', {}).get('requirements', {})
            print(f"   City: {reqs.get('city_name', 'N/A')} ({reqs.get('city_code', 'N/A')})")
            print(f"   Hotels: {len(hotels)}")
            if detail.get('result_json', {}).get('fallback_used'):
                print(f"   ⚠️ Fallback kullanıldı")
    else:
        print(f"\n🏨 Hotel Match: Henüz başlatılmadı")

print()

