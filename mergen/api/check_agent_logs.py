"""Check agent response logs in detail"""
import requests
import json

API_BASE = "http://localhost:8000"

# Get latest hotel match
resp = requests.get(f"{API_BASE}/api/pipeline/results?analysis_type=hotel_match&limit=1")
if resp.status_code == 200:
    results = resp.json()
    if results:
        analysis_id = results[0]['id']
        print(f"Latest hotel match ID: {analysis_id}")
        print("=" * 70)
        
        # Get all logs
        resp2 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}/logs?limit=200")
        if resp2.status_code == 200:
            logs = resp2.json()
            
            # Filter relevant logs
            agent_response_logs = [l for l in logs if 'Agent Response' in l.get('message', '')]
            json_extraction_logs = [l for l in logs if 'JSON Extraction' in l.get('message', '')]
            hotel_name_logs = [l for l in logs if 'Hotel Name' in l.get('message', '')]
            normalization_logs = [l for l in logs if 'Normalized' in l.get('message', '') or 'normalize' in l.get('message', '').lower()]
            
            print(f"\n📊 LOG SUMMARY:")
            print(f"  Total logs: {len(logs)}")
            print(f"  Agent Response logs: {len(agent_response_logs)}")
            print(f"  JSON Extraction logs: {len(json_extraction_logs)}")
            print(f"  Hotel Name logs: {len(hotel_name_logs)}")
            print(f"  Normalization logs: {len(normalization_logs)}")
            
            print(f"\n📝 AGENT RESPONSE LOGS:")
            for log in agent_response_logs:
                print(f"  [{log.get('level')}] {log.get('message')}")
            
            print(f"\n🔍 JSON EXTRACTION LOGS:")
            for log in json_extraction_logs:
                print(f"  [{log.get('level')}] {log.get('message')}")
            
            print(f"\n🏨 HOTEL NAME LOGS:")
            for log in hotel_name_logs:
                print(f"  [{log.get('level')}] {log.get('message')[:200]}")
            
            print(f"\n🔄 NORMALIZATION LOGS:")
            for log in normalization_logs:
                print(f"  [{log.get('level')}] {log.get('message')[:200]}")
            
            # Get result to see final hotels
            print(f"\n📋 FINAL RESULT:")
            resp3 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
            if resp3.status_code == 200:
                result = resp3.json()
                result_json = result.get('result_json', {})
                if isinstance(result_json, str):
                    result_json = json.loads(result_json)
                
                hotels = result_json.get('hotels', [])
                print(f"  Hotels count: {len(hotels)}")
                if hotels:
                    print(f"\n  First 3 hotels:")
                    for i, hotel in enumerate(hotels[:3], 1):
                        name = hotel.get('name', 'N/A')
                        print(f"    {i}. Name: {name}")
                        print(f"       Keys: {list(hotel.keys())[:10]}")

