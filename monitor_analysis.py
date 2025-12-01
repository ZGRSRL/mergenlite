import requests
import json
import time

def check_analysis():
    try:
        # Check analysis status
        response = requests.get("http://localhost:8001/api/pipeline/results/5")
        result = response.json()
        print(f"Status: {result.get('status')}")
        print(f"Analysis Type: {result.get('analysis_type')}")
        print(f"Created: {result.get('created_at')}")
        print(f"Completed: {result.get('completed_at')}")
        
        # Check logs
        log_response = requests.get("http://localhost:8001/api/pipeline/results/5/logs?limit=10")
        logs = log_response.json()
        print(f"\n--- Recent Logs ({len(logs)} entries) ---")
        for log in logs[-5:]:  # Last 5 logs
            print(f"[{log.get('level')}] ({log.get('step')}): {log.get('message')[:100]}")
        
        return result.get('status')
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    for i in range(10):  # Check 10 times
        print(f"\n=== Check {i+1} ===")
        status = check_analysis()
        if status in ['completed', 'failed']:
            print(f"\n✅ Analysis {status}!")
            break
        print("Waiting 10 seconds...")
        time.sleep(10)
