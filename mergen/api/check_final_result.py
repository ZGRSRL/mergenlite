"""Check final hotel match result"""
import requests
import json

API_BASE = "http://localhost:8000"

# Get latest hotel match
resp = requests.get(f"{API_BASE}/api/pipeline/results?analysis_type=hotel_match&limit=1")
if resp.status_code == 200:
    results = resp.json()
    if results:
        analysis_id = results[0]['id']
        print(f"Latest hotel match ID: {analysis_id}")
        print("=" * 70)
        
        # Get result
        resp2 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
        if resp2.status_code == 200:
            result = resp2.json()
            result_json = result.get('result_json', {})
            if isinstance(result_json, str):
                result_json = json.loads(result_json)
            
            hotels = result_json.get('hotels', [])
            print(f"\n📊 RESULT SUMMARY:")
            print(f"  Total hotels: {len(hotels)}")
            
            if hotels:
                print(f"\n🏨 FIRST 5 HOTELS:")
                unknown_count = 0
                for i, hotel in enumerate(hotels[:5], 1):
                    name = hotel.get('name', 'N/A')
                    if name == 'Unknown Hotel':
                        unknown_count += 1
                    print(f"  {i}. {name}")
                    print(f"     Price: ${hotel.get('price_per_night', 0)}/night")
                    print(f"     Score: {hotel.get('score', 0)}")
                
                print(f"\n✅ STATUS:")
                if unknown_count == 0:
                    print(f"  ✅ SUCCESS - All hotel names are correct!")
                elif unknown_count < len(hotels):
                    print(f"  ⚠️ PARTIAL - {unknown_count}/{len(hotels)} hotels have 'Unknown Hotel'")
                else:
                    print(f"  ❌ FAILED - All hotels have 'Unknown Hotel'")
            else:
                print("  ❌ No hotels found")

