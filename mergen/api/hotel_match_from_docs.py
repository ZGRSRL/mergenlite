#!/usr/bin/env python3
"""Hotel match using dates from documents (no override)."""
import requests
import time

API_BASE = "http://localhost:8000"
OPP_ID = 6  # Houston opportunity

print("=" * 70)
print("🏨 HOTEL MATCH - DÖKÜMANLARDAN ÇIKARILAN TARİHLER İLE")
print("=" * 70)
print()

# Start Hotel Match - NO date override, use dates from SOW analysis
print("🏨 Hotel Match başlatılıyor (dökümanlardan çıkarılan tarihler ile)...")
hotel_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": OPP_ID,
        "analysis_type": "hotel_match",
        "options": {
            "force_refresh": True
            # NO date override - will use dates from SOW analysis (2026-03-03 to 2026-03-07)
        }
    }
)
if hotel_resp.status_code == 200:
    hotel_result = hotel_resp.json()
    hotel_analysis_id = hotel_result.get("analysis_result_id")
    print(f"   ✅ Hotel Match ID: {hotel_analysis_id}")
    print(f"   📅 Tarihler: Dökümanlardan çıkarılacak (2026-03-03 to 2026-03-07)")
    print(f"   🏙️ Şehir: Houston (HOU)")
    
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
                
                # Check hotels found
                hotel_data = hotel_status.get('result_json', {})
                hotels = hotel_data.get('hotels', [])
                requirements = hotel_data.get('requirements', {})
                
                print(f"\n   🏨 Hotels Found: {len(hotels)}")
                print(f"   🔍 City: {requirements.get('city_name')} ({requirements.get('city_code')})")
                print(f"   📅 Dates: {requirements.get('check_in')} to {requirements.get('check_out')}")
                
                if hotels:
                    print(f"\n   🏨 Top Hotels:")
                    for i, hotel in enumerate(hotels[:5], 1):
                        hotel_info = hotel.get('hotel', {}) or hotel
                        print(f"      {i}. {hotel_info.get('name', 'N/A')}")
                        price = hotel.get('price', {}) or hotel_info.get('price', {})
                        if price:
                            total = price.get('total', 'N/A')
                            currency = price.get('currency', 'USD')
                            print(f"         Price: {total} {currency}")
                        score = hotel.get('score', 'N/A')
                        print(f"         Score: {score}")
                else:
                    print(f"   ⚠️ Otel bulunamadı")
                    print(f"   Not: 2026 tarihleri için Amadeus test ortamında veri olmayabilir")
                
                break
            elif hotel_status_val == 'failed':
                print(f"   ❌ Hotel Match başarısız!")
                # Check logs
                logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}/logs?limit=10")
                if logs_resp.status_code == 200:
                    logs = logs_resp.json()
                    print(f"\n   Son loglar:")
                    for log in logs[-5:]:
                        print(f"      [{log.get('level')}] {log.get('message', '')[:150]}")
                break
else:
    print(f"   ❌ Hotel Match başlatılamadı: {hotel_resp.status_code} - {hotel_resp.text}")

print()
print("=" * 70)
print("📝 NOT:")
print("   Dökümanlarda tarihler 2026 olarak görünüyor.")
print("   Sistem dökümanlardan çıkarılan tarihleri kullanıyor (2026-03-03 to 2026-03-07).")
print("   Eğer tarihler yanlışsa, dökümanları kontrol edin.")
print("=" * 70)

