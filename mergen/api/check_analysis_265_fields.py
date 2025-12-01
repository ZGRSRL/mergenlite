#!/usr/bin/env python3
"""Check actual field names in analysis 265."""
import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("📊 ANALİZ 265 - FIELD İSİMLERİ KONTROLÜ")
print("=" * 70)
print()

# Get analysis 265
resp = requests.get(f"{API_BASE}/api/pipeline/results/265")
if resp.status_code == 200:
    data = resp.json()
    result_json = data.get('result_json', {})
    sow_analysis = result_json.get('sow_analysis', {})
    
    print("📄 SOW Analysis Fields:")
    print(f"   Keys: {list(sow_analysis.keys())[:20]}")
    print()
    
    # Function Space
    function_space = sow_analysis.get('FunctionSpaceRequirements', {})
    print("🏢 FunctionSpaceRequirements:")
    print(f"   Keys: {list(function_space.keys())}")
    print(f"   room_types: {function_space.get('room_types', [])}")
    print(f"   capacity_requirements: {function_space.get('capacity_requirements', [])}")
    print(f"   setup_requirements: {function_space.get('setup_requirements', [])}")
    print()
    
    # AV Requirements
    av_reqs = sow_analysis.get('AVRequirements', {})
    print("🎤 AVRequirements:")
    print(f"   Keys: {list(av_reqs.keys())}")
    print(f"   room_requirements: {av_reqs.get('room_requirements', [])}")
    print(f"   special_notes: {av_reqs.get('special_notes', [])}")
    print()
    
    # F&B Requirements
    fb_reqs = sow_analysis.get('FoodAndBeverageRequirements', {})
    print("🍽️ FoodAndBeverageRequirements:")
    print(f"   Keys: {list(fb_reqs.keys())}")
    print(f"   daily_breakdown: {fb_reqs.get('daily_breakdown', [])}")
    print()

print("=" * 70)

