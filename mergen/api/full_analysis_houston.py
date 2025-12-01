#!/usr/bin/env python3
"""Full analysis for Houston opportunity - SOW + Hotel Match with full PDF."""
import requests
import time
import json
from pathlib import Path

API_BASE = "http://localhost:8000"
OPP_ID = 6  # Houston opportunity

print("=" * 70)
print("🚀 TAM ANALİZ - HOUSTON (SOW + HOTEL MATCH + PDF)")
print("=" * 70)
print()

# Step 1: Check opportunity
print("📋 Step 1: Opportunity kontrol ediliyor...")
opp_resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}")
if opp_resp.status_code == 200:
    opp = opp_resp.json()
    print(f"   ✅ Opportunity: {opp.get('title', 'N/A')[:60]}")
    print(f"   Notice ID: {opp.get('notice_id', 'N/A')}")
else:
    print(f"   ❌ Opportunity bulunamadı: {opp_resp.status_code}")
    exit(1)

# Step 2: Check/download attachments
print(f"\n📎 Step 2: Attachments kontrol ediliyor...")
atts_resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}/attachments")
if atts_resp.status_code == 200:
    atts = atts_resp.json()
    print(f"   Attachments: {len(atts)}")
    downloaded = sum(1 for att in atts if att.get('downloaded'))
    print(f"   Downloaded: {downloaded}/{len(atts)}")
    
    if downloaded < len(atts):
        print(f"\n📥 Attachments indiriliyor...")
        download_resp = requests.post(f"{API_BASE}/api/opportunities/{OPP_ID}/download-attachments")
        if download_resp.status_code == 200:
            download_job = download_resp.json()
            job_id = download_job.get('job_id')
            print(f"   Download Job: {job_id}")
            
            for i in range(18):  # Max 3 minutes
                time.sleep(10)
                status_resp = requests.get(f"{API_BASE}/api/download-jobs/{job_id}")
                if status_resp.status_code == 200:
                    status = status_resp.json()
                    if status.get('status') in ['completed', 'failed']:
                        print(f"   ✅ Download {status.get('status')}")
                        break

# Step 3: Start SOW Analysis
print(f"\n📄 Step 3: SOW Analysis başlatılıyor...")
sow_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={"opportunity_id": OPP_ID, "analysis_type": "sow_draft"}
)
if sow_resp.status_code == 200:
    sow_result = sow_resp.json()
    sow_analysis_id = sow_result.get("analysis_result_id")
    print(f"   ✅ SOW Analysis ID: {sow_analysis_id}")
    
    # Wait for SOW completion
    print(f"\n⏳ SOW Analysis tamamlanması bekleniyor...")
    for i in range(20):  # Max 10 minutes
        time.sleep(30)
        status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status')
            print(f"   Status: {status} ({i*30}s)")
            
            if status == 'completed':
                print(f"   ✅ SOW Analysis tamamlandı!")
                
                # Check PDF
                pdf_path = status_data.get('pdf_path')
                if pdf_path:
                    print(f"   📄 SOW PDF: {pdf_path}")
                    if Path(pdf_path).exists():
                        pdf_size = Path(pdf_path).stat().st_size
                        print(f"      Size: {pdf_size:,} bytes")
                
                # Check results
                result_json = status_data.get('result_json', {})
                sow_analysis = result_json.get('sow_analysis', {})
                doc_analysis = result_json.get('document_analysis', {})
                
                locations = sow_analysis.get('Locations', [])
                print(f"   🏙️ Locations: {len(locations)}")
                print(f"   📊 Words: {doc_analysis.get('total_word_count', 0):,}")
                print(f"   📋 Tables: {doc_analysis.get('total_tables', 0)}")
                
                # Step 4: Start Hotel Match
                print(f"\n🏨 Step 4: Hotel Match başlatılıyor...")
                hotel_resp = requests.post(
                    f"{API_BASE}/api/pipeline/run",
                    json={"opportunity_id": OPP_ID, "analysis_type": "hotel_match"}
                )
                if hotel_resp.status_code == 200:
                    hotel_result = hotel_resp.json()
                    hotel_analysis_id = hotel_result.get("analysis_result_id")
                    print(f"   ✅ Hotel Match ID: {hotel_analysis_id}")
                    
                    # Wait for Hotel Match
                    print(f"\n⏳ Hotel Match tamamlanması bekleniyor...")
                    for j in range(20):  # Max 10 minutes
                        time.sleep(30)
                        hotel_status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
                        if hotel_status_resp.status_code == 200:
                            hotel_status = hotel_status_resp.json()
                            hotel_status_val = hotel_status.get('status')
                            print(f"   Status: {hotel_status_val} ({j*30}s)")
                            
                            if hotel_status_val == 'completed':
                                print(f"   ✅ Hotel Match tamamlandı!")
                                
                                # Check Hotel PDF
                                hotel_pdf = hotel_status.get('pdf_path')
                                if hotel_pdf:
                                    print(f"   📄 Hotel PDF: {hotel_pdf}")
                                    if Path(hotel_pdf).exists():
                                        hotel_pdf_size = Path(hotel_pdf).stat().st_size
                                        print(f"      Size: {hotel_pdf_size:,} bytes")
                                
                                # Check hotels found
                                hotel_data = hotel_status.get('result_json', {})
                                hotels = hotel_data.get('hotels', [])
                                requirements = hotel_data.get('requirements', {})
                                
                                print(f"   🏨 Hotels Found: {len(hotels)}")
                                print(f"   🔍 City: {requirements.get('city_name')} ({requirements.get('city_code')})")
                                print(f"   📅 Dates: {requirements.get('check_in')} to {requirements.get('check_out')}")
                                
                                if hotels:
                                    print(f"\n   🏨 Top Hotels:")
                                    for i, hotel in enumerate(hotels[:3], 1):
                                        hotel_info = hotel.get('hotel', {}) or hotel
                                        print(f"      {i}. {hotel_info.get('name', 'N/A')}")
                                        price = hotel.get('price', {}) or hotel_info.get('price', {})
                                        if price:
                                            print(f"         Price: {price.get('total', 'N/A')} {price.get('currency', '')}")
                                
                                break
                            elif hotel_status_val == 'failed':
                                print(f"   ❌ Hotel Match başarısız!")
                                break
                else:
                    print(f"   ❌ Hotel Match başlatılamadı: {hotel_resp.status_code} - {hotel_resp.text}")
                
                break
            elif status == 'failed':
                print(f"   ❌ SOW Analysis başarısız!")
                break
else:
    print(f"   ❌ SOW Analysis başlatılamadı: {sow_resp.status_code} - {sow_resp.text}")

print()
print("=" * 70)
print("✅ ANALİZ TAMAMLANDI!")
print("=" * 70)

