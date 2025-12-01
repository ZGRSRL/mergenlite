#!/usr/bin/env python3
"""Start hotel match for opportunity 6 (Houston)."""
import requests
import time
import json

API_BASE = "http://localhost:8000"
OPP_ID = 6

print("=" * 70)
print("🏨 HOTEL MATCH BAŞLATILIYOR - OPPORTUNITY 6 (HOUSTON)")
print("=" * 70)
print()

# Start Hotel Match
print("🔍 Hotel Match başlatılıyor...")
resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": OPP_ID,
        "analysis_type": "hotel_match",
        "pipeline_version": "v1",
        "options": {"force_refresh": True}
    }
)

if resp.status_code == 200:
    result = resp.json()
    hotel_analysis_id = result.get("analysis_result_id")
    print(f"✅ Hotel Match Analysis ID: {hotel_analysis_id}")
    print()
    
    # Wait for completion
    print("⏳ Otel eşleştirmesi tamamlanması bekleniyor...")
    print("   (Amadeus API'den Houston otelleri çekiliyor)")
    print()
    
    max_wait = 300  # 5 minutes
    for i in range(max_wait):
        time.sleep(3)
        resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
        if resp.status_code == 200:
            result = resp.json()
            status = result.get('status')
            
            if i % 10 == 0:
                print(f"   Status: {status} ({i*3}s)")
            
            if status in ['completed', 'failed']:
                print(f"\n✅ Hotel Match {status}!")
                
                # Check PDF
                pdf_path = result.get('pdf_path')
                if pdf_path:
                    print(f"✅ Hotel PDF: {pdf_path}")
                else:
                    print("⚠️ Hotel PDF üretilmedi")
                
                # Check hotels
                result_json = result.get('result_json', {})
                if isinstance(result_json, str):
                    result_json = json.loads(result_json)
                
                hotels = result_json.get('hotels', [])
                print(f"\n🏨 Bulunan Oteller: {len(hotels)}")
                
                if hotels:
                    print("\n🏨 İlk 5 Otel:")
                    for i, hotel in enumerate(hotels[:5], 1):
                        print(f"\n   {i}. {hotel.get('name', 'N/A')}")
                        print(f"      Score: {hotel.get('score', 0):.2f}")
                        price = hotel.get('price', {})
                        if isinstance(price, dict):
                            print(f"      Price: ${price.get('total', 'N/A')} {price.get('currency', '')}")
                        else:
                            print(f"      Price: {price}")
                        distance = hotel.get('distance', {})
                        if isinstance(distance, dict):
                            print(f"      Distance: {distance.get('value', 'N/A')} {distance.get('unit', '')}")
                        else:
                            print(f"      Distance: {distance}")
                else:
                    print("   ⚠️ Otel bulunamadı")
                
                # Check requirements
                reqs = result_json.get('requirements', {})
                print(f"\n🔍 Requirements:")
                print(f"   City: {reqs.get('city_name')} ({reqs.get('city_code')})")
                print(f"   Check-in: {reqs.get('check_in')}")
                print(f"   Check-out: {reqs.get('check_out')}")
                print(f"   Adults: {reqs.get('adults')}")
                
                # Check for errors
                if result_json.get('error'):
                    print(f"\n❌ Error: {result_json.get('error')}")
                
                reasoning = result_json.get('reasoning', '')
                if reasoning and len(reasoning) > 50:
                    print(f"\n💭 Reasoning (ilk 300 karakter):")
                    print(f"   {reasoning[:300]}...")
                
                break
else:
    print(f"❌ Hata: {resp.status_code}")
    print(resp.text)

