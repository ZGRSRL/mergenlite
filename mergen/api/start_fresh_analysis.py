#!/usr/bin/env python3
"""Start fresh analysis for opportunity 3."""
import requests
import time
import json

API_BASE = "http://localhost:8000"
OPP_ID = 3

print("=" * 70)
print("🚀 YENİ ANALİZ BAŞLATILIYOR - OPPORTUNITY 3")
print("=" * 70)
print()

# Step 1: SOW Analysis
print("📄 Step 1: SOW Analysis başlatılıyor...")
resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={"opportunity_id": OPP_ID, "analysis_type": "sow"}
)
if resp.status_code == 200:
    result = resp.json()
    sow_analysis_id = result.get("analysis_result_id")
    print(f"✓ SOW Analysis ID: {sow_analysis_id}")
    print()
    
    # Wait for completion with progress updates
    print("⏳ SOW Analysis tamamlanması bekleniyor...")
    print("   (Bu işlem 1-3 dakika sürebilir - AutoGen agent çalışıyor)")
    print()
    
    max_wait = 180  # 3 minutes
    for i in range(max_wait):
        time.sleep(2)
        resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
        if resp.status_code == 200:
            result = resp.json()
            status = result.get('status')
            
            # Show progress every 10 seconds
            if i % 5 == 0:
                print(f"   Status: {status} ({i*2}s)")
            
            if status in ['completed', 'failed']:
                print(f"\n✓ SOW Analysis {status}!")
                break
    
    # Check SOW results
    print("\n" + "=" * 70)
    print("📊 SOW ANALYSIS SONUÇLARI")
    print("=" * 70)
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
    if resp.status_code == 200:
        result = resp.json()
        result_json = result.get('result_json', {})
        if isinstance(result_json, str):
            result_json = json.loads(result_json)
        
        # Document analysis
        docs = result_json.get('analyzed_documents', [])
        total_chars = sum(doc.get('text_length', 0) for doc in docs)
        print(f"\n📄 Doküman Analizi:")
        print(f"   Toplam doküman: {len(docs)}")
        print(f"   Toplam karakter: {total_chars:,}")
        for i, doc in enumerate(docs, 1):
            print(f"     {i}. {doc.get('attachment_name', 'N/A')} - {doc.get('text_length', 0):,} chars")
        
        # SOW Analysis
        sow_analysis = result_json.get('sow_analysis')
        if sow_analysis:
            print(f"\n✅ SOW Analysis başarılı!")
            locations = sow_analysis.get('Locations', []) or sow_analysis.get('locations', [])
            print(f"   Bulunan şehir sayısı: {len(locations)}")
            
            if locations:
                print(f"\n   📍 Şehirler:")
                for i, loc in enumerate(locations[:15], 1):
                    city = loc.get('city', 'N/A')
                    stadium = loc.get('stadium', 'N/A')
                    start_date = loc.get('start_date', 'N/A')
                    print(f"     {i}. {city} - {stadium} - {start_date}")
            
            event_details = sow_analysis.get('EventDetails', {})
            if event_details:
                print(f"\n   📅 Event Details:")
                print(f"     Event Name: {event_details.get('event_name', 'N/A')}")
                print(f"     Start Date: {event_details.get('start_date', 'N/A')}")
                print(f"     End Date: {event_details.get('end_date', 'N/A')}")
        else:
            print(f"\n⚠️ SOW Analysis None - AutoGen agent çalışmadı veya başarısız oldu")
            print(f"   Status: {result.get('status')}")
        
        print()
        
        # Step 2: Hotel Match (if SOW has locations)
        if sow_analysis and locations:
            print("=" * 70)
            print("🏨 Step 2: Hotel Match başlatılıyor...")
            print("=" * 70)
            print()
            
            resp = requests.post(
                f"{API_BASE}/api/pipeline/run",
                json={"opportunity_id": OPP_ID, "analysis_type": "hotel_match"}
            )
            if resp.status_code == 200:
                result = resp.json()
                hotel_analysis_id = result.get("analysis_result_id")
                print(f"✓ Hotel Match ID: {hotel_analysis_id}")
                print()
                print("⏳ Hotel Match tamamlanması bekleniyor...")
                print("   (Bu işlem 2-5 dakika sürebilir - 11 şehir için API sorguları)")
                print()
                
                for i in range(180):
                    time.sleep(2)
                    resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
                    if resp.status_code == 200:
                        result = resp.json()
                        status = result.get('status')
                        if i % 5 == 0:
                            print(f"   Status: {status} ({i*2}s)")
                        if status in ['completed', 'failed']:
                            print(f"\n✓ Hotel Match {status}!")
                            break
                
                # Check Hotel Match results
                resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
                if resp.status_code == 200:
                    result = resp.json()
                    result_json = result.get('result_json', {})
                    if isinstance(result_json, str):
                        result_json = json.loads(result_json) if result_json else {}
                    
                    hotels = result_json.get('hotels', []) if result_json else []
                    requirements = result_json.get('requirements', {}) if result_json else {}
                    
                    print(f"\n🏨 Hotel Match Sonuçları:")
                    print(f"   City Code: {requirements.get('city_code', 'N/A')}")
                    print(f"   City Name: {requirements.get('city_name', 'N/A')}")
                    print(f"   Bulunan otel sayısı: {len(hotels)}")
                    if hotels:
                        for i, hotel in enumerate(hotels[:5], 1):
                            print(f"     {i}. {hotel.get('name', 'N/A')} - Score: {hotel.get('score', 'N/A')}")
            else:
                print(f"✗ Hotel Match başlatılamadı: {resp.status_code}")
        else:
            print("\n⚠️ Hotel Match başlatılmadı - SOW Analysis'te şehir bulunamadı")
    else:
        print(f"✗ Sonuçlar alınamadı: {resp.status_code}")
else:
    print(f"✗ SOW Analysis başlatılamadı: {resp.status_code} - {resp.text}")

print()
print("=" * 70)
print("✅ ANALİZ TAMAMLANDI!")
print("=" * 70)

