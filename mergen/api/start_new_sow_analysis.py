#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Start new SOW analysis and monitor progress."""
import requests
import time
import json
import sys
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

API_BASE = "http://localhost:8000"
OPP_ID = 6  # Houston opportunity

print("=" * 70)
print("YENI SOW ANALIZI BASLATILIYOR")
print("=" * 70)
print()

# Start SOW Analysis
print("SOW Analysis baslatiliyor...")
resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": OPP_ID,
        "analysis_type": "sow_draft"
    }
)

if resp.status_code == 200:
    result = resp.json()
    analysis_id = result.get("analysis_result_id")
    print(f"[OK] SOW Analysis ID: {analysis_id}")
    print()
    
    # Wait for completion
    print("Analiz tamamlanmasi bekleniyor...")
    print("   (Bu islem 2-5 dakika surebilir)")
    print()
    
    max_wait = 300  # 5 minutes
    for i in range(max_wait):
        time.sleep(2)
        resp2 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
        if resp2.status_code == 200:
            result2 = resp2.json()
            status = result2.get('status')
            
            # Show progress every 10 seconds
            if i % 5 == 0:
                print(f"   Status: {status} ({i*2}s)")
            
            if status in ['completed', 'failed']:
                print(f"\n[OK] SOW Analysis {status}!")
                break
    
    # Check results
    print("\n" + "=" * 70)
    print("SOW ANALYSIS SONUCLARI")
    print("=" * 70)
    resp3 = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
    if resp3.status_code == 200:
        result3 = resp3.json()
        status = result3.get('status')
        print(f"Status: {status}")
        
        # Check if hotel match exists
        result_json = result3.get('result_json', {})
        if isinstance(result_json, str):
            result_json = json.loads(result_json)
        
        hotels = result_json.get('hotels', [])
        if hotels:
            print(f"\n[OK] Hotel Match Data Found: {len(hotels)} hotels")
            print("\nFirst 3 hotels:")
            for i, hotel in enumerate(hotels[:3], 1):
                name = hotel.get('name', 'N/A')
                print(f"  {i}. {name}")
        else:
            print("\n[INFO] No hotel match data in SOW result")
            print("   (Hotel match will be in separate PDF attachment)")
        
        # Check PDF and JSON paths
        pdf_path = result3.get('pdf_path')
        json_path = result3.get('json_path')
        print(f"\nPDF Path: {pdf_path if pdf_path else 'N/A'}")
        print(f"JSON Path: {json_path if json_path else 'N/A'}")
        
        # Check email status
        print("\nEmail Status:")
        logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}/logs?limit=50")
        if logs_resp.status_code == 200:
            logs = logs_resp.json()
            email_logs = [l for l in logs if 'email' in l.get('message', '').lower()]
            if email_logs:
                for log in email_logs[-3:]:
                    print(f"   {log.get('message')[:100]}")
            else:
                print("   No email logs found yet")
    
    print("\n" + "=" * 70)
    print("[OK] Analiz tamamlandi!")
    print("=" * 70)
else:
    print(f"[ERROR] Failed to start analysis: {resp.status_code}")
    print(f"   Response: {resp.text}")
    sys.exit(1)

