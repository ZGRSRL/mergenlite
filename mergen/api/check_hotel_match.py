from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Get latest hotel match
hotel = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3,
    AIAnalysisResult.analysis_type == 'hotel_match'
).order_by(AIAnalysisResult.created_at.desc()).first()

if hotel:
    print(f"--- HOTEL MATCH RAPORU ---")
    print(f"Analysis ID: {hotel.id}")
    print(f"Status: {hotel.status}")
    print(f"Created: {hotel.created_at}")
    
    if hotel.result_json:
        data = hotel.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        if isinstance(data, dict):
            hotels = data.get('hotels', [])
            print(f"\n📊 Sonuçlar:")
            print(f"   - Hotels found: {len(hotels)}")
            
            if 'error' in data:
                print(f"\n❌ HATA:")
                print(f"   {data.get('error', 'Unknown error')}")
                if 'reasoning' in data:
                    print(f"\n   Reasoning: {data.get('reasoning', '')[:300]}")
            
            elif hotels:
                print(f"\n✅ BAŞARILI! Oteller bulundu:")
                for i, h in enumerate(hotels[:5], 1):
                    print(f"   {i}. {h.get('name', 'N/A')} - Score: {h.get('score', 'N/A')}")
                    print(f"      Price: {h.get('total_price', 'N/A')} {h.get('currency', 'USD')}")
            else:
                print(f"\n⚠️ No hotels in result")
                
            # Check requirements
            reqs = data.get('requirements', {})
            if reqs:
                print(f"\n🔍 Requirements:")
                print(f"   - City Code: {reqs.get('city_code', 'N/A')}")
                print(f"   - City Name: {reqs.get('city_name', 'N/A')}")
                print(f"   - Check In: {reqs.get('check_in', 'N/A')}")
                print(f"   - Check Out: {reqs.get('check_out', 'N/A')}")
    else:
        print("❌ No result_json")
else:
    print("No hotel match found")

db.close()

