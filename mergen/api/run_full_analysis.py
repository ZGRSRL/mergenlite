#!/usr/bin/env python3
"""Run full analysis for opportunity 3."""
import requests
import time
import json

API_BASE = "http://localhost:8000"
OPP_ID = 3

print("=" * 60)
print("🚀 FULL ANALYSIS BAŞLATILIYOR - OPPORTUNITY 3")
print("=" * 60)
print()

# Step 1: SOW Analysis
print("📄 Step 1: SOW Analysis başlatılıyor...")
resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={"opportunity_id": OPP_ID, "analysis_type": "sow"}
)
if resp.status_code == 200:
    result = resp.json()
    sow_analysis_id = result.get("analysis_result_id")
    print(f"✓ SOW Analysis ID: {sow_analysis_id}")
    
    # Wait for completion
    print("⏳ SOW Analysis tamamlanması bekleniyor...")
    for i in range(60):
        time.sleep(2)
        resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
        if resp.status_code == 200:
            result = resp.json()
            status = result.get('status')
            print(f"  Status: {status} ({i*2}s)")
            if status in ['completed', 'failed']:
                break
    
    # Check SOW results
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
    if resp.status_code == 200:
        result = resp.json()
        result_json = result.get('result_json', {})
        if isinstance(result_json, str):
            result_json = json.loads(result_json)
        
        docs = result_json.get('analyzed_documents', [])
        total_chars = sum(doc.get('text_length', 0) for doc in docs)
        print(f"\n✓ SOW Analysis tamamlandı!")
        print(f"  Toplam doküman: {len(docs)}")
        print(f"  Toplam karakter: {total_chars}")
        for i, doc in enumerate(docs, 1):
            print(f"    Doc {i}: {doc.get('attachment_name', 'N/A')} - {doc.get('text_length', 0)} chars")
else:
    print(f"✗ SOW Analysis başlatılamadı: {resp.status_code} - {resp.text}")
    sow_analysis_id = None

print()

# Step 2: Hotel Match
if sow_analysis_id:
    print("🏨 Step 2: Hotel Match başlatılıyor...")
    resp = requests.post(
        f"{API_BASE}/api/pipeline/run",
        json={"opportunity_id": OPP_ID, "analysis_type": "hotel_match"}
    )
    if resp.status_code == 200:
        result = resp.json()
        hotel_analysis_id = result.get("analysis_result_id")
        print(f"✓ Hotel Match ID: {hotel_analysis_id}")
        
        # Wait for completion
        print("⏳ Hotel Match tamamlanması bekleniyor...")
        for i in range(60):
            time.sleep(2)
            resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
            if resp.status_code == 200:
                result = resp.json()
                status = result.get('status')
                print(f"  Status: {status} ({i*2}s)")
                if status in ['completed', 'failed']:
                    break
        
        # Check Hotel Match results
        resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
        if resp.status_code == 200:
            result = resp.json()
            result_json = result.get('result_json', {})
            if isinstance(result_json, str):
                result_json = json.loads(result_json) if result_json else {}
            
            hotels = result_json.get('hotels', []) if result_json else []
            print(f"\n✓ Hotel Match tamamlandı!")
            print(f"  Bulunan otel sayısı: {len(hotels)}")
            if hotels:
                for i, hotel in enumerate(hotels[:5], 1):
                    print(f"    {i}. {hotel.get('name', 'N/A')} - Score: {hotel.get('score', 'N/A')}")
    else:
        print(f"✗ Hotel Match başlatılamadı: {resp.status_code} - {resp.text}")

print()
print("=" * 60)
print("✅ ANALİZ TAMAMLANDI!")
print("=" * 60)
