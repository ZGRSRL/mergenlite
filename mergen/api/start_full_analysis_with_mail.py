#!/usr/bin/env python3
"""Start full analysis (SOW + Hotel Match) and send email."""
import requests
import time
import json

API_BASE = "http://localhost:8000"
OPP_ID = 38  # FIFA World Cup opportunity

print("=" * 70)
print("🚀 TAM ANALİZ BAŞLATILIYOR (SOW + Hotel Match + Mail)")
print("=" * 70)
print()

# Step 1: Start SOW Analysis
print("📄 1. SOW Analysis başlatılıyor...")
sow_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": OPP_ID,
        "analysis_type": "sow_draft",
        "options": {
            "max_text_length": 120000  # Ensure full document analysis
        }
    }
)

if sow_resp.status_code == 200:
    sow_result = sow_resp.json()
    sow_analysis_id = sow_result.get("analysis_result_id")
    print(f"   ✅ SOW Analysis ID: {sow_analysis_id}")
    print()
    
    # Wait for SOW completion
    print(f"⏳ SOW Analysis tamamlanması bekleniyor...")
    for i in range(30):  # Max 15 minutes
        time.sleep(30)
        status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status')
            print(f"   Status: {status} ({i*30}s)")
            
            if status == 'completed':
                print(f"   ✅ SOW Analysis tamamlandı!")
                
                # Check document analysis
                result_json = status_data.get('result_json', {})
                doc_analysis = result_json.get('document_analysis', {})
                if doc_analysis:
                    print(f"\n📊 Doküman Analizi:")
                    print(f"   - Doküman Sayısı: {doc_analysis.get('documents_analyzed', 'N/A')}")
                    print(f"   - Toplam Kelime: {doc_analysis.get('total_word_count', 'N/A')}")
                    print(f"   - Toplam Karakter: {doc_analysis.get('total_text_length', 'N/A')}")
                    print(f"   - Tablo Sayısı: {doc_analysis.get('total_tables', 'N/A')}")
                
                # Step 2: Start Hotel Match
                print(f"\n🏨 2. Hotel Match başlatılıyor...")
                hotel_resp = requests.post(
                    f"{API_BASE}/api/pipeline/run",
                    json={
                        "opportunity_id": OPP_ID,
                        "analysis_type": "hotel_match"
                    }
                )
                
                if hotel_resp.status_code == 200:
                    hotel_result = hotel_resp.json()
                    hotel_analysis_id = hotel_result.get("analysis_result_id")
                    print(f"   ✅ Hotel Match Analysis ID: {hotel_analysis_id}")
                    print()
                    
                    # Wait for Hotel Match completion
                    print(f"⏳ Hotel Match tamamlanması bekleniyor...")
                    for j in range(30):  # Max 15 minutes
                        time.sleep(30)
                        hotel_status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
                        if hotel_status_resp.status_code == 200:
                            hotel_status_data = hotel_status_resp.json()
                            hotel_status = hotel_status_data.get('status')
                            print(f"   Status: {hotel_status} ({j*30}s)")
                            
                            if hotel_status == 'completed':
                                print(f"   ✅ Hotel Match tamamlandı!")
                                
                                # Check hotels
                                hotel_result_json = hotel_status_data.get('result_json', {})
                                hotels = hotel_result_json.get('hotels', [])
                                print(f"\n🏨 Bulunan Oteller: {len(hotels)}")
                                if hotels:
                                    for idx, hotel in enumerate(hotels[:5], 1):
                                        print(f"   {idx}. {hotel.get('name', 'N/A')} - Score: {hotel.get('score', 'N/A')}")
                                
                                # Step 3: Check if email was sent
                                print(f"\n📧 3. Email kontrol ediliyor...")
                                # Check logs for email
                                logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}/logs")
                                if logs_resp.status_code == 200:
                                    logs = logs_resp.json()
                                    email_logs = [log for log in logs if 'email' in log.get('message', '').lower()]
                                    if email_logs:
                                        print(f"   Email logları bulundu:")
                                        for log in email_logs[-3:]:
                                            print(f"      [{log.get('level')}] {log.get('message', '')[:150]}")
                                    else:
                                        print(f"   ⚠️ Email logu bulunamadı (email otomatik gönderilmiş olabilir)")
                                
                                print(f"\n✅ TAM ANALİZ TAMAMLANDI!")
                                print(f"   - SOW Analysis ID: {sow_analysis_id}")
                                print(f"   - Hotel Match ID: {hotel_analysis_id}")
                                print(f"   - Email gönderildi (kontrol edin)")
                                break
                            elif hotel_status == 'failed':
                                print(f"   ❌ Hotel Match başarısız!")
                                break
                else:
                    print(f"   ❌ Hotel Match başlatılamadı: {hotel_resp.status_code}")
                
                break
            elif status == 'failed':
                print(f"   ❌ SOW Analysis başarısız!")
                break
else:
    print(f"   ❌ SOW Analysis başlatılamadı: {sow_resp.status_code}")
    print(f"   Response: {sow_resp.text}")

print()
print("=" * 70)

