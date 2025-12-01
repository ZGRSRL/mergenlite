#!/usr/bin/env python3
"""Retry Analysis #302 after waiting for rate limit to reset."""
import sys
import os
from pathlib import Path
import time
import requests

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

mergen_api = project_root / "mergen" / "api"
sys.path.insert(0, str(mergen_api))

API_BASE = "http://localhost:8000"
OPP_DB_ID = 38  # FIFA World Cup opportunity

print("=" * 70)
print("RETRY ANALYSIS - Hotel Match (After Rate Limit Reset)")
print("=" * 70)
print()

# Wait 2 minutes for rate limit to reset
print("Waiting 2 minutes for rate limit to reset...")
for i in range(120, 0, -10):
    print(f"   {i} seconds remaining...", end='\r')
    time.sleep(10)
print("\n   Ready to retry!")
print()

# Start new hotel_match analysis
print("Starting new hotel_match analysis...")
try:
    pipeline_resp = requests.post(
        f"{API_BASE}/api/pipeline/run",
        json={
            "opportunity_id": OPP_DB_ID,
            "analysis_type": "hotel_match",
            "pipeline_version": "v1",
            "options": {
                "max_text_length": 120000,
                "llm_model": "gpt-4o-mini"  # Keep same model
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
        print(f"   Monitor progress in frontend or check logs:")
        print(f"      GET {API_BASE}/api/pipeline/results/{analysis_id}/logs")
    else:
        print(f"   [ERROR] Failed to start: {pipeline_resp.status_code}")
        print(f"      {pipeline_resp.text}")
        
except Exception as e:
    print(f"   [ERROR] Exception: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

