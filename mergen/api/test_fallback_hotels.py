#!/usr/bin/env python3
"""Test fallback mechanism with proper hotel names."""
import requests
import time

API_BASE = "http://localhost:8000"
OPP_ID = 6

print("=" * 70)
print("🚀 FALLBACK MECHANISM TEST - Hotel Names")
print("=" * 70)
print()

# Start Hotel Match directly (will use fallback if agent fails)
print("🏨 Hotel Match başlatılıyor...")
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
    print(f"✅ Hotel Match ID: {hotel_analysis_id}")
    print(f"⏳ Bekleniyor (~3 dakika)...")
    
    for j in range(12):
        time.sleep(15)
        status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status')
            print(f"   Status: {status} ({j*15}s)")
            
            if status == 'completed':
                print(f"   ✅ Tamamlandı!")
                
                hotels = status_data.get('result_json', {}).get('hotels', [])
                reqs = status_data.get('result_json', {}).get('requirements', {})
                fallback = status_data.get('result_json', {}).get('fallback_used', False)
                
                print(f"\n📋 Sonuçlar:")
                print(f"   City: {reqs.get('city_name', 'N/A')} ({reqs.get('city_code', 'N/A')})")
                print(f"   Hotels: {len(hotels)}")
                print(f"   Fallback: {'✅ Kullanıldı' if fallback else '❌ Kullanılmadı'}")
                
                if hotels:
                    print(f"\n   İlk 5 Otel:")
                    for idx, h in enumerate(hotels[:5], 1):
                        name = h.get('name', 'Unknown Hotel')
                        price = h.get('price_per_night', 0)
                        total = h.get('total_price', 0)
                        score = h.get('score', 'N/A')
                        print(f"      {idx}. {name}")
                        print(f"         Price/Night: ${price}, Total: ${total}, Score: {score}")
                
                # Check email
                logs = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}/logs").json()
                email_logs = [l for l in logs if 'email' in l.get('message', '').lower()]
                print(f"\n📧 Email: {'✅ Gönderildi' if email_logs else '❌ Gönderilmedi'}")
                
                break
            elif status == 'failed':
                print(f"   ❌ Başarısız!")
                break
else:
    print(f"❌ Başlatılamadı: {hotel_resp.status_code}")

print()
print("=" * 70)

