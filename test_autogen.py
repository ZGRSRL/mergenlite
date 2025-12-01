import requests
import time

# Start analysis for opportunity 275
body = {
    "opportunity_id": 275,
    "analysis_type": "sow_draft",
    "pipeline_version": "v1"
}

response = requests.post("http://localhost:8001/api/pipeline/run", json=body)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    result = response.json()
    analysis_id = result.get('analysis_result_id')
    print(f"\n✅ Analysis started: ID {analysis_id}")
    
    # Monitor for 2 minutes
    print("\nMonitoring analysis...")
    for i in range(12):  # 12 * 10s = 2 minutes
        time.sleep(10)
        status_response = requests.get(f"http://localhost:8001/api/pipeline/results/{analysis_id}")
        status = status_response.json().get('status')
        print(f"[{i+1}] Status: {status}")
        
        if status in ['completed', 'failed']:
            # Get logs
            logs_response = requests.get(f"http://localhost:8001/api/pipeline/results/{analysis_id}/logs?limit=50")
            logs = logs_response.json()
            
            print(f"\n=== Final Status: {status} ===")
            print(f"Total logs: {len(logs)}")
            
            # Check for SOW analysis logs
            sow_logs = [log for log in logs if 'sow' in log.get('message', '').lower() or 'autogen' in log.get('message', '').lower()]
            print(f"\nSOW/AutoGen logs: {len(sow_logs)}")
            for log in sow_logs:
                print(f"[{log.get('level')}] {log.get('message')[:150]}")
            
            # Check result JSON
            result_json = status_response.json().get('result_json', {})
            sow_analysis = result_json.get('sow_analysis')
            if sow_analysis:
                print(f"\n✅ SOW Analysis PRESENT! Keys: {list(sow_analysis.keys())[:10]}")
            else:
                print(f"\n❌ SOW Analysis MISSING")
            
            break
