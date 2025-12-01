#!/usr/bin/env python3
"""Check hotel match 267 details and what was sent to Amadeus."""
import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("🔍 HOTEL MATCH 267 - DETAYLI KONTROL")
print("=" * 70)
print()

# Get hotel match 267
resp = requests.get(f"{API_BASE}/api/pipeline/results/267")
if resp.status_code == 200:
    data = resp.json()
    result_json = data.get('result_json', {})
    
    print("📄 Hotel Match Result:")
    print(f"   Status: {data.get('status')}")
    print(f"   Analysis ID: 267")
    print()
    
    # Requirements
    requirements = result_json.get('requirements', {})
    print("📋 Amadeus API'ye Gönderilen Parametreler:")
    print(f"   City Code: {requirements.get('city_code', 'N/A')}")
    print(f"   City Name: {requirements.get('city_name', 'N/A')}")
    print(f"   Check-In: {requirements.get('check_in', 'N/A')}")
    print(f"   Check-Out: {requirements.get('check_out', 'N/A')}")
    print(f"   Adults: {requirements.get('adults', 'N/A')}")
    print(f"   Must Have: {requirements.get('must_have', [])}")
    print()
    
    # Hotels
    hotels = result_json.get('hotels', [])
    print(f"🏨 Bulunan Oteller: {len(hotels)}")
    if hotels:
        for i, hotel in enumerate(hotels[:5], 1):
            print(f"\n   {i}. {hotel.get('name', 'N/A')}")
            print(f"      Score: {hotel.get('score', 'N/A')}")
            print(f"      Price: {hotel.get('price_per_night', 'N/A')}")
    else:
        print("   ⚠️ Otel bulunamadı!")
        print()
        
        # Check reasoning
        reasoning = result_json.get('reasoning', '')
        if reasoning:
            print(f"📝 Reasoning: {reasoning[:500]}")
            print()
        
        # Check for errors
        error = result_json.get('error', '')
        if error:
            print(f"❌ Error: {error}")
            print()
        
        # Check requirements_analysis
        req_analysis = result_json.get('requirements_analysis', {})
        if req_analysis:
            print(f"📊 Requirements Analysis: {json.dumps(req_analysis, indent=2)}")
            print()
    
    # Full result_json keys
    print(f"📋 Result JSON Keys: {list(result_json.keys())}")
    print()
    
    # Check logs
    print("📝 Pipeline Logları kontrol ediliyor...")
    logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/267/logs")
    if logs_resp.status_code == 200:
        logs = logs_resp.json()
        print(f"   Toplam log: {len(logs)}")
        # Find Amadeus-related logs
        amadeus_logs = [log for log in logs if 'amadeus' in log.get('message', '').lower() or 'hotel' in log.get('message', '').lower()]
        if amadeus_logs:
            print(f"   Amadeus/Hotel ile ilgili loglar:")
            for log in amadeus_logs[-10:]:  # Son 10 log
                print(f"      [{log.get('level')}] {log.get('message', '')[:200]}")
        else:
            print("   ⚠️ Amadeus/Hotel ile ilgili log bulunamadı")
    else:
        print(f"   ⚠️ Loglar alınamadı: {logs_resp.status_code}")

print()
print("=" * 70)

