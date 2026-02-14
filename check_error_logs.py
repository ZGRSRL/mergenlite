import requests
import json

def get_logs(analysis_id):
    url = f"http://localhost:8000/api/pipeline/results/{analysis_id}/logs?limit=50"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            logs = resp.json()
            print(f"\n--- Logs for Analysis {analysis_id} ---")
            for log in logs:
                msg = log.get('message', '')
                lvl = log.get('level', 'INFO')
                if 'error' in msg.lower() or 'warn' in msg.lower() or 'fail' in msg.lower() or lvl == 'ERROR':
                    print(f"[{lvl}] {msg}")
        else:
            print(f"Failed to get logs: {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_logs(7)
