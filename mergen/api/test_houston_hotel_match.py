#!/usr/bin/env python3
"""Test hotel matcher for Houston opportunity - verify city detection and hotel results."""
import requests
import time
import json

API_BASE = "http://localhost:8000"
OPP_ID = 6  # March 2026 National Assessment Governing Board Meeting - Houston, Texas

print("=" * 70)
print("🚀 HOUSTON HOTEL MATCHER TEST")
print("=" * 70)
print()

# Get opportunity title
opp_resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}")
if opp_resp.status_code == 200:
    opp_data = opp_resp.json()
    title = opp_data.get('title', '')
    print(f"📄 Opportunity Title: {title}")
    print()

# Step 1: Start SOW Analysis (if not exists)
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
                break
            elif status == 'failed':
                print(f"      ❌ SOW Analysis başarısız!")
                exit(1)
else:
    print(f"   ❌ SOW Analysis başlatılamadı: {sow_resp.status_code}")
    exit(1)

print()

# Step 2: Start Hotel Match (NO options - let it auto-detect from title/documents)
print(f"🏨 2. Hotel Match başlatılıyor (dokümanlardan otomatik şehir tespiti)...")
hotel_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": OPP_ID,
        "analysis_type": "hotel_match"
        # NO options - sistem title ve dokümanlardan Houston'ı bulmalı
    }
)

if hotel_resp.status_code == 200:
    hotel_result = hotel_resp.json()
    hotel_analysis_id = hotel_result.get("analysis_result_id")
    print(f"   ✅ Hotel Match Analysis ID: {hotel_analysis_id}")
    print()
    
    # Wait for Hotel Match completion
    print(f"⏳ Hotel Match tamamlanması bekleniyor...")
    for j in range(30):
        time.sleep(30)
        hotel_status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
        if hotel_status_resp.status_code == 200:
            hotel_status_data = hotel_status_resp.json()
            hotel_status = hotel_status_data.get('status')
            print(f"   Status: {hotel_status} ({j*30}s)")
            
            if hotel_status == 'completed':
                print(f"   ✅ Hotel Match tamamlandı!")
                
                hotel_result_json = hotel_status_data.get('result_json', {})
                requirements = hotel_result_json.get('requirements', {})
                hotels = hotel_result_json.get('hotels', [])
                
                print(f"\n📋 Hotel Match Parametreleri:")
                print(f"   City Code: {requirements.get('city_code', 'N/A')}")
                print(f"   City Name: {requirements.get('city_name', 'N/A')}")
                print(f"   Check-In: {requirements.get('check_in', 'N/A')}")
                print(f"   Check-Out: {requirements.get('check_out', 'N/A')}")
                print(f"   Adults: {requirements.get('adults', 'N/A')}")
                
                if requirements.get('city_code') == 'HOU':
                    print(f"   ✅ DOĞRU ŞEHİR: Houston (HOU) tespit edildi!")
                else:
                    print(f"   ⚠️ YANLIŞ ŞEHİR: {requirements.get('city_code')} (Houston/HOU olmalıydı)")
                
                print(f"\n🏨 Bulunan Oteller: {len(hotels)}")
                if hotels:
                    print(f"   ✅ Otel bulundu! İlk 5 otel:")
                    for idx, hotel in enumerate(hotels[:5], 1):
                        name = hotel.get('name', 'N/A')
                        score = hotel.get('score', 'N/A')
                        price = hotel.get('price_per_night', 'N/A')
                        print(f"      {idx}. {name} - Score: {score}, Price: ${price}")
                else:
                    error = hotel_result_json.get('error', '')
                    reasoning = hotel_result_json.get('reasoning', '')
                    print(f"   ⚠️ Otel bulunamadı")
                    if error:
                        print(f"      Error: {error[:200]}")
                    if reasoning:
                        print(f"      Reasoning: {reasoning[:200]}")
                
                # Check logs
                print(f"\n📊 3. Loglar kontrol ediliyor...")
                logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}/logs")
                if logs_resp.status_code == 200:
                    logs = logs_resp.json()
                    llm_logs = [log for log in logs if 'llm' in log.get('message', '').lower() or 'openai' in log.get('message', '').lower()]
                    print(f"   Toplam log sayısı: {len(logs)}")
                    print(f"   LLM ile ilgili loglar: {len(llm_logs)}")
                    if llm_logs:
                        print(f"   ✅ LLM logları bulundu!")
                
                print(f"\n✅ TEST TAMAMLANDI!")
                print(f"   - Hotel Match ID: {hotel_analysis_id}")
                print(f"   - Şehir: {requirements.get('city_name', 'N/A')} ({requirements.get('city_code', 'N/A')})")
                print(f"   - Bulunan Oteller: {len(hotels)}")
                break
            elif hotel_status == 'failed':
                print(f"   ❌ Hotel Match başarısız!")
                # Get error details
                hotel_result_json = hotel_status_data.get('result_json', {})
                error = hotel_result_json.get('error', '')
                print(f"   Error: {error[:300]}")
                break
else:
    print(f"   ❌ Hotel Match başlatılamadı: {hotel_resp.status_code}")
    print(f"   Response: {hotel_resp.text[:200]}")

print()
print("=" * 70)
