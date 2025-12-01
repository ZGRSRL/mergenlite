"""Check hotel match error details"""
import requests
import json

API_BASE = "http://localhost:8000"
HOTEL_ANALYSIS_ID = 324

print("=" * 70)
print("HOTEL MATCH ERROR DETAILS")
print("=" * 70)

resp = requests.get(f"{API_BASE}/api/pipeline/results/{HOTEL_ANALYSIS_ID}")
if resp.status_code == 200:
    result = resp.json()
    print(f"Status: {result.get('status')}")
    
    result_json = result.get('result_json')
    if result_json:
        if isinstance(result_json, str):
            result_json = json.loads(result_json)
        
        error = result_json.get('error')
        if error:
            print(f"\nError: {error}")
    
    # Get logs
    print("\n" + "=" * 70)
    print("ERROR LOGS:")
    print("=" * 70)
    resp2 = requests.get(f"{API_BASE}/api/pipeline/results/{HOTEL_ANALYSIS_ID}/logs?limit=50")
    if resp2.status_code == 200:
        logs = resp2.json()
        error_logs = [log for log in logs if log.get('level') == 'ERROR']
        if error_logs:
            for log in error_logs:
                print(f"[ERROR] {log.get('step')}: {log.get('message')}")
        else:
            print("No error logs found")
            print("\nAll logs:")
            for log in logs[-10:]:
                print(f"[{log.get('level')}] {log.get('step')}: {log.get('message')[:100]}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("1. SOW Analysis (ID: 321): COMPLETED")
print("   - PDF and JSON generated")
print("   - Email: NOT SENT (SMTP settings may be missing)")
print()
print("2. Hotel Match Analysis (ID: 324): FAILED")
print("   - Check error details above")
print()
print("Note: For email to be sent, SMTP settings must be configured in .env:")
print("  - SMTP_HOST")
print("  - SMTP_USERNAME")
print("  - SMTP_PASSWORD")
print("  - PIPELINE_NOTIFICATION_EMAIL")

