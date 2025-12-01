#!/usr/bin/env python3
"""Start new analysis for opportunity 3 to test PDF and email."""
import requests
import time
import json

API_BASE = "http://localhost:8000"
OPP_ID = 3

print("=" * 70)
print("🚀 YENİ ANALİZ BAŞLATILIYOR - PDF VE MAİL TESTİ")
print("=" * 70)
print()

# Start SOW Analysis
print("📄 SOW Analysis başlatılıyor...")
resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": OPP_ID,
        "analysis_type": "sow_draft",
        "pipeline_version": "v1"
    }
)

if resp.status_code == 200:
    result = resp.json()
    analysis_id = result.get("analysis_result_id")
    print(f"✅ Analysis ID: {analysis_id}")
    print()
    
    # Wait for completion
    print("⏳ Analiz tamamlanması bekleniyor...")
    print("   (PDF üretilecek ve mail gönderilecek)")
    print()
    
    max_wait = 300  # 5 minutes
    for i in range(max_wait):
        time.sleep(3)
        resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
        if resp.status_code == 200:
            result = resp.json()
            status = result.get('status')
            
            if i % 10 == 0:
                print(f"   Status: {status} ({i*3}s)")
            
            if status in ['completed', 'failed']:
                print(f"\n✅ Analiz {status}!")
                
                # Check PDF
                pdf_path = result.get('pdf_path')
                if pdf_path:
                    print(f"✅ PDF üretildi: {pdf_path}")
                else:
                    print("❌ PDF üretilmedi")
                
                # Check result
                result_json = result.get('result_json', {})
                if isinstance(result_json, str):
                    result_json = json.loads(result_json)
                
                sow_analysis = result_json.get('sow_analysis', {})
                locations = sow_analysis.get('Locations', [])
                print(f"✅ Locations: {len(locations)}")
                
                break
else:
    print(f"❌ Hata: {resp.status_code}")
    print(resp.text)

