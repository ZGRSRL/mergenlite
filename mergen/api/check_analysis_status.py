"""Check analysis status and wait for completion"""
import requests
import time
import json

API_BASE = "http://localhost:8000"
ANALYSIS_ID = 321  # Son başlatılan analiz

print("=" * 70)
print(f"Checking analysis status for ID: {ANALYSIS_ID}")
print("=" * 70)
print()

# Check current status
resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}")
if resp.status_code == 200:
    result = resp.json()
    status = result.get('status')
    print(f"Current Status: {status}")
    print(f"Analysis Type: {result.get('analysis_type')}")
    print(f"Opportunity ID: {result.get('opportunity_id')}")
    
    if status == 'completed':
        print("\n[OK] Analysis completed!")
        print(f"PDF Path: {result.get('pdf_path', 'N/A')}")
        print(f"JSON Path: {result.get('json_path', 'N/A')}")
        
        # Show result summary
        result_json = result.get('result_json')
        if result_json:
            if isinstance(result_json, str):
                result_json = json.loads(result_json)
            
            sow_analysis = result_json.get('sow_analysis')
            if sow_analysis:
                locations = sow_analysis.get('Locations', []) or sow_analysis.get('locations', [])
                print(f"\nSOW Analysis Results:")
                print(f"  Locations found: {len(locations)}")
                if locations:
                    for i, loc in enumerate(locations[:5], 1):
                        city = loc.get('city', 'N/A')
                        print(f"    {i}. {city}")
    elif status == 'running':
        print("\n[INFO] Analysis is still running...")
        print("Waiting for completion (max 5 minutes)...")
        print()
        
        max_wait = 300  # 5 minutes
        for i in range(max_wait):
            time.sleep(5)
            resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}")
            if resp.status_code == 200:
                result = resp.json()
                new_status = result.get('status')
                
                if i % 12 == 0:  # Every minute
                    print(f"  Status: {new_status} ({i//12} minutes elapsed)")
                
                if new_status in ['completed', 'failed']:
                    print(f"\n[OK] Analysis {new_status}!")
                    if new_status == 'completed':
                        print(f"PDF: {result.get('pdf_path', 'N/A')}")
                        print(f"JSON: {result.get('json_path', 'N/A')}")
                    break
        else:
            print("\n[WARNING] Timeout - analysis still running after 5 minutes")
    elif status == 'failed':
        print("\n[ERROR] Analysis failed!")
        result_json = result.get('result_json')
        if result_json:
            if isinstance(result_json, str):
                result_json = json.loads(result_json)
            error = result_json.get('error', 'Unknown error')
            print(f"Error: {error}")
    elif status == 'pending':
        print("\n[INFO] Analysis is pending (not started yet)")
    else:
        print(f"\n[INFO] Status: {status}")
    
    # Check logs
    print("\n" + "=" * 70)
    print("Recent Logs:")
    print("=" * 70)
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}/logs?limit=10")
    if resp.status_code == 200:
        logs = resp.json()
        for log in logs[-10:]:
            level = log.get('level', 'INFO')
            message = log.get('message', '')
            step = log.get('step', '')
            print(f"[{level}] {step}: {message[:80]}")
else:
    print(f"[ERROR] Failed to get analysis: {resp.status_code}")
    print(f"Response: {resp.text}")

