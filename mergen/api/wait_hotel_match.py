"""Wait for hotel match to complete"""
import requests
import time

API_BASE = "http://localhost:8000"
HOTEL_ANALYSIS_ID = 324

print("Waiting for hotel match analysis to complete...")
print("(This may take 2-5 minutes)")
print()

max_wait = 300  # 5 minutes
for i in range(max_wait):
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{HOTEL_ANALYSIS_ID}")
    if resp.status_code == 200:
        result = resp.json()
        status = result.get('status')
        
        if i % 12 == 0:  # Every minute
            print(f"  Status: {status} ({i//12} minutes elapsed)")
        
        if status in ['completed', 'failed']:
            print(f"\n[OK] Hotel match analysis {status}!")
            print(f"PDF: {result.get('pdf_path', 'N/A')}")
            print(f"JSON: {result.get('json_path', 'N/A')}")
            
            # Check for email logs
            print("\nChecking email logs...")
            resp2 = requests.get(f"{API_BASE}/api/pipeline/results/{HOTEL_ANALYSIS_ID}/logs?limit=50")
            if resp2.status_code == 200:
                logs = resp2.json()
                email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or log.get('step') == 'email']
                if email_logs:
                    print("Email logs found:")
                    for log in email_logs:
                        print(f"  [{log.get('level')}] {log.get('message')}")
                else:
                    print("  No email logs found (SMTP may not be configured)")
            break
    
    time.sleep(5)
else:
    print("\n[WARNING] Timeout - hotel match still running after 5 minutes")

