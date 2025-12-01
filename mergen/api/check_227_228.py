from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Check analysis 227 (hotel match with SOW 204)
result227 = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 227).first()
if result227:
    print(f"Analysis 227: {result227.analysis_type} - {result227.status}")
    if result227.result_json:
        data = result227.result_json
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict):
            hotels = data.get('hotels', [])
            print(f"  Hotels: {len(hotels)}")
            if 'error' in data:
                print(f"  Error: {data.get('error', 'Unknown')[:200]}")
            elif hotels:
                print(f"  ✅ SUCCESS! First hotel: {hotels[0].get('name', 'N/A')}")

# Check latest hotel match
hotel = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3,
    AIAnalysisResult.analysis_type == 'hotel_match'
).order_by(AIAnalysisResult.created_at.desc()).first()

if hotel:
    print(f"\nLatest Hotel Match (ID {hotel.id}):")
    print(f"  Status: {hotel.status}")
    if hotel.result_json:
        data = hotel.result_json
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict):
            hotels = data.get('hotels', [])
            print(f"  Hotels found: {len(hotels)}")
            if 'error' in data:
                print(f"  ❌ Error: {data.get('error', 'Unknown')[:300]}")
            elif hotels:
                print(f"  ✅ SUCCESS! Hotels found:")
                for i, h in enumerate(hotels[:3], 1):
                    print(f"    {i}. {h.get('name', 'N/A')} - Score: {h.get('score', 'N/A')}")
            else:
                print("  No hotels in result")

db.close()

