#!/usr/bin/env python3
import json
import requests

result = requests.get('http://localhost:8000/api/pipeline/results/142').json()
print("=== Pipeline Result ===")
print(f"Status: {result['status']}")
print(f"PDF: {result.get('pdf_path')}")

json_content = result.get('result_json')
if isinstance(json_content, str):
    data = json.loads(json_content)
else:
    data = json_content

print(f"\n=== JSON Structure ===")
print(f"Keys: {list(data.keys()) if data else 'None'}")

sow_analysis = data.get('sow_analysis') if data else None
print(f"\nSOW Analysis Present: {bool(sow_analysis)}")
if sow_analysis:
    print(f"SOW Keys: {list(sow_analysis.keys())}")
    for key in ['EventDetails', 'SleepingRoomRequirements', 'FunctionSpaceRequirements', 'CommercialTerms']:
        if key in sow_analysis:
            val = sow_analysis[key]
            if val:
                print(f"  {key}: ✓ Dolu ({type(val).__name__})")
            else:
                print(f"  {key}: ✗ Bos")
        else:
            print(f"  {key}: ✗ Yok")

# Check hotels
hotels = data.get('hotels', []) if data else []
print(f"\nHotels: {len(hotels)} found")

