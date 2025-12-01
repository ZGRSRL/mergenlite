#!/usr/bin/env python3
"""Quick pipeline test - SOW → Auto Hotel Match → Email."""
import requests
import time

API_BASE = "http://localhost:8000"
OPP_ID = 6

print("=" * 70)
print("🚀 HIZLI PIPELINE TEST")
print("=" * 70)
print()

# Start SOW Analysis
print("📄 SOW Analysis başlatılıyor...")
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
    print(f"✅ SOW Analysis ID: {sow_analysis_id}")
    print(f"⏳ SOW Analysis bekleniyor (3 dakika)...")
    
    # Wait for SOW completion
    for i in range(6):
        time.sleep(30)
        status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status')
            print(f"   Status: {status} ({i*30}s)")
            
            if status == 'completed':
                print(f"   ✅ SOW Analysis tamamlandı!")
                print(f"\n🏨 Hotel Match otomatik başlatılması bekleniyor (3 dakika)...")
                
                # Wait for hotel match (check every 15 seconds)
                for j in range(12):
                    time.sleep(15)
                    # Check for hotel match
                    hotel_resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}/analysis")
                    if hotel_resp.status_code == 200:
                        hotel_data = hotel_resp.json()
                        hotel_results = hotel_data.get('results', [])
                        hotel_match = None
                        for result in hotel_results:
                            if result.get('analysis_type') == 'hotel_match' and result.get('id') > sow_analysis_id:
                                hotel_match = result
                                break
                        
                        if hotel_match:
                            hotel_status = hotel_match.get('status')
                            hotel_id = hotel_match.get('id')
                            print(f"   Hotel Match ID: {hotel_id}, Status: {hotel_status} ({j*15}s)")
                            
                            if hotel_status == 'completed':
                                print(f"   ✅ Hotel Match tamamlandı!")
                                
                                # Get details
                                hotel_detail = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_id}").json()
                                hotels = hotel_detail.get('result_json', {}).get('hotels', [])
                                reqs = hotel_detail.get('result_json', {}).get('requirements', {})
                                
                                print(f"\n📋 Sonuçlar:")
                                print(f"   City: {reqs.get('city_name', 'N/A')} ({reqs.get('city_code', 'N/A')})")
                                print(f"   Hotels: {len(hotels)}")
                                if hotels:
                                    print(f"   ✅ {len(hotels)} otel bulundu!")
                                    for idx, h in enumerate(hotels[:3], 1):
                                        print(f"      {idx}. {h.get('name', 'N/A')}")
                                
                                # Check email
                                logs = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_id}/logs").json()
                                email_logs = [l for l in logs if 'email' in l.get('message', '').lower()]
                                print(f"\n📧 Email: {'✅ Gönderildi' if email_logs else '❌ Gönderilmedi'}")
                                
                                print(f"\n✅ TEST TAMAMLANDI!")
                                break
                            elif hotel_status == 'failed':
                                print(f"   ❌ Hotel Match başarısız!")
                                break
                        elif j == 0:
                            print(f"   ⏳ Hotel Match henüz başlatılmadı...")
                
                break
            elif status == 'failed':
                print(f"   ❌ SOW Analysis başarısız!")
                break
else:
    print(f"❌ SOW Analysis başlatılamadı: {sow_resp.status_code}")

print()
print("=" * 70)

