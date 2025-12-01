from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

print("=" * 60)
print("SOW ANALİZİ VE HOTEL MATCH AKIŞ KONTROLÜ")
print("=" * 60)

# 1. En son SOW analizini kontrol et
sow = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3,
    AIAnalysisResult.analysis_type.in_(['sow', 'sow_draft']),
    AIAnalysisResult.status == 'completed'
).order_by(AIAnalysisResult.created_at.desc()).first()

if sow:
    print(f"\n✅ SOW ANALİZİ BULUNDU:")
    print(f"   ID: {sow.id}")
    print(f"   Status: {sow.status}")
    print(f"   Created: {sow.created_at}")
    
    if sow.result_json:
        data = sow.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        # Document analysis kontrolü
        doc_analysis = data.get('document_analysis', {})
        chars = doc_analysis.get('total_text_length', 0)
        words = doc_analysis.get('total_word_count', 0)
        tables = doc_analysis.get('total_tables', 0)
        
        print(f"\n   📊 Doküman İstatistikleri:")
        print(f"      - Karakter: {chars:,}")
        print(f"      - Kelime: {words:,}")
        print(f"      - Tablo: {tables}")
        
        # SOW analysis kontrolü
        sow_analysis = data.get('sow_analysis', {})
        if sow_analysis and isinstance(sow_analysis, dict):
            print(f"\n   ✅ SOW Analysis Var!")
            
            # Locations kontrolü
            locations = sow_analysis.get('Locations', [])
            print(f"      - Locations: {len(locations)}")
            if locations:
                print(f"      - İlk Şehir: {locations[0].get('city', 'N/A')}")
                if len(locations) >= 11:
                    print(f"      🎉 11 şehir bulundu!")
            else:
                print(f"      ❌ Locations array boş!")
            
            # Event Details kontrolü
            event_details = sow_analysis.get('EventDetails', {})
            if event_details:
                print(f"      - Event Name: {event_details.get('event_name', 'N/A')}")
                print(f"      - Agency: {event_details.get('agency', 'N/A')}")
        else:
            print(f"\n   ❌ SOW Analysis yok veya boş!")
    else:
        print(f"\n   ❌ result_json yok!")
else:
    print(f"\n❌ SOW analizi bulunamadı!")

# 2. En son Hotel Match'i kontrol et
hotel = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3,
    AIAnalysisResult.analysis_type == 'hotel_match'
).order_by(AIAnalysisResult.created_at.desc()).first()

if hotel:
    print(f"\n" + "=" * 60)
    print(f"✅ HOTEL MATCH BULUNDU:")
    print(f"   ID: {hotel.id}")
    print(f"   Status: {hotel.status}")
    print(f"   Created: {hotel.created_at}")
    
    if hotel.result_json:
        data = hotel.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        # Requirements kontrolü
        reqs = data.get('requirements', {})
        print(f"\n   🔍 Requirements:")
        print(f"      - City Code: {reqs.get('city_code', 'N/A')}")
        print(f"      - City Name: {reqs.get('city_name', 'N/A')}")
        print(f"      - Check In: {reqs.get('check_in', 'N/A')}")
        print(f"      - Check Out: {reqs.get('check_out', 'N/A')}")
        print(f"      - Adults: {reqs.get('adults', 'N/A')}")
        
        # SOW requirements kontrolü
        sow_reqs = data.get('sow_requirements', {})
        if sow_reqs:
            print(f"\n   📋 SOW Requirements (Hotel Match'e gönderilen):")
            locations = sow_reqs.get('Locations', [])
            print(f"      - Locations in SOW reqs: {len(locations)}")
            if locations:
                print(f"      - First city: {locations[0].get('city', 'N/A')}")
        
        # Hotels kontrolü
        hotels = data.get('hotels', [])
        print(f"\n   🏨 Hotels:")
        print(f"      - Found: {len(hotels)}")
        
        if 'error' in data:
            print(f"\n   ❌ HATA:")
            print(f"      {data.get('error', 'Unknown')[:300]}")
        
        # Reasoning kontrolü
        reasoning = data.get('reasoning', '')
        if reasoning:
            print(f"\n   💭 Reasoning (ilk 200 karakter):")
            print(f"      {reasoning[:200]}")
    else:
        print(f"\n   ❌ result_json yok!")
else:
    print(f"\n❌ Hotel Match bulunamadı!")

# 3. Pipeline log kontrolü - hangi SOW kullanıldı?
print(f"\n" + "=" * 60)
print("PIPELINE SOW SEÇİMİ KONTROLÜ")
print("=" * 60)

# Pipeline'ın Locations array'i olan SOW'u seçip seçmediğini kontrol et
sows_with_locations = []
all_sows = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3,
    AIAnalysisResult.analysis_type.in_(['sow', 'sow_draft']),
    AIAnalysisResult.status == 'completed'
).order_by(AIAnalysisResult.created_at.desc()).limit(10).all()

for s in all_sows:
    if s.result_json:
        d = s.result_json
        if isinstance(d, str):
            d = json.loads(d)
        sow_an = d.get('sow_analysis', {})
        if sow_an and isinstance(sow_an, dict):
            locs = sow_an.get('Locations', [])
            if locs and len(locs) > 0:
                sows_with_locations.append((s.id, len(locs)))

print(f"\nLocations array'i olan SOW analizleri:")
for sid, loc_count in sows_with_locations:
    print(f"   - SOW ID {sid}: {loc_count} locations")

db.close()

