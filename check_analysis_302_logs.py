#!/usr/bin/env python3
"""Check Analysis #302 logs and error details."""
import sys
import requests

API_BASE = "http://localhost:8000"
ANALYSIS_ID = 302

print("=" * 70)
print(f"CHECKING ANALYSIS #{ANALYSIS_ID} LOGS")
print("=" * 70)
print()

try:
    # Get analysis result
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}")
    if resp.status_code == 200:
        result = resp.json()
        print(f"Status: {result.get('status')}")
        print(f"Analysis Type: {result.get('analysis_type')}")
        print(f"Created: {result.get('created_at')}")
        print(f"Completed: {result.get('completed_at')}")
        print()
        
        # Get logs
        logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}/logs")
        if logs_resp.status_code == 200:
            logs = logs_resp.json()
            print(f"Total Logs: {len(logs)}")
            print()
            print("Recent Logs (last 20):")
            print("-" * 70)
            for log in logs[-20:]:
                level = log.get('level', 'INFO')
                message = log.get('message', '')
                step = log.get('step', '')
                timestamp = log.get('created_at', '')
                print(f"[{level}] {step}: {message[:200]}")
                if timestamp:
                    print(f"  Time: {timestamp}")
                print()
        else:
            print(f"Failed to get logs: {logs_resp.status_code}")
            print(logs_resp.text)
    else:
        print(f"Failed to get analysis: {resp.status_code}")
        print(resp.text)
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

