#!/usr/bin/env python3
"""Download attachments and start analysis for opportunity 6."""
import requests
import time
import json

API_BASE = "http://localhost:8000"
OPP_ID = 6

print("=" * 70)
print("📥 DOKÜMAN İNDİRME VE ANALİZ - OPPORTUNITY 6")
print("=" * 70)
print()

# Step 1: Download attachments
print("📥 Step 1: Dokümanlar indiriliyor...")
resp = requests.post(f"{API_BASE}/api/opportunities/{OPP_ID}/download-attachments")

if resp.status_code == 200:
    job = resp.json()
    job_id = job.get('job_id')
    print(f"✅ Download job started: {job_id}")
    
    # Wait for download to complete
    print("⏳ İndirme tamamlanması bekleniyor...")
    for i in range(60):  # Max 3 minutes
        time.sleep(2)
        resp = requests.get(f"{API_BASE}/api/jobs/{job_id}")
        if resp.status_code == 200:
            job_status = resp.json()
            status = job_status.get('status')
            if i % 5 == 0:
                print(f"   Download status: {status} ({i*2}s)")
            
            if status in ['completed', 'failed']:
                print(f"\n✅ Download {status}!")
                if status == 'failed':
                    error = job_status.get('error', 'Unknown error')
                    print(f"   Error: {error}")
                break
    
    # Check attachments
    print("\n📋 Attachments kontrol ediliyor...")
    resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}/attachments")
    if resp.status_code == 200:
        attachments = resp.json()
        print(f"   Found {len(attachments)} attachments")
        downloaded = [a for a in attachments if a.get('downloaded')]
        print(f"   Downloaded: {len(downloaded)}")
        
        if len(downloaded) == 0:
            print("   ⚠️ Hiç doküman indirilmemiş!")
            print("   Analiz başlatılamaz - önce dokümanları indirmelisiniz")
            exit(1)
else:
    print(f"❌ Download başlatılamadı: {resp.status_code}")
    print(resp.text)
    exit(1)

# Step 2: Start analysis
print("\n" + "=" * 70)
print("🚀 Step 2: Analiz başlatılıyor...")
print("=" * 70)
print()

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
                    print(f"✅ PDF: {pdf_path}")
                else:
                    print("❌ PDF üretilmedi")
                
                # Check result
                result_json = result.get('result_json', {})
                if isinstance(result_json, str):
                    result_json = json.loads(result_json)
                
                doc_analysis = result_json.get('document_analysis', {})
                words = doc_analysis.get('total_word_count', 0)
                chars = doc_analysis.get('total_text_length', 0)
                print(f"📊 Words: {words:,}, Chars: {chars:,}")
                
                sow_analysis = result_json.get('sow_analysis', {})
                if sow_analysis:
                    locations = sow_analysis.get('Locations', [])
                    print(f"🏙️ Locations: {len(locations)}")
                else:
                    print("❌ SOW Analysis yok")
                
                break
else:
    print(f"❌ Hata: {resp.status_code}")
    print(resp.text)

