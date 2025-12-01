#!/usr/bin/env python3
"""Check analysis 268 and 269 details."""
import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("📊 ANALİZ 268 & 269 - DETAYLI KONTROL")
print("=" * 70)
print()

# Check SOW Analysis 268
print("📄 SOW Analysis 268:")
resp = requests.get(f"{API_BASE}/api/pipeline/results/268")
if resp.status_code == 200:
    data = resp.json()
    result_json = data.get('result_json', {})
    doc_analysis = result_json.get('document_analysis', {})
    sow_analysis = result_json.get('sow_analysis', {})
    
    print(f"   Status: {data.get('status')}")
    print(f"   PDF Path: {data.get('pdf_path', 'N/A')}")
    print(f"   JSON Path: {data.get('json_path', 'N/A')}")
    print()
    print(f"   Doküman Analizi:")
    print(f"      - Doküman: {doc_analysis.get('documents_analyzed', 'N/A')}")
    print(f"      - Kelime: {doc_analysis.get('total_word_count', 'N/A')}")
    print(f"      - Karakter: {doc_analysis.get('total_text_length', 'N/A')}")
    print(f"      - Tablo: {doc_analysis.get('total_tables', 'N/A')}")
    print()
    
    if sow_analysis:
        locations = sow_analysis.get('Locations', [])
        print(f"   SOW Analizi:")
        print(f"      - Locations: {len(locations)}")
        if locations:
            print(f"      - İlk Location: {locations[0].get('city', 'N/A')}")
        event_details = sow_analysis.get('EventDetails', {})
        print(f"      - Event: {event_details.get('event_name', 'N/A')}")
        print(f"      - Start Date: {event_details.get('start_date', 'N/A')}")
        print(f"      - End Date: {event_details.get('end_date', 'N/A')}")

print()
print("=" * 70)
print()

# Check Hotel Match 269
print("🏨 Hotel Match 269:")
hotel_resp = requests.get(f"{API_BASE}/api/pipeline/results/269")
if hotel_resp.status_code == 200:
    hotel_data = hotel_resp.json()
    hotel_result_json = hotel_data.get('result_json', {})
    
    print(f"   Status: {hotel_data.get('status')}")
    print(f"   PDF Path: {hotel_data.get('pdf_path', 'N/A')}")
    print()
    
    requirements = hotel_result_json.get('requirements', {})
    print(f"   Amadeus Parametreleri:")
    print(f"      - City Code: {requirements.get('city_code', 'N/A')}")
    print(f"      - City Name: {requirements.get('city_name', 'N/A')}")
    print(f"      - Check-In: {requirements.get('check_in', 'N/A')}")
    print(f"      - Check-Out: {requirements.get('check_out', 'N/A')}")
    print(f"      - Adults: {requirements.get('adults', 'N/A')}")
    
    # Calculate days
    if requirements.get('check_in') and requirements.get('check_out'):
        from datetime import datetime
        try:
            check_in_dt = datetime.fromisoformat(requirements.get('check_in'))
            check_out_dt = datetime.fromisoformat(requirements.get('check_out'))
            days = (check_out_dt - check_in_dt).days
            print(f"      - Gün Sayısı: {days} gün")
        except:
            pass
    
    print()
    hotels = hotel_result_json.get('hotels', [])
    print(f"   Bulunan Oteller: {len(hotels)}")
    if hotels:
        for i, hotel in enumerate(hotels[:5], 1):
            print(f"      {i}. {hotel.get('name', 'N/A')} - Score: {hotel.get('score', 'N/A')}")
    else:
        error = hotel_result_json.get('error', '')
        reasoning = hotel_result_json.get('reasoning', '')
        print(f"   ⚠️ Otel bulunamadı!")
        if error:
            print(f"      Error: {error[:200]}")
        if reasoning:
            print(f"      Reasoning: {reasoning[:200]}")

print()
print("=" * 70)

