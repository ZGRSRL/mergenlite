import requests
import json

def get_logs(analysis_id):
    url = f"http://localhost:8000/api/pipeline/results/{analysis_id}/logs?limit=50"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            logs = resp.json()
            print(f"Logs for Analysis {analysis_id}:")
            for log in logs:
                print(f"[{log.get('level')}] {log.get('message')}")
        else:
            print(f"Failed to get logs: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

def get_status(analysis_id):
    url = f"http://localhost:8000/api/pipeline/results/{analysis_id}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            print(f"Status for Analysis {analysis_id}:")
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Failed to get status: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

def get_latest_ids(limit=5):
    url = f"http://localhost:8000/api/pipeline/results/history?limit={limit}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            results = resp.json()
            return [r['id'] for r in results]
    except:
        pass
    return []

if __name__ == "__main__":
    ids = get_latest_ids()
    print(f"Checking IDs: {ids}")
    for i in ids:
        get_status(i)
        # get_logs(i) # Reduce noise
        print("-" * 50)
