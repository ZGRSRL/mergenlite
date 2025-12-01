"""Check opportunities and start analysis"""
import requests
import sys

API_BASE = "http://localhost:8000"

# Get opportunities
print("Checking available opportunities...")
resp = requests.get(f"{API_BASE}/api/opportunities?page_size=5")
if resp.status_code == 200:
    opps = resp.json()
    print(f"Found {len(opps)} opportunities:\n")
    for i, opp in enumerate(opps[:5], 1):
        print(f"{i}. ID: {opp['id']}, Title: {opp.get('title', 'N/A')[:60]}")
    
    if opps:
        # Use first opportunity
        opp_id = opps[0]['id']
        print(f"\nStarting SOW analysis for opportunity {opp_id}...")
        
        # Start analysis
        resp = requests.post(
            f"{API_BASE}/api/pipeline/run",
            json={
                "opportunity_id": opp_id,
                "analysis_type": "sow_draft"
            }
        )
        
        if resp.status_code == 200:
            result = resp.json()
            analysis_id = result.get("analysis_result_id")
            print(f"[OK] Analysis started successfully!")
            print(f"   Analysis ID: {analysis_id}")
            print(f"   Status: {result.get('status')}")
            print(f"\nYou can check status at: {API_BASE}/api/pipeline/results/{analysis_id}")
        else:
            print(f"[ERROR] Failed to start analysis: {resp.status_code}")
            print(f"   Response: {resp.text}")
    else:
        print("\nNo opportunities found")
else:
    print(f"Failed to get opportunities: {resp.status_code}")
    print(f"Response: {resp.text}")

