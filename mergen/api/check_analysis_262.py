#!/usr/bin/env python3
"""Check analysis 262 details and fix dates for hotel match."""
import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("📊 ANALİZ 262 DETAYLARI VE TARİH KONTROLÜ")
print("=" * 70)
print()

# Check SOW Analysis 262
print("📄 SOW Analysis 262:")
sow_resp = requests.get(f"{API_BASE}/api/pipeline/results/262")
if sow_resp.status_code == 200:
    sow_data = sow_resp.json()
    result_json = sow_data.get('result_json', {})
    sow_analysis = result_json.get('sow_analysis', {})
    
    # Event Details
    event_details = sow_analysis.get('EventDetails', {})
    print(f"   Event: {event_details.get('event_name', 'N/A')}")
    print(f"   Start Date: {event_details.get('start_date', 'N/A')}")
    print(f"   End Date: {event_details.get('end_date', 'N/A')}")
    print(f"   Duration: {event_details.get('duration_days', 'N/A')} days")
    
    # Period of Performance
    pop = sow_analysis.get('PeriodOfPerformance', {})
    print(f"\n   Period of Performance:")
    print(f"      Start: {pop.get('start_date', 'N/A')}")
    print(f"      End: {pop.get('end_date', 'N/A')}")
    
    # Locations
    locations = sow_analysis.get('Locations', [])
    print(f"\n   Locations: {len(locations)}")
    for loc in locations[:3]:
        print(f"      - {loc.get('city', 'N/A')} ({loc.get('start_date', 'N/A')})")
    
    print(f"\n⚠️ Tarih Sorunu:")
    start_date = event_details.get('start_date') or pop.get('start_date')
    if start_date and start_date.startswith('2026'):
        print(f"   ❌ Tarihler 2026 olarak çıkarılmış, ancak 2025 olmalı!")
        print(f"   Mevcut: {start_date}")
        print(f"   Düzeltme: 2025 tarihleriyle hotel match yapılmalı")
    elif start_date and start_date.startswith('2025'):
        print(f"   ✅ Tarihler doğru (2025)")

print()
print("=" * 70)

