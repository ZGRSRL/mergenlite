"""Check latest hotel match result"""
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
            
            hotels = result_json.get('hotels', [])
            print(f"\nHotels: {len(hotels)}")
            if hotels:
                print(f"\nFirst hotel:")
                print(f"  Name: {hotels[0].get('name')}")
                print(f"  Keys: {list(hotels[0].keys())}")
                
                # Check logs for hotel name extraction
                print(f"\nChecking logs for hotel name extraction...")
                resp3 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}/logs?limit=100")
                if resp3.status_code == 200:
                    logs = resp3.json()
                    name_logs = [l for l in logs if 'Hotel Name Extraction' in l.get('message', '')]
                    if name_logs:
                        print(f"Found {len(name_logs)} hotel name extraction logs:")
                        for log in name_logs[-5:]:
                            print(f"  [{log.get('level')}] {log.get('message')[:150]}")
                    else:
                        print("No hotel name extraction logs found")

