"""Check _convert logs"""
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
        
        # Get all logs
        resp2 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}/logs?limit=200")
        if resp2.status_code == 200:
            logs = resp2.json()
            
            # Filter _convert logs
            convert_logs = [l for l in logs if '_convert' in l.get('message', '')]
            
            print(f"\n📊 _convert LOGS: {len(convert_logs)}")
            for log in convert_logs:
                print(f"  [{log.get('level')}] {log.get('message')[:300]}")

