#!/usr/bin/env python3
"""
Tam Analiz Pipeline - Rate Limit Bekleme ile
SOW Analizi -> Otel Eşleştirme -> Mail Gönderimi
"""
import sys
import requests
import time
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
mergen_api = project_root / "mergen" / "api"
sys.path.insert(0, str(mergen_api))

API_BASE = "http://localhost:8000"
NOTICE_ID = "d0e8f443c3d84a0ba96d8b74e416698a"  # FIFA World Cup

print("=" * 70)
print("TAM ANALIZ PIPELINE - Rate Limit Bekleme ile")
print("=" * 70)
print()

# Wait 3 minutes for rate limit to reset
print("Waiting 3 minutes for rate limit to reset...")
for i in range(180, 0, -10):
    print(f"   {i} seconds remaining...", end='\r')
    time.sleep(10)
print("\n   Ready to start!")
print()

# Find opportunity
print(f"Finding opportunity: {NOTICE_ID}")
resp = requests.get(f"{API_BASE}/api/opportunities", params={"notice_id": NOTICE_ID})
if resp.status_code == 200:
    opportunities = resp.json()
    if opportunities and len(opportunities) > 0:
        opp = opportunities[0]
        opp_db_id = opp.get('id')
        opp_title = opp.get('title', 'N/A')
        print(f"   [OK] Opportunity found: {opp_title}")
        print(f"      Database ID: {opp_db_id}")
        print()
    else:
        print(f"   [ERROR] Opportunity not found")
        sys.exit(1)
else:
    print(f"   [ERROR] API request failed")
    sys.exit(1)

# Step 1: SOW Analysis
print("=" * 70)
print("STEP 1: SOW ANALIZI")
print("=" * 70)
print()

sow_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": opp_db_id,
        "analysis_type": "sow_draft",
        "pipeline_version": "v1",
        "options": {"max_text_length": 120000}
    }
)

if sow_resp.status_code != 200:
    print(f"   [ERROR] Failed to start: {sow_resp.status_code}")
    sys.exit(1)

sow_result = sow_resp.json()
sow_analysis_id = sow_result.get("analysis_result_id")
print(f"   [OK] Started! Analysis ID: {sow_analysis_id}")
print()

print("Waiting for completion (max 5 minutes)...")
max_wait = 300
for i in range(max_wait):
    time.sleep(2)
    status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
    if status_resp.status_code == 200:
        status_data = status_resp.json()
        status = status_data.get('status')
        if i % 5 == 0:
            print(f"   Status: {status} ({i*2}s)", end='\r')
        if status == 'completed':
            print(f"\n   [OK] SOW Analysis completed!")
            result_json = status_data.get('result_json', {})
            if isinstance(result_json, str):
                result_json = json.loads(result_json) if result_json else {}
            sow_analysis = result_json.get('sow_analysis', {})
            if sow_analysis and 'error' not in sow_analysis:
                print(f"      SOW analysis: OK")
            else:
                print(f"      [WARNING] SOW analysis failed or empty")
            break
        elif status == 'failed':
            print(f"\n   [FAILED] SOW Analysis failed!")
            break
else:
    print(f"\n   [TIMEOUT] Did not complete in time")

print()
print("=" * 70)
print("STEP 2: HOTEL MATCH")
print("=" * 70)
print()

hotel_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": opp_db_id,
        "analysis_type": "hotel_match",
        "pipeline_version": "v1"
    }
)

if hotel_resp.status_code != 200:
    print(f"   [ERROR] Failed to start: {hotel_resp.status_code}")
    sys.exit(1)

hotel_result = hotel_resp.json()
hotel_analysis_id = hotel_result.get("analysis_result_id")
print(f"   [OK] Started! Analysis ID: {hotel_analysis_id}")
print()

print("Waiting for completion (max 5 minutes)...")
for i in range(max_wait):
    time.sleep(2)
    status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
    if status_resp.status_code == 200:
        status_data = status_resp.json()
        status = status_data.get('status')
        if i % 5 == 0:
            print(f"   Status: {status} ({i*2}s)", end='\r')
        if status == 'completed':
            print(f"\n   [OK] Hotel Match completed!")
            result_json = status_data.get('result_json', {})
            if isinstance(result_json, str):
                result_json = json.loads(result_json) if result_json else {}
            hotels = result_json.get('hotels', [])
            print(f"      Hotels found: {len(hotels)}")
            break
        elif status == 'failed':
            print(f"\n   [FAILED] Hotel Match failed!")
            break
else:
    print(f"\n   [TIMEOUT] Did not complete in time")

print()
print("=" * 70)
print("STEP 3: EMAIL")
print("=" * 70)
print()
print("   [INFO] Email should be sent automatically after hotel_match completes")
print("   [INFO] Check SMTP logs and frontend for email status")
print()

print("=" * 70)
print("PIPELINE COMPLETED")
print("=" * 70)
print(f"SOW Analysis ID: {sow_analysis_id}")
print(f"Hotel Match ID: {hotel_analysis_id}")
print()

