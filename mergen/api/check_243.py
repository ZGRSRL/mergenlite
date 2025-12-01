from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Check analysis 243
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 243).first()

if result:
    print(f"Analysis 243: {result.analysis_type} - {result.status}")
    
    if result.result_json:
        data = result.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        if result.analysis_type in ['sow', 'sow_draft']:
            # SOW Analysis
            sow_analysis = data.get('sow_analysis', {})
            if sow_analysis:
                locations = sow_analysis.get('Locations', [])
                print(f"\n✅ SOW Analysis:")
                print(f"   - Locations: {len(locations)}")
                if locations:
                    print(f"   🎉 BAŞARILI! Locations bulundu!")
                    for i, loc in enumerate(locations[:5], 1):
                        city = loc.get('city', 'N/A') if isinstance(loc, dict) else 'N/A'
                        print(f"      {i}. {city}")
                else:
                    print(f"   ❌ Locations array hala boş")
        elif result.analysis_type == 'hotel_match':
            # Hotel Match
            hotels = data.get('hotels', [])
            reqs = data.get('requirements', {})
            print(f"\n🏨 Hotel Match:")
            print(f"   - Hotels: {len(hotels)}")
            print(f"   - City Code: {reqs.get('city_code', 'N/A')}")
            print(f"   - City Name: {reqs.get('city_name', 'N/A')}")
            if hotels:
                print(f"   🎉 BAŞARILI! Oteller bulundu!")
else:
    print("Analysis 243 not found")

db.close()

