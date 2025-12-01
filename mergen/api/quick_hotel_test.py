"""Quick hotel match test"""
import requests
import json
import time

API_BASE = "http://localhost:8000"
OPP_ID = 6

print("Starting quick hotel match test...")

# Start hotel match
resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": OPP_ID,
        "analysis_type": "hotel_match",
        "options": {
            "city_code": "HOU",
            "check_in": "2026-03-03",
            "check_out": "2026-03-07",
            "adults": 2,
            "force_refresh": True  # Bypass cache to test actual function
        }
    }
)

if resp.status_code == 200:
    result = resp.json()
    analysis_id = result.get("analysis_result_id")
    print(f"Analysis ID: {analysis_id}")
    
    # Wait for completion
    for i in range(30):
        time.sleep(2)
        resp2 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
        if resp2.status_code == 200:
            result2 = resp2.json()
            status = result2.get('status')
            if status in ['completed', 'failed']:
                print(f"Status: {status}")
                
                # Check result
                result_json = result2.get('result_json', {})
                if isinstance(result_json, str):
                    result_json = json.loads(result_json)
                
                hotels = result_json.get('hotels', [])
                print(f"Hotels: {len(hotels)}")
                if hotels:
                    print(f"First hotel name: {hotels[0].get('name')}")
                
                # Check logs
                resp3 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}/logs?limit=100")
                if resp3.status_code == 200:
                    logs = resp3.json()
                    name_logs = [l for l in logs if 'Hotel Name' in l.get('message', '')]
                    print(f"\nHotel name extraction logs: {len(name_logs)}")
                    for log in name_logs[-5:]:
                        print(f"  {log.get('message')[:200]}")
                
                break
else:
    print(f"Failed to start: {resp.status_code}")

