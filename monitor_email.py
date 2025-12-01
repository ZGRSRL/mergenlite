import requests
import json
import time

def monitor_analysis_with_email():
    analysis_id = 6
    
    for i in range(15):  # Check for up to 2.5 minutes
        print(f"\n=== Check {i+1} ===")
        try:
            # Check analysis status
            response = requests.get(f"http://localhost:8001/api/pipeline/results/{analysis_id}")
            result = response.json()
            status = result.get('status')
            print(f"Status: {status}")
            
            # Get logs
            log_response = requests.get(f"http://localhost:8001/api/pipeline/results/{analysis_id}/logs?limit=100")
            logs = log_response.json()
            
            # Check for email logs
            email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or log.get('step') == 'email']
            
            if email_logs:
                print(f"\n📧 Email Logs Found:")
                for log in email_logs:
                    print(f"  [{log.get('level')}] {log.get('message')}")
            
            if status in ['completed', 'failed']:
                print(f"\n✅ Analysis {status}!")
                
                if email_logs:
                    print("\n--- Final Email Status ---")
                    for log in email_logs:
                        print(f"[{log.get('level')}] ({log.get('step')}): {log.get('message')}")
                else:
                    print("\n⚠️  No email logs found - email might not have been sent")
                
                break
        except Exception as e:
            print(f"Error: {e}")
        
        print("Waiting 10 seconds...")
        time.sleep(10)
    else:
        print("\n⏱️ Timeout - analysis still running")

if __name__ == "__main__":
    monitor_analysis_with_email()
