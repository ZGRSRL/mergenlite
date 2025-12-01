#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check hotel names in analysis result."""
import requests
import json

API_BASE = "http://localhost:8000"
ANALYSIS_ID = 412

resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}")
if resp.status_code == 200:
    r = resp.json()
    result_json = r.get('result_json', {})
    if isinstance(result_json, str):
        result_json = json.loads(result_json)
    
    hotels = result_json.get('hotels', [])
    print(f"Total hotels: {len(hotels)}")
    print("\nAll hotel names:")
    for i, hotel in enumerate(hotels, 1):
        name = hotel.get('name', 'N/A')
        print(f"  {i}. {name}")
        
        # Check if name contains "Unknown" or "N/A"
        if "Unknown" in name or name == "N/A":
            print(f"     ⚠️  WARNING: Invalid name!")
else:
    print(f"Failed to get results: {resp.status_code}")

