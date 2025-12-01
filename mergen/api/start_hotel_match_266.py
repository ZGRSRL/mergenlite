#!/usr/bin/env python3
"""Start hotel match for analysis 266."""
import requests
import time

API_BASE = "http://localhost:8000"
OPP_ID = 3  # FIFA World Cup opportunity

print("=" * 70)
print("🏨 HOTEL MATCH BAŞLATILIYOR - Analiz #266")
print("=" * 70)
print()

# Get analysis 266 details first
print("📄 Analiz #266 detayları kontrol ediliyor...")
resp = requests.get(f"{API_BASE}/api/pipeline/results/266")
if resp.status_code == 200:
    data = resp.json()
    print(f"   Status: {data.get('status')}")
    print(f"   Type: {data.get('analysis_type')}")
    print(f"   Opportunity ID: {data.get('opportunity_id')}")
    OPP_ID = data.get('opportunity_id', OPP_ID)
    print()

# Start hotel match
print(f"🏨 Hotel Match başlatılıyor (Opportunity ID: {OPP_ID})...")
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
    
    # Wait for completion
    print(f"⏳ Hotel Match tamamlanması bekleniyor...")
    for i in range(30):  # Max 15 minutes
        time.sleep(30)
        status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status')
            print(f"   Status: {status} ({i*30}s)")
            
            if status == 'completed':
                print(f"   ✅ Hotel Match tamamlandı!")
                
                # Check hotels
                result_json = status_data.get('result_json', {})
                hotels = result_json.get('hotels', [])
                print(f"\n🏨 Bulunan Oteller: {len(hotels)}")
                if hotels:
                    for i, hotel in enumerate(hotels[:5], 1):
                        print(f"   {i}. {hotel.get('name', 'N/A')} - Score: {hotel.get('score', 'N/A')}")
                else:
                    print("   ⚠️ Otel bulunamadı")
                
                break
            elif status == 'failed':
                print(f"   ❌ Hotel Match başarısız!")
                break
else:
    print(f"   ❌ Hotel Match başlatılamadı: {hotel_resp.status_code}")
    print(f"   Response: {hotel_resp.text}")

print()
print("=" * 70)

