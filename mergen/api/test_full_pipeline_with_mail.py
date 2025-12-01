#!/usr/bin/env python3
"""Full pipeline test: SOW Analysis → Hotel Match → Email."""
import requests
import time

API_BASE = "http://localhost:8000"
OPP_ID = 6  # March 2026 National Assessment Governing Board Meeting - Houston, Texas

print("=" * 70)
print("🚀 TAM PIPELINE TEST - SOW → HOTEL MATCH → EMAIL")
print("=" * 70)
print()

# Get opportunity title
opp_resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}")
if opp_resp.status_code == 200:
    opp_data = opp_resp.json()
    title = opp_data.get('title', '')
    print(f"📄 Opportunity: {title}")
    print()

# Step 1: Start SOW Analysis
print("📄 1. SOW Analysis başlatılıyor...")
sow_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": OPP_ID,
        "analysis_type": "sow_draft",
        "options": {"max_text_length": 120000}
    }
)

if sow_resp.status_code == 200:
    sow_result = sow_resp.json()
    sow_analysis_id = sow_result.get("analysis_result_id")
    print(f"   ✅ SOW Analysis ID: {sow_analysis_id}")
    print(f"   ⏳ SOW Analysis tamamlanması bekleniyor...")
    
    for i in range(30):
        time.sleep(30)
        status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status')
            print(f"      Status: {status} ({i*30}s)")
            
            if status == 'completed':
                print(f"      ✅ SOW Analysis tamamlandı!")
                print(f"      ⏳ Hotel Match otomatik başlatılması bekleniyor...")
                break
            elif status == 'failed':
                print(f"      ❌ SOW Analysis başarısız!")
                exit(1)
    
    # Step 2: Wait for Hotel Match (auto-triggered)
    print(f"\n🏨 2. Hotel Match bekleniyor (otomatik tetiklenmiş olmalı)...")
    
    # Find hotel match result
    for j in range(40):
        time.sleep(15)
        # Check for hotel match results
        hotel_results_resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}/analysis")
        if hotel_results_resp.status_code == 200:
            hotel_data = hotel_results_resp.json()
            hotel_results = hotel_data.get('results', [])
            hotel_match = None
            for result in hotel_results:
                if result.get('analysis_type') == 'hotel_match':
                    hotel_match = result
                    break
            
            if hotel_match:
                hotel_status = hotel_match.get('status')
                hotel_analysis_id = hotel_match.get('id')
                print(f"   Hotel Match ID: {hotel_analysis_id}, Status: {hotel_status} ({j*15}s)")
                
                if hotel_status == 'completed':
                    print(f"   ✅ Hotel Match tamamlandı!")
                    
                    # Get hotel match details
                    hotel_detail_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
                    if hotel_detail_resp.status_code == 200:
                        hotel_detail = hotel_detail_resp.json()
                        hotel_result_json = hotel_detail.get('result_json', {})
                        hotels = hotel_result_json.get('hotels', [])
                        requirements = hotel_result_json.get('requirements', {})
                        
                        print(f"\n📋 Hotel Match Sonuçları:")
                        print(f"   City: {requirements.get('city_name', 'N/A')} ({requirements.get('city_code', 'N/A')})")
                        print(f"   Check-In: {requirements.get('check_in', 'N/A')}")
                        print(f"   Check-Out: {requirements.get('check_out', 'N/A')}")
                        print(f"   Adults: {requirements.get('adults', 'N/A')}")
                        print(f"   Bulunan Oteller: {len(hotels)}")
                        
                        if hotels:
                            print(f"   ✅ Oteller bulundu!")
                            for idx, hotel in enumerate(hotels[:3], 1):
                                print(f"      {idx}. {hotel.get('name', 'N/A')} - Score: {hotel.get('score', 'N/A')}")
                        else:
                            print(f"   ⚠️ Otel bulunamadı (fallback kullanılmış olabilir)")
                            fallback = hotel_result_json.get('fallback_used', False)
                            if fallback:
                                print(f"   ℹ️ Fallback mekanizması kullanıldı")
                    
                    # Check email logs
                    print(f"\n📧 3. Email kontrol ediliyor...")
                    logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}/logs")
                    if logs_resp.status_code == 200:
                        logs = logs_resp.json()
                        email_logs = [log for log in logs if 'email' in log.get('message', '').lower()]
                        if email_logs:
                            print(f"   ✅ Email gönderildi!")
                            for log in email_logs[-1:]:
                                print(f"      {log.get('message', '')[:200]}")
                        else:
                            print(f"   ⚠️ Email logları bulunamadı")
                    
                    print(f"\n✅ TAM PIPELINE TEST TAMAMLANDI!")
                    print(f"   - SOW Analysis ID: {sow_analysis_id}")
                    print(f"   - Hotel Match ID: {hotel_analysis_id}")
                    print(f"   - Bulunan Oteller: {len(hotels)}")
                    print(f"   - Email gönderildi: {'Evet' if email_logs else 'Bilinmiyor'}")
                    break
                elif hotel_status == 'failed':
                    print(f"   ❌ Hotel Match başarısız!")
                    break
            elif j == 0:
                print(f"   ⏳ Hotel Match henüz başlatılmadı, bekleniyor...")
else:
    print(f"   ❌ SOW Analysis başlatılamadı: {sow_resp.status_code}")

print()
print("=" * 70)
