from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Check analysis 226
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 226).first()
if result:
    print(f"Analysis 226: {result.analysis_type} - {result.status}")

# Check latest hotel match
hotel = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3,
    AIAnalysisResult.analysis_type == 'hotel_match'
).order_by(AIAnalysisResult.created_at.desc()).first()

if hotel:
    print(f"\nLatest Hotel Match (ID {hotel.id}):")
    print(f"  Status: {hotel.status}")
    print(f"  Created: {hotel.created_at}")
    if hotel.result_json:
        data = hotel.result_json
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict):
            hotels = data.get('hotels', [])
            print(f"  Hotels found: {len(hotels)}")
            if 'error' in data:
                print(f"  ❌ Error: {data.get('error', 'Unknown')[:300]}")
                if 'reasoning' in data:
                    print(f"  Reasoning: {data.get('reasoning', 'N/A')[:200]}")
            elif hotels:
                print(f"  ✅ SUCCESS! Hotels found:")
                for i, h in enumerate(hotels[:3], 1):
                    print(f"    {i}. {h.get('name', 'N/A')} - Score: {h.get('score', 'N/A')}")
            else:
                print("  No hotels in result")
    else:
        print("  No result_json")
else:
    print("\nNo hotel match found yet")

db.close()

