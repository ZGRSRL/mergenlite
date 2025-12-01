import requests
import json

def check_email_logs():
    try:
        # Get all logs
        response = requests.get("http://localhost:8001/api/pipeline/results/5/logs?limit=50")
        logs = response.json()
        
        print(f"Total logs: {len(logs)}")
        print("\n--- Checking for email-related logs ---")
        
        email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or log.get('step') == 'email']
        
        if email_logs:
            print(f"\n✅ Found {len(email_logs)} email-related log entries:")
            for log in email_logs:
                print(f"\n[{log.get('level')}] Step: {log.get('step')}")
                print(f"Message: {log.get('message')}")
                print(f"Time: {log.get('timestamp')}")
        else:
            print("\n⚠️  No email-related logs found")
            print("\nAll logs:")
            for log in logs:
                print(f"[{log.get('level')}] ({log.get('step')}): {log.get('message')[:150]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_email_logs()
