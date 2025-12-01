#!/usr/bin/env python3
"""Full analysis for a new opportunity - SOW + Hotel Match."""
import requests
import time
import json
from pathlib import Path

API_BASE = "http://localhost:8000"

print("=" * 70)
print("🚀 TAM ANALİZ - YENİ FIRSAT (SOW + HOTEL MATCH)")
print("=" * 70)
print()

# Get a new opportunity (recently synced)
print("📋 Step 1: Yeni opportunity seçiliyor...")
opps_resp = requests.get(f"{API_BASE}/api/opportunities?limit=5&sort=created_at&order=desc")
if opps_resp.status_code == 200:
    opps = opps_resp.json()
    if opps:
        # Find one without analysis
        selected_opp = None
        for opp in opps:
            # Check if it has completed analysis
            analysis_resp = requests.get(f"{API_BASE}/api/opportunities/{opp['id']}/analyses")
            if analysis_resp.status_code == 200:
                analyses = analysis_resp.json()
                has_completed = any(a.get('status') == 'completed' for a in analyses)
                if not has_completed:
                    selected_opp = opp
                    break
        
        if not selected_opp:
            selected_opp = opps[0]  # Use first one anyway
        
        opp_id = selected_opp['id']
        notice_id = selected_opp.get('notice_id', 'N/A')
        title = selected_opp.get('title', 'N/A')[:60]
        
        print(f"   ✅ Seçilen Opportunity:")
        print(f"      ID: {opp_id}")
        print(f"      Notice ID: {notice_id}")
        print(f"      Title: {title}")
        
        # Check attachments
        print(f"\n📎 Step 2: Attachments kontrol ediliyor...")
        atts_resp = requests.get(f"{API_BASE}/api/opportunities/{opp_id}/attachments")
        if atts_resp.status_code == 200:
            atts = atts_resp.json()
            print(f"   Attachments: {len(atts)}")
            downloaded = sum(1 for att in atts if att.get('downloaded'))
            print(f"   Downloaded: {downloaded}/{len(atts)}")
            
            # Download if needed
            if downloaded < len(atts):
                print(f"\n📥 Step 3: Attachments indiriliyor...")
                download_resp = requests.post(f"{API_BASE}/api/opportunities/{opp_id}/download-attachments")
                if download_resp.status_code == 200:
                    download_job = download_resp.json()
                    job_id = download_job.get('job_id')
                    print(f"   Download Job: {job_id}")
                    
                    # Wait for download
                    for i in range(30):  # Max 5 minutes
                        time.sleep(10)
                        status_resp = requests.get(f"{API_BASE}/api/download-jobs/{job_id}")
                        if status_resp.status_code == 200:
                            status = status_resp.json()
                            if status.get('status') in ['completed', 'failed']:
                                print(f"   ✅ Download {status.get('status')}")
                                break
        
        # Start SOW Analysis
        print(f"\n📄 Step 4: SOW Analysis başlatılıyor...")
        sow_resp = requests.post(
            f"{API_BASE}/api/pipeline/run",
            json={"opportunity_id": opp_id, "analysis_type": "sow_draft"}
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
                            print(f"   📄 PDF: {pdf_path}")
                            if Path(pdf_path).exists():
                                pdf_size = Path(pdf_path).stat().st_size
                                print(f"      Size: {pdf_size:,} bytes")
                        
                        # Check results
                        result_json = status_data.get('result_json', {})
                        sow_analysis = result_json.get('sow_analysis', {})
                        locations = sow_analysis.get('Locations', [])
                        print(f"   🏙️ Locations: {len(locations)}")
                        
                        # Start Hotel Match
                        print(f"\n🏨 Step 5: Hotel Match başlatılıyor...")
                        hotel_resp = requests.post(
                            f"{API_BASE}/api/opportunities/{opp_id}/analyze",
                            json={"analysis_type": "hotel_match", "options": {"force_refresh": True}}
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
                                        print(f"   🏨 Hotels Found: {len(hotels)}")
                                        
                                        break
                        else:
                            print(f"   ❌ Hotel Match başlatılamadı: {hotel_resp.status_code}")
                        
                        break
                    elif status == 'failed':
                        print(f"   ❌ SOW Analysis başarısız!")
                        break
        else:
            print(f"   ❌ SOW Analysis başlatılamadı: {sow_resp.status_code}")
    else:
        print("   ❌ Opportunity bulunamadı")
else:
    print(f"   ❌ Opportunities alınamadı: {opps_resp.status_code}")

print()
print("=" * 70)
print("✅ ANALİZ TAMAMLANDI!")
print("=" * 70)

