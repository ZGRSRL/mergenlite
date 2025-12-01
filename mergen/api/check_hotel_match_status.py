#!/usr/bin/env python3
"""Check Hotel Match status and requirements."""
import requests
import json

API_BASE = "http://localhost:8000"

# Check latest hotel match
print("=" * 60)
print("🏨 HOTEL MATCH DURUM KONTROLÜ")
print("=" * 60)
print()

# Get all hotel match results for opportunity 3
resp = requests.get(f"{API_BASE}/api/pipeline/results", params={"opportunity_id": 3})
if resp.status_code == 200:
    results = resp.json()
    hotel_matches = [r for r in results if r.get('analysis_type') == 'hotel_match']
    hotel_matches.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    print(f"Toplam Hotel Match analizi: {len(hotel_matches)}")
    print()
    
    if hotel_matches:
        latest = hotel_matches[0]
        analysis_id = latest.get('id')
        status = latest.get('status')
        
        print(f"En son Hotel Match (ID: {analysis_id}):")
        print(f"  Status: {status}")
        print(f"  Created: {latest.get('created_at', 'N/A')}")
        print()
        
        # Get detailed result
        resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
        if resp.status_code == 200:
            result = resp.json()
            result_json = result.get('result_json', {})
            if isinstance(result_json, str):
                try:
                    result_json = json.loads(result_json) if result_json else {}
                except:
                    result_json = {}
            
            if not result_json:
                result_json = {}
            
            requirements = result_json.get('requirements', {}) if result_json else {}
            hotels = result_json.get('hotels', []) if result_json else []
            error = result_json.get('error') if result_json else None
            
            print("Requirements:")
            print(f"  City Code: {requirements.get('city_code', 'N/A')}")
            print(f"  City Name: {requirements.get('city_name', 'N/A')}")
            print(f"  Check In: {requirements.get('check_in', 'N/A')}")
            print(f"  Check Out: {requirements.get('check_out', 'N/A')}")
            print(f"  Adults: {requirements.get('adults', 'N/A')}")
            print()
            
            if error:
                print(f"❌ Error: {error}")
                print()
            
            if hotels:
                print(f"✅ Hotels found: {len(hotels)}")
                for i, hotel in enumerate(hotels[:5], 1):
                    print(f"  {i}. {hotel.get('name', 'N/A')}")
                    print(f"     Score: {hotel.get('score', 'N/A')}")
                    print(f"     Price: {hotel.get('total_price', 'N/A')} {hotel.get('currency', 'USD')}")
            else:
                print("⚠️ No hotels found")
                print()
            
            # Check if SOW analysis was used
            sow_requirements = result_json.get('sow_requirements')
            if sow_requirements:
                print("\n✅ SOW Requirements kullanıldı:")
                locations = sow_requirements.get('Locations', [])
                if locations:
                    print(f"  Locations: {len(locations)} şehir")
                else:
                    print(f"  Locations: None")
        else:
            print(f"✗ Sonuç alınamadı: {resp.status_code}")
    else:
        print("⚠️ Hiç Hotel Match analizi bulunamadı")
else:
    print(f"✗ API hatası: {resp.status_code}")

print()
print("=" * 60)

