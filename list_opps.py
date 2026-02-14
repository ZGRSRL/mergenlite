import requests
try:
    resp = requests.get('http://localhost:8000/api/opportunities?limit=20')
    if resp.status_code == 200:
        ops = resp.json()
        print(f"Total: {len(ops)}")
        for o in ops:
            print(f"DB_ID: {o.get('id')} | NoticeID: {o.get('notice_id')} | OppID: {o.get('opportunity_id')} | Title: {o.get('title')[:30]}")
    else:
        print(f"Error: {resp.status_code} {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
