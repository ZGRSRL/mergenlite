import requests
import time

# Start analysis for opportunity 277 (no documents)
body = {
    "opportunity_id": 277,
    "analysis_type": "sow_draft",
    "pipeline_version": "v1"
}

print("=== Starting Analysis for Opportunity 277 (No Documents) ===")
response = requests.post("http://localhost:8001/api/pipeline/run", json=body)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    result = response.json()
    analysis_id = result.get('analysis_result_id')
    print(f"\n✅ Analysis started: ID {analysis_id}")
    
    # Wait for completion
    print("\nWaiting for completion...")
    for i in range(20):  # 20 * 5s = 100 seconds max
        time.sleep(5)
        status_response = requests.get(f"http://localhost:8001/api/pipeline/results/{analysis_id}")
        status = status_response.json().get('status')
        print(f"[{(i+1)*5}s] Status: {status}")
        
        if status in ['completed', 'failed']:
            print(f"\n=== Analysis {status.upper()} ===")
            
            # Get all logs
            logs_response = requests.get(f"http://localhost:8001/api/pipeline/results/{analysis_id}/logs?limit=100")
            logs = logs_response.json()
            
            print(f"\n=== Logs ({len(logs)}) ===")
            for log in logs:
                print(f"[{log.get('level')}] ({log.get('step')}): {log.get('message')}")
            
            # Check for document warning
            doc_warnings = [log for log in logs if 'DOKÜMAN' in log.get('message', '').upper() or 'attachment' in log.get('message', '').lower()]
            if doc_warnings:
                print(f"\n✅ Document Warning Found!")
                for warning in doc_warnings:
                    print(f"\n{warning.get('message')}")
            
            # Check for email logs
            email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or log.get('step') == 'email']
            if email_logs:
                print(f"\n📧 Email Logs:")
                for email_log in email_logs:
                    print(f"  [{email_log.get('level')}] {email_log.get('message')}")
            
            break
