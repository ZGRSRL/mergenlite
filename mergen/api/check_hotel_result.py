"""Check hotel match result"""
import requests
import json

API_BASE = "http://localhost:8000"
ANALYSIS_ID = 339

resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}")
result = resp.json()

result_json = result.get('result_json', {})
if isinstance(result_json, str):
    result_json = json.loads(result_json)

hotels = result_json.get('hotels', [])
print(f'Hotels count: {len(hotels)}')

if hotels:
    print(f'\nFirst hotel keys: {list(hotels[0].keys())}')
    print(f'First hotel name: {hotels[0].get("name")}')
    print(f'\nFirst hotel (full):')
    print(json.dumps(hotels[0], indent=2)[:1000])
    
    # Check if fallback was used
    if result_json.get('fallback_used'):
        print('\n⚠️ Fallback was used!')
    else:
        print('\n✅ Agent response was used')

