#!/usr/bin/env python3
"""Check Hotel Match error."""
import requests
import json

API_BASE = "http://localhost:8000"
ANALYSIS_ID = 205

resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}")
result = resp.json()

print("=" * 60)
print("🔍 HOTEL MATCH HATA KONTROLÜ")
print("=" * 60)
print()

print(f"Status: {result.get('status')}")
print(f"Analysis Type: {result.get('analysis_type')}")
print()

result_json = result.get('result_json', {})
if isinstance(result_json, str):
    try:
        result_json = json.loads(result_json) if result_json else {}
    except:
        result_json = {}

error = result_json.get('error', 'N/A')
print(f"Error: {error}")
print()

requirements = result_json.get('requirements', {})
print(f"Requirements:")
print(f"  City Code: {requirements.get('city_code', 'N/A')}")
print(f"  City Name: {requirements.get('city_name', 'N/A')}")
print(f"  Check In: {requirements.get('check_in', 'N/A')}")
print(f"  Check Out: {requirements.get('check_out', 'N/A')}")
print()

# Check logs
print("Checking analysis logs...")
resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}/logs")
if resp.status_code == 200:
    logs = resp.json()
    error_logs = [log for log in logs if log.get('level') == 'ERROR']
    if error_logs:
        print(f"\nError Logs ({len(error_logs)}):")
        for log in error_logs[-5:]:  # Last 5 errors
            print(f"  - {log.get('message', 'N/A')}")

