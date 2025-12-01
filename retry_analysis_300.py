#!/usr/bin/env python3
"""Retry Analysis #300 - Hotel Match for FIFA World Cup opportunity."""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add mergen/api to path
mergen_api = project_root / "mergen" / "api"
sys.path.insert(0, str(mergen_api))

import requests
import time

API_BASE = "http://localhost:8000"
NOTICE_ID = "d0e8f443c3d84a0ba96d8b74e416698a"

print("=" * 70)
print("RETRY ANALYSIS #300 - Hotel Match")
print("=" * 70)
print()

# Step 1: Find opportunity by notice_id
print(f"Step 1: Finding opportunity with notice_id: {NOTICE_ID}")
try:
    resp = requests.get(f"{API_BASE}/api/opportunities", params={"notice_id": NOTICE_ID})
    if resp.status_code == 200:
        opportunities = resp.json()
        if opportunities and len(opportunities) > 0:
            opp = opportunities[0]
            opp_db_id = opp.get('id')
            opp_title = opp.get('title', 'N/A')
            print(f"   [OK] Opportunity found:")
            print(f"      Database ID: {opp_db_id}")
            print(f"      Title: {opp_title}")
            print()
            
            # Step 2: Start hotel_match analysis
            print(f"Step 2: Starting hotel_match analysis...")
            pipeline_resp = requests.post(
                f"{API_BASE}/api/pipeline/run",
                json={
                    "opportunity_id": opp_db_id,
                    "analysis_type": "hotel_match",
                    "pipeline_version": "v1",
                    "options": {
                        "max_text_length": 120000
                    }
                }
            )
            
            if pipeline_resp.status_code == 200:
                result = pipeline_resp.json()
                analysis_id = result.get("analysis_result_id")
                print(f"   [OK] Analysis started!")
                print(f"      Analysis ID: {analysis_id}")
                print(f"      Status: {result.get('status')}")
                print()
                
                # Step 3: Wait for completion
                print(f"Step 3: Waiting for analysis to complete...")
                print(f"   (This may take 2-5 minutes)")
                print()
                
                max_wait = 300  # 5 minutes
                for i in range(max_wait):
                    time.sleep(2)
                    status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        status = status_data.get('status')
                        
                        # Show progress every 10 seconds
                        if i % 5 == 0:
                            print(f"   Status: {status} ({i*2}s)", end='\r')
                        
                        if status == 'completed':
                            print(f"\n   [OK] Analysis completed!")
                            
                            # Check results
                            result_json = status_data.get('result_json', {})
                            if isinstance(result_json, str):
                                import json
                                result_json = json.loads(result_json)
                            
                            hotels = result_json.get('hotels', [])
                            print(f"\n   Results:")
                            print(f"      Hotels found: {len(hotels)}")
                            if hotels:
                                for idx, hotel in enumerate(hotels[:5], 1):
                                    print(f"      {idx}. {hotel.get('name', 'N/A')} - Score: {hotel.get('score', 'N/A')}")
                            
                            # Check if email was sent
                            print(f"\n   Email: Should be sent automatically (check logs)")
                            break
                        elif status == 'failed':
                            print(f"\n   [FAILED] Analysis failed!")
                            error_msg = status_data.get('error_message', 'Unknown error')
                            print(f"      Error: {error_msg}")
                            break
                else:
                    print(f"\n   [TIMEOUT] Analysis did not complete within {max_wait*2} seconds")
            else:
                print(f"   [ERROR] Failed to start analysis: {pipeline_resp.status_code}")
                print(f"      Response: {pipeline_resp.text}")
        else:
            print(f"   [ERROR] Opportunity not found with notice_id: {NOTICE_ID}")
            print(f"   Response: {resp.text}")
    else:
        print(f"   [ERROR] API request failed: {resp.status_code}")
        print(f"      Response: {resp.text}")
        
except Exception as e:
    print(f"   [ERROR] Exception: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

