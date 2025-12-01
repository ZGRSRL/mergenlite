"""Check agent's JSON response"""
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
        
        # Get result
        resp2 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
        if resp2.status_code == 200:
            result = resp2.json()
            result_json = result.get('result_json', {})
            if isinstance(result_json, str):
                result_json = json.loads(result_json)
            
            print(f"\nResult JSON keys: {list(result_json.keys())}")
            
            hotels = result_json.get('hotels', [])
            print(f"Hotels count: {len(hotels)}")
            
            if hotels:
                print(f"\nFirst hotel structure:")
                first_hotel = hotels[0]
                print(f"  Keys: {list(first_hotel.keys())[:15]}")
                print(f"  Name: {first_hotel.get('name')}")
                print(f"  Reasoning: {first_hotel.get('reasoning', '')[:100]}")
                
                # Check if it's from agent or fallback
                if 'agent fallback' in first_hotel.get('reasoning', '').lower():
                    print(f"\n⚠️ This is from FALLBACK path")
                else:
                    print(f"\n✅ This is from AGENT response")
                    
                    # Show full structure
                    print(f"\nFull first hotel JSON (first 1000 chars):")
                    print(json.dumps(first_hotel, indent=2, default=str)[:1000])

