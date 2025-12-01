"""Test SOW analysis with hotel match"""
import requests
import json
import time

API_BASE = "http://localhost:8000"
OPP_ID = 6

print("="*70)
print("TEST: SOW Analysis with Hotel Match")
print("="*70)

# 1. First, ensure we have a completed hotel match
print("\n1. Checking for existing hotel match...")
resp = requests.get(f"{API_BASE}/api/pipeline/results?opportunity_id={OPP_ID}&analysis_type=hotel_match&limit=1")
if resp.status_code == 200:
    hotel_matches = resp.json()
    if hotel_matches and hotel_matches[0].get('status') == 'completed':
        print(f"   ✅ Found completed hotel match: ID {hotel_matches[0].get('id')}")
    else:
        print("   ⚠️  No completed hotel match found. Starting one...")
        resp2 = requests.post(
            f"{API_BASE}/api/pipeline/run",
            json={
                "opportunity_id": OPP_ID,
                "analysis_type": "hotel_match",
                "options": {
                    "city_code": "HOU",
                    "check_in": "2026-03-03",
                    "check_out": "2026-03-07",
                    "adults": 2,
                    "force_refresh": True
                }
            }
        )
        if resp2.status_code == 200:
            hotel_id = resp2.json().get("analysis_result_id")
            print(f"   Started hotel match: ID {hotel_id}")
            # Wait for completion
            for i in range(30):
                time.sleep(2)
                resp3 = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_id}")
                if resp3.status_code == 200:
                    data = resp3.json()
                    if data.get('status') in ['completed', 'failed']:
                        print(f"   Hotel match {data.get('status')}")
                        break

# 2. Now start SOW analysis
print("\n2. Starting SOW analysis...")
resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": OPP_ID,
        "analysis_type": "sow_draft",
        "options": {
            "force_refresh": False
        }
    }
)

if resp.status_code == 200:
    result = resp.json()
    sow_id = result.get("analysis_result_id")
    print(f"   ✅ SOW Analysis ID: {sow_id}")
    
    # Wait for completion
    print("\n3. Waiting for SOW analysis to complete...")
    for i in range(60):
        time.sleep(2)
        resp2 = requests.get(f"{API_BASE}/api/pipeline/results/{sow_id}")
        if resp2.status_code == 200:
            data = resp2.json()
            status = data.get('status')
            if status == 'completed':
                print(f"   ✅ SOW Analysis completed!")
                
                # Check logs for email
                print("\n4. Checking email logs...")
                resp3 = requests.get(f"{API_BASE}/api/pipeline/results/{sow_id}/logs?limit=100")
                if resp3.status_code == 200:
                    logs = resp3.json()
                    email_logs = [l for l in logs if 'email' in l.get('message', '').lower() or 'hotel' in l.get('message', '').lower()]
                    for log in email_logs[-10:]:
                        print(f"   {log.get('level')}: {log.get('message')}")
                
                break
            elif status == 'failed':
                print(f"   ❌ SOW Analysis failed!")
                break
            else:
                print(f"   Status: {status}...")
else:
    print(f"   ❌ Failed to start SOW analysis: {resp.status_code}")

print("\n" + "="*70)
print("Test completed!")
print("="*70)

