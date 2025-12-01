#!/usr/bin/env python3
"""Check what cities Hotel Match is trying to use."""
import requests
import json
import sys
sys.path.insert(0, '/app')

from app.services.opportunity_context import build_hotel_match_requirements
from app.db import get_db
from app.models import Opportunity

API_BASE = "http://localhost:8000"
OPP_ID = 3

print("=" * 60)
print("🔍 HOTEL MATCH ŞEHİR KONTROLÜ")
print("=" * 60)
print()

# Get SOW Analysis
print("1. SOW Analysis sonuçlarını kontrol ediyorum...")
resp = requests.get(f"{API_BASE}/api/pipeline/results/201")
if resp.status_code == 200:
    result = resp.json()
    result_json = result.get('result_json', {})
    if isinstance(result_json, str):
        result_json = json.loads(result_json)
    
    sow_analysis = result_json.get('sow_analysis', {})
    if not sow_analysis:
        sow_analysis = {}
    locations = sow_analysis.get('Locations', []) if sow_analysis else []
    
    print(f"   SOW Analysis'te bulunan şehirler: {len(locations)}")
    if locations:
        for i, loc in enumerate(locations[:15], 1):
            city = loc.get('city', 'N/A')
            stadium = loc.get('stadium', 'N/A')
            start_date = loc.get('start_date', 'N/A')
            print(f"   {i}. {city} - Stadium: {stadium} - Start: {start_date}")
    else:
        print("   ⚠️ Hiç şehir bulunamadı!")
    
    event_details = sow_analysis.get('EventDetails', {})
    if event_details:
        print(f"\n   Event Details:")
        print(f"     Event Name: {event_details.get('event_name', 'N/A')}")
        print(f"     Start Date: {event_details.get('start_date', 'N/A')}")
        print(f"     End Date: {event_details.get('end_date', 'N/A')}")
else:
    print("   ✗ SOW Analysis bulunamadı")
    sow_analysis = None
    locations = []

print()

# Get document analysis
print("2. Document Analysis sonuçlarını kontrol ediyorum...")
resp = requests.get(f"{API_BASE}/api/pipeline/results/201")
if resp.status_code == 200:
    result = resp.json()
    result_json = result.get('result_json', {})
    if isinstance(result_json, str):
        result_json = json.loads(result_json)
    
    document_analysis = result_json.get('document_analysis', {})
    analyzed_docs = document_analysis.get('analyzed_documents', [])
    total_chars = sum(doc.get('text_length', 0) for doc in analyzed_docs)
    print(f"   Toplam karakter: {total_chars}")
    print(f"   Analiz edilen doküman: {len(analyzed_docs)}")
else:
    document_analysis = None

print()

# Test build_hotel_match_requirements
print("3. build_hotel_match_requirements fonksiyonunu test ediyorum...")
try:
    db = next(get_db())
    opportunity = db.query(Opportunity).filter(Opportunity.id == OPP_ID).first()
    
    if opportunity:
        print(f"   Opportunity: {opportunity.title}")
        print(f"   Notice ID: {opportunity.notice_id}")
        
        # Build requirements
        requirements = build_hotel_match_requirements(
            opportunity=opportunity,
            options=None,
            sow_analysis=sow_analysis,
            document_analysis=document_analysis
        )
        
        print(f"\n   ✓ Requirements oluşturuldu:")
        print(f"     City Code: {requirements.get('city_code', 'N/A')}")
        print(f"     City Name: {requirements.get('city_name', 'N/A')}")
        print(f"     Check In: {requirements.get('check_in', 'N/A')}")
        print(f"     Check Out: {requirements.get('check_out', 'N/A')}")
        print(f"     Adults: {requirements.get('adults', 'N/A')}")
        
        if locations and len(locations) > 0:
            print(f"\n   ⚠️ SOW Analysis'te {len(locations)} şehir var ama sadece 1 şehir kullanılıyor!")
            print(f"   Öneri: Hotel Match'i her şehir için ayrı ayrı çalıştırmak gerekebilir.")
    else:
        print("   ✗ Opportunity bulunamadı")
except Exception as e:
    print(f"   ✗ Hata: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)

