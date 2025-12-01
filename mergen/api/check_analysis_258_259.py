#!/usr/bin/env python3
"""Check detailed results of analysis 258 (SOW) and 259 (Hotel Match)."""
import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("📊 ANALİZ DETAYLARI - 258 (SOW) ve 259 (HOTEL MATCH)")
print("=" * 70)
print()

# Check SOW Analysis 258
print("📄 SOW Analysis 258:")
sow_resp = requests.get(f"{API_BASE}/api/pipeline/results/258")
if sow_resp.status_code == 200:
    sow_data = sow_resp.json()
    result_json = sow_data.get('result_json', {})
    sow_analysis = result_json.get('sow_analysis', {})
    doc_analysis = result_json.get('document_analysis', {})
    
    print(f"   Status: {sow_data.get('status')}")
    print(f"   PDF: {sow_data.get('pdf_path', 'N/A')}")
    print(f"   Words: {doc_analysis.get('total_word_count', 0):,}")
    print(f"   Tables: {doc_analysis.get('total_tables', 0)}")
    
    # Event Details
    event_details = sow_analysis.get('EventDetails', {})
    print(f"\n   Event Details:")
    print(f"      Name: {event_details.get('event_name', 'N/A')}")
    print(f"      Agency: {event_details.get('agency', 'N/A')}")
    print(f"      Start: {event_details.get('start_date', 'N/A')}")
    print(f"      End: {event_details.get('end_date', 'N/A')}")
    
    # Locations
    locations = sow_analysis.get('Locations', [])
    print(f"\n   Locations ({len(locations)}):")
    for loc in locations[:3]:
        print(f"      - {loc.get('city', 'N/A')} ({loc.get('stadium', 'N/A')})")
    
    # Lodging Requirements
    lodging = sow_analysis.get('LodgingRequirements', {})
    print(f"\n   Lodging Requirements:")
    print(f"      Rooms: {lodging.get('rooms_per_city_min')}-{lodging.get('rooms_per_city_max')}")
    print(f"      Max Stay: {lodging.get('max_stay_days_per_city')} days")
    
    # Commercial Terms
    commercial = sow_analysis.get('CommercialTerms', {})
    print(f"\n   Commercial Terms:")
    print(f"      NAICS: {commercial.get('naics_code', 'N/A')}")
    print(f"      Set-Aside: {commercial.get('set_aside_type', 'N/A')}")

print("\n" + "=" * 70)

# Check Hotel Match 259
print("\n🏨 Hotel Match 259:")
hotel_resp = requests.get(f"{API_BASE}/api/pipeline/results/259")
if hotel_resp.status_code == 200:
    hotel_data = hotel_resp.json()
    result_json = hotel_data.get('result_json', {})
    
    print(f"   Status: {hotel_data.get('status')}")
    print(f"   PDF: {hotel_data.get('pdf_path', 'N/A')}")
    
    # Requirements
    requirements = result_json.get('requirements', {})
    print(f"\n   Requirements:")
    print(f"      City: {requirements.get('city_name')} ({requirements.get('city_code')})")
    print(f"      Check-in: {requirements.get('check_in')}")
    print(f"      Check-out: {requirements.get('check_out')}")
    print(f"      Adults: {requirements.get('adults')}")
    
    # Hotels
    hotels = result_json.get('hotels', [])
    print(f"\n   Hotels Found: {len(hotels)}")
    if hotels:
        for i, hotel in enumerate(hotels[:5], 1):
            hotel_info = hotel.get('hotel', {}) or hotel
            print(f"      {i}. {hotel_info.get('name', 'N/A')}")
            price = hotel.get('price', {}) or hotel_info.get('price', {})
            if price:
                print(f"         Price: {price.get('total', 'N/A')} {price.get('currency', '')}")
            print(f"         Score: {hotel.get('score', 'N/A')}")
    else:
        print("      (No hotels found)")
    
    # Reasoning
    reasoning = result_json.get('reasoning', '')
    if reasoning:
        print(f"\n   Reasoning: {reasoning[:200]}...")

print()
print("=" * 70)

